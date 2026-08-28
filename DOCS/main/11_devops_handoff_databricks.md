# Handoff DevOps — Deploy Logistico 2.0 sul Databricks esistente

**Data:** 2026-07-03 · **Ultimo aggiornamento:** 2026-08-27 (post multi-repo deploy su GitLab)
**Destinatario:** DevOps Senior / Platform Engineer
**Owner tecnico dominio:** Team Logistico 2.0

> **⚡ Stato al 2026-08-27 — gran parte di questo handoff è già ESEGUITA dal team.**
> - **FASE C (Git multi-repo + CI/CD): FATTA.** 3 repo su GitLab (`logistico-infrastructure/-workflows/-lib`),
>   CI in DEV **via Managed Identity** (nessun secret di deploy). Vedi `16_runbook_multirepo_github_gitlab.md`.
> - **FASE A (Terraform UC): `plan` FATTO** — verde via MSI (15 add, 0 destroy). **`apply` bloccato** sul grant
>   `CREATE SCHEMA` alla MI → **OP-INF-1** ([[ACT_0.1.6]]).
> - **FASE B (wheel + DAB): FATTA in DEV** — wheel `v1.0.4` nel Package Registry; `deploy_dev` verde (7 job).
> - **FASE D (ingestion & primo run): da fare** al gate (credenziali SFTP + `apply`).
> Le righe sotto restano come riferimento; gli stati puntuali sono aggiornati in linea.
**Scopo:** lista completa e ordinata delle attività per portare la pipeline Logistico 2.0 sul
**Databricks/Unity Catalog aziendale già esistente**, senza rompere il DWH, con tutto il codice
(Terraform, Git, CI/CD, bundle) pronto e referenziato in questo documento.

> Documenti collegati:
> - `10_piano_migrazione_databricks.md` — razionale architetturale e decisioni D1-D5
> - `12_checklist_infra_setup.md` — **checklist operativa infra + mail al cliente + stato punti aperti**
> - `05_open_points.md` (sez. G) — registro decisioni
> - `06_backlog.md` (sez. 5j) — tracking attività databricks-readiness

---

## 1. Executive summary — cosa serve davvero

Il codice della pipeline (35+ notebook Bronze/Silver/Gold + libreria `logistica_utils`) è **già
scritto per Unity Catalog a 3 livelli** (`catalog.schema.table` via `get_catalog()`), e i nomi
catalog che produce (`bronze_dev`, `silver_dev`, `gold_dev`) **coincidono con quelli del DWH**. Quindi
NON è una riscrittura: è un lavoro di **provisioning mirato + deploy**.

Fatti che riducono lo scope rispetto all'infra greenfield preesistente in `infra/`:

1. **Catalog già esistenti** → non si creano, si **referenziano**; creiamo solo i nostri **schemi**.
2. **Ingestion in push via SFTP** (Logistix + cdt_dw) → **niente** connettività Oracle, VNet
   injection, Key Vault per credenziali sorgente. Il modulo `infra/terraform/modules/networking`
   **non serve**.
3. **Multi-repo in un subgroup GitLab dedicato** (NON mono-repo): subgroup `logistico` sotto il
   macro-gruppo data-platform, con un repository per componente.
4. **Job cluster SERVERLESS** → nessuna cluster policy con `node_type_id`/VM da gestire.

**Effort stimato DevOps:** ~4-6 giornate (setup UC + bundle + CI/CD multi-repo), escluse le attese
di attivazione utenze/permessi di piattaforma. **Auth risolta**: Managed Identity del group runner (no secret) —
il meccanismo "certificate vs secret manager" non è più un blocco.

---

## 2. Greenfield esistente vs Brownfield da fare (delta)

In `infra/terraform/` esiste un modulo **greenfield** completo (creato per un workspace nuovo). NON
va applicato così com'è sul DWH — anzi, il root module è marcato **DEPRECATO**. Ecco cosa si riusa e
cosa si sostituisce:

| Artefatto esistente | Stato | Azione brownfield |
|---|---|---|
| `infra/terraform/` root module (greenfield) | ❌ **Deprecato** | Non applicare. Header del file lo segnala. |
| `infra/terraform/modules/unity_catalog` (crea 8 catalog) | ⚠️ Greenfield | **Sostituito** da `infra/terraform/brownfield/` (referenzia catalog, crea solo schemi) |
| `infra/terraform/modules/networking` (VNet/Oracle) | ❌ Non serve | **Escluso** (ingestion in push) |
| `infra/terraform/modules/compute` (cluster policy VM) | ❌ Superato | **Sostituito** da cluster policy SERVERLESS in `brownfield/main.tf` |
| `databricks.yml` + `workflows/*.yml` (DAB, 8 job) | ✅ Riusabile | Default landing Volume + `retail_master_schema` per target dev; workflow ereditano via `${var.*}` |
| `.gitlab-ci.yml` (validate→deploy) | ✅ **Fatto** | Un `.gitlab-ci.yml` per-repo generato dallo split ([[ACT_9017]]); auth **via MSI** (no secret CI di deploy) |
| `lib/setup.py` (wheel `logistica_utils`) | ✅ Riusabile | Nessuna modifica; build wheel invariata |
| `scripts/migration/git_monorepo_import.sh` | ❌ **Obsoleto** | Non usare: la scelta è multi-repo, non mono-repo. |

**Nuovi/aggiornati artefatti per il brownfield (questa consegna):**

| File | Scopo |
|---|---|
| `infra/terraform/brownfield/main.tf` | Referenzia catalog esistenti, crea schemi logistici + Volume landing + grants + cluster policy serverless. Backend `azurerm` compilato coi valori DEV reali. |
| `infra/terraform/brownfield/variables.tf` | Variabili (catalog, schemi, decisioni D1/D2/D3, gruppi UC, reader-grant condizionale) |
| `infra/terraform/brownfield/outputs.tf` | Output: schemi creati, path Volume |
| `infra/terraform/brownfield/terraform.tfvars.example` | Template valori DEV già compilati |
| `scripts/migration/preflight_databricks.sh` | Verifica catalog/gruppi target prima del deploy |
| `lib/logistica_utils/storage.py` | Astrazione path landing/warehouse per ambiente (già integrata) |

---

## 3. Decisioni — TUTTE CHIUSE (rif. call 02-03/07/2026)

| ID | Decisione | Scelta confermata | Variabile Terraform |
|----|-----------|-------------------|---------------------|
| **D1** | Catalog di controllo watermark | ✅ `config_dev` (allineato DWH) | `catalog_control = "config_dev"` |
| **D2** | Anagrafiche cdt_dw | ✅ Schema proprio `bronze_dev.condiviso` (isolamento) | `create_condiviso_schema = true` |
| **D3** | Landing storage | ✅ UC Volume in `landing_dev` | `landing_mode = "volume"` |
| **D4** | Ambiente prod/stage | ✅ `_prod` / `_stage`; senza suffisso saranno eliminati. **Solo DEV configurato ora.** | (secondo set tfvars, non attivo) |
| **D5** | Lettura DWH legacy per quadratura | ✅ Export su landing (no JDBC diretto) | (config quadratura, DBR-04) |
| **D6** | Nomi gruppi UC | ✅ `Engineering-dev` (writer). Reader **non esiste ancora** → grant condizionale. | `group_engineers`, `enable_reader_grants` |

**Compute:** ✅ job cluster **SERVERLESS** (nessun `node_type_id`).

---

## 4. Attività — checklist ordinata per il DevOps

### FASE 0 — Prerequisiti di piattaforma (blocchi esterni)

| # | Attività | Responsabile | Stato |
|---|----------|--------------|-------|
| 0-1 | Attivazione utenze GitLab aziendale + subgroup `logistico` con permessi (creare repo + gestire pipeline) | Extrared + Ippazio | 🔴 mail inviata (§F.1 checklist) |
| 0-2 | Utenza Azure per navigazione/terraform | Francesco Giambona (PM) | 🔴 mail (§F.3 checklist) |
| 0-3 | Credenziali SFTP per push landing Logistico | Team Azure/DevOps | 🔴 mail (§F.2 checklist) |
| 0-4 | Meccanismo auth CI | Team Logistico | ✅ **Risolto**: Managed Identity del group runner (no secret) — 2026-08-27 |

### FASE A — Setup Unity Catalog (DEV)

| # | Attività | Comando / file | Owner | Effort |
|---|----------|----------------|-------|--------|
| A-1 | Preflight: verificare catalog/gruppi target esistenti | `scripts/migration/preflight_databricks.sh` | DevOps | 0.25g |
| A-2 | Copiare e verificare `terraform.tfvars` (valori DEV già compilati nell'example) | `brownfield/terraform.tfvars.example` | DevOps | 0.25g |
| A-3 | `terraform init` (backend già compilato coi valori DEV) | `cd infra/terraform/brownfield` | DevOps | 0.25g |
| A-4 | `terraform plan` → **review con Ippazio** prima dell'apply | idem | DevOps + Ippazio | 0.5g |
| A-5 | `terraform apply` → schemi + Volume landing + grants + cluster policy | idem | DevOps | 0.25g |

Comandi FASE A:
```bash
# A-1 preflight
export DATABRICKS_HOST=https://adb-3179436993731139.19.azuredatabricks.net
# In CI: auth via Managed Identity del runner (ARM_USE_MSI=true; Databricks CLI via MSI). In locale: PAT dev.
bash scripts/migration/preflight_databricks.sh --catalog-control config_dev

# A-2..A-5 terraform (backend DEV già compilato in main.tf)
cd infra/terraform/brownfield
cp terraform.tfvars.example terraform.tfvars   # valori DEV già pronti
terraform init
terraform plan      # verificare: SOLO schemi/volume/grants/policy, nessun catalog creato
# --- review con Ippazio prima di procedere ---
terraform apply
```

### FASE B — Wheel + Asset Bundle

| # | Attività | Comando / file | Owner | Effort |
|---|----------|----------------|-------|--------|
| B-1 | Build wheel `logistica_utils` | `pip install build && python -m build --wheel lib/` | DevOps | 0.25g |
| B-2 | ✅ **Fatto**: `databricks.yml` con default brownfield risolti (landing Volume, retail_master_schema) | `databricks.yml` | — | — |
| B-3 | ✅ **Fatto**: workflow collegati alle var del bundle; placeholder rimossi | `workflows/*.yml` | — | — |
| B-3b | Verificare valori risolti (D2/D3) e `siti` per area; adattare solo se necessario | `databricks.yml` variables + target dev | DevOps + Eng | 0.5g |
| B-4 | `databricks bundle validate -t dev` | idem | DevOps | 0.25g |
| B-5 | `databricks bundle deploy -t dev` | idem | DevOps | 0.25g |

### FASE C — Git multi-repo + CI/CD

| # | Attività | Comando / file | Owner | Effort |
|---|----------|----------------|-------|--------|
| C-1 | Creare i 3 repo nel subgroup `logistico` | GitLab | Team | ✅ **Fatto** ([[ACT_9011]]) |
| C-2 | Push del codice nei rispettivi repo (snapshot di release, no history) | `promote_to_gitlab.py` | Team | ✅ **Fatto** ([[ACT_9017]]) |
| C-3 | `.gitlab-ci.yml` per repo (validate→plan/deploy) | `.gitlab-ci.yml` | Team | ✅ **Fatto** (generato dallo split) |
| C-4 | Auth CI **via Managed Identity** (no secret di deploy); variabili non sensibili come **protected** ([[LL-016]]) | GitLab CI/CD | Team | ✅ **Fatto** (2026-08-27) |
| C-5 | **GitLab Runner** del subgroup — job **taggati** `azure-runner` | GitLab | Team | ✅ **Fatto** ([[LL-011]]) |

### FASE D — Ingestion & primo run

| # | Attività | Note | Owner | Effort |
|---|----------|------|-------|--------|
| D-1 | Concordare col team sorgente il **push SFTP** su Volume landing | struttura `<source>-landing/{tabella}/YYYY/MM/DD/`; SLA 04:00 | DevOps + Sorgente | — |
| D-2 | Primo run Bronze su Databricks da landing | validare conteggi vs locale | Eng | 0.5g |
| D-3 | Run Silver → Gold layer per layer | quadratura vs CDT_DW per layer | Eng | 1g |
| D-4 | Attivare scheduling/trigger sui workflow (SLA 04:00 → check 04:30) | `workflows/*.yml` | DevOps | 0.5g |

---

## 5. Dettaglio codice consegnato

### 5.1 Terraform brownfield (`infra/terraform/brownfield/`)
- **Referenzia** i catalog con `data "databricks_catalog"` → `terraform plan` **fallisce** se un
  catalog non esiste (fail-safe: evita di creare oggetti nel posto sbagliato).
- **Crea** gli schemi: `bronze.logistica`, `bronze.condiviso` (D2), `silver.logistica`,
  `silver.logistica_curated`, `gold.logistica`, `gold.logistica_dm`, `config.logistica_etl`.
- **Landing** (D3=volume): schema `landing.logistica` + `databricks_volume` MANAGED `files`.
- **Compute**: nessuna cluster policy da creare — i job girano su **serverless** (ADR-0009), che si ottiene
  **non dichiarando compute** nei job (`workflows/*.yml`, blocco `environments` per le dipendenze). La
  precedente policy `logistico-serverless-job-policy` è stata rimossa il 2026-08-04 (ACT_9007): le compute
  policy non si applicano al serverless e `runtime_engine=SERVERLESS` non è un valore valido.
- **Grants**: gruppo engineer `Engineering-dev` (full). Reader **condizionale** (`enable_reader_grants`,
  default false: il gruppo analisti non esiste ancora).
- **Backend** `azurerm` compilato coi valori DEV: `rg-dev-dataplatform-00` / `stdevdataplatformweu00`
  / container `statefile`.
- Tutto guidato da `terraform.tfvars` — **nessun token hardcoded**.

### 5.2 Storage abstraction (`lib/logistica_utils/storage.py`)
- `is_databricks()` (detect via `DATABRICKS_RUNTIME_VERSION`), `get_landing_root(env)`,
  `get_warehouse_root(env)`.
- Su Databricks default = UC Volume `/Volumes/landing_<env>/logistica/files`.
- In locale = filesystem come oggi. **Comportamento locale invariato** (già testato).

### 5.3 Preflight (`scripts/migration/preflight_databricks.sh`)
- Verifica autenticazione CLI, esistenza catalog target, presenza schemi (informativo).
- Da lanciare **prima** di `terraform apply` e del bundle deploy.

### 5.4 Artefatti greenfield riusabili
- `databricks.yml` (DAB, target dev, wheel build), `workflows/*.yml` (8 job), `.gitlab-ci.yml`,
  `lib/setup.py`. Vedi §2 per gli aggiustamenti.

---

## 6. Cosa NON fare (guardrail)

- ❌ NON applicare `infra/terraform/` root module né `modules/unity_catalog` (greenfield): usare **solo** `brownfield/`.
- ❌ NON applicare `infra/terraform/modules/networking`: nessuna connettività Oracle richiesta.
- ❌ NON usare `git_monorepo_import.sh`: la scelta è **multi-repo** in un subgroup.
- ❌ NON creare secret scope per credenziali Oracle: l'ingestion è in **push**; le credenziali Oracle
  restano solo in `.env` locale (tool dev).
- ❌ NON committare `terraform.tfvars` né token nei file (usare env/CI masked var).
- ⚠️ Le tabelle/anagrafiche del DWH esistente sono **read-only** per noi.

---

## 7. Definition of Done

- [x] Utenze GitLab attive + subgroup `logistico` creato con permessi (pipeline incluse) — 2026-08-03
- [ ] Utenza Azure attiva + credenziali SFTP Logistico ricevute
- [ ] `preflight_databricks.sh` verde su tutti i catalog target
- [~] `terraform plan` **verde via MSI** (15 add, 0 destroy) → **`apply` bloccato** sul grant UC alla MI (OP-INF-1)
- [x] wheel `logistica_utils` buildato e pubblicato (`v1.0.4`) + `deploy_dev` OK (7 job in DEV)
- [x] 3 repo popolati nel subgroup + **CI verde via Managed Identity** (no secret di deploy) — 2026-08-27
- [ ] push sorgenti su landing concordato e primo file atterrato
- [ ] primo run Bronze→Silver→Gold su Databricks con quadratura vs CDT_DW nei limiti attesi
- [ ] scheduling/trigger attivi sui workflow (SLA 04:00)
