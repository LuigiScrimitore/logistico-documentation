# Sprint 0.1 — Unity Catalog & Storage Foundation

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_0.md`](../milestones/fase_0.md)

---

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 0 — Fondamenta Infrastrutturali |
| **Obiettivo** | Provisioning Unity Catalog (schemi logistici nei catalog DWH), landing UC Volume, compute serverless, grants least-privilege — tutto via Terraform brownfield |
| **Gg stimati** | 7 |
| **Gg completati** | 0 (codice pronto; esecuzione bloccata su prerequisiti piattaforma) |
| **% avanzamento** | ~85% codice / 0% esecuzione |
| **Stato** | 🔵 IN CORSO |
| **Data inizio** | _da definire_ |
| **Data fine prevista** | _da definire_ (dipende da utenza Azure + subgroup GitLab) |
| **Ultimo aggiornamento** | 2026-07-03 |

### Note di sprint
- **Decisioni D1-D5 chiuse** (02-03/07/2026): controllo `config_dev` (D1), anagrafiche `bronze_dev.condiviso` (D2), landing UC Volume (D3), prod `_prod`/stage `_stage` non configurati ora (D4), quadratura via export su landing (D5).
- **Compute serverless** confermato (call Reply 2026-07-03): niente `node_type_id`/VM.
- **0.1.4 ridisegnata** (Key Vault → GitLab CI/CD) e **0.1.6 ridisegnata** (multi-repo, non mono-repo).
- Il codice Terraform (`infra/terraform/brownfield/`) è completo; manca solo l'esecuzione, bloccata su prerequisiti esterni.

### Blocchi attivi (🔴)
| Blocco | Owner | Riferimento |
|--------|-------|-------------|
| Utenza Azure (per `terraform init/plan`) | Francesco Giambona (PM) | [`../12_checklist_infra_setup.md`](../12_checklist_infra_setup.md) §F.3 |
| Subgroup GitLab `logistico` + permessi | Extrared + Ippazio (Reply) | §F.1 |
| Credenziali SFTP landing Logistico | Tech Reply | §F.2 |
| Meccanismo secret auth (cert vs secret manager) | Technology | ⏸️ ping mensile |

---

## Attività

| # | Attività | Gg | Stato | Sintesi |
|---|----------|----|-------|---------|
| 0.1.1 | Cataloghi Unity Catalog (solo DEV) | 1 | 🔵 IN CORSO | Referenzia catalog DWH esistenti, crea solo schemi |
| 0.1.2 | Schemi per dominio | 1 | 🔵 IN CORSO | 7 schemi logistici + condiviso + config |
| 0.1.3 | Landing storage — UC Volume | 1 | 🔵 IN CORSO | D3: Volume in `landing_dev` |
| 0.1.4 | ~~Key Vault + Secret Scope~~ → GitLab CI/CD | 0 | ✅ CHIUSA | Ridisegnata: no segreti Oracle |
| 0.1.5 | Cluster Policy — serverless | 1 | ✅ CHIUSA | Job cluster serverless |
| 0.1.6 | ~~TF state & moduli~~ → consegna `brownfield/` multi-repo | 1 | 🟡 QUASI PRONTA | Backend DEV compilato; MR pendente |
| 0.1.7 | Grants least-privilege | 2 | 🟡 IN ATTESA | Writer `Engineering-dev` ✅; reader condizionale |

---

## Dettaglio attività

### 0.1.1 — Cataloghi Unity Catalog (solo DEV) 🔵
**Cosa:** l'overlay brownfield referenzia (non crea) i catalog DWH esistenti `bronze_dev`, `silver_dev`, `gold_dev`, `config_dev` (D1), `landing_dev` via `data "databricks_catalog"`; `terraform plan` fallisce se un catalog manca (fail-safe).
**File:** `infra/terraform/brownfield/main.tf`.
**Stato:** codice pronto. PROD (`_prod`) / stage (`_stage`) non configurati ora (D4).
**Blocco:** esecuzione `terraform apply` dipende da utenza Azure (0.1 blocco).

### 0.1.2 — Schemi per dominio 🔵
**Cosa:** crea gli schemi logistici: `bronze.logistica`, `bronze.condiviso` (D2), `silver.logistica`, `silver.logistica_curated`, `gold.logistica`, `gold.logistica_dm`, `config.logistica_etl` (D1).
**Nota rename 2026-07-03:** ex `silver.prep_logistica` → `silver.logistica_curated`.
**Dipende da:** 0.1.1.

### 0.1.3 — Landing storage — UC Volume 🔵
**Cosa:** D3 confermato — UC Volume MANAGED in `landing_dev` (`landing_mode="volume"`, path `/Volumes/landing_dev/logistica/files`). External Location ADLS non necessaria.
**⚠️ Punto aperto (C6 checklist):** il push SFTP arriva su un container dedicato (`logisticolanding`); se il push è esterno, UC dovrà leggerlo via **external** location/volume, non managed. Da riconciliare alla risposta SFTP di Tech Reply (`landing_mode` → external).

### 0.1.4 — ~~Key Vault + Secret Scope~~ → GitLab CI/CD ✅ CHIUSA
**Ridisegnata 2026-07-02.** Nessun segreto Oracle su Azure (D5 = export su landing, no JDBC). SP e token Databricks come variabili masked in GitLab. UC Volume usa managed identity del workspace — nessun `dbutils.secrets.get(...)` nei notebook. Nessuna colonna da cifrare (dati operativi, no PII). **AKV non necessario.**

### 0.1.5 — Compute serverless ✅ CHIUSA (implementazione corretta 2026-08-04)
**Confermato Reply 2026-07-03:** job **serverless** ("nasce col job, killato al termine"). Nessun `node_type_id`/`num_workers`.
**Correzione 2026-08-04 (ACT_9007):** la policy `logistico-serverless-job-policy` (`runtime_engine=SERVERLESS`) è stata **rimossa** — valore non valido e **le compute policy non si applicano al serverless**. Il serverless si ottiene **non dichiarando compute** nei job; dipendenze via `environments`/`environment_key`. Vedi ADR-0009.

### 0.1.6 — Consegna `brownfield/` multi-repo 🟡 QUASI PRONTA
**Ridisegnata.** Root module greenfield `infra/terraform/` **deprecato**. Solo `brownfield/` va applicato. Backend `azurerm` compilato coi valori DEV reali (`rg-dev-dataplatform-00` / `stdevdataplatformweu00` / `statefile`). Git: **multi-repo** in subgroup `logistico` (`logistico-infrastructure`/`-workflows`/`-lib`), non mono-repo. `git_monorepo_import.sh` obsoleto.
**Azione:** creare subgroup (mail Extrared) → creare repo → `terraform init/plan` → review con Ippazio → apply.

### 0.1.7 — Grants least-privilege 🟡 IN ATTESA
**Cosa:** grant in `brownfield/main.tf`: `engineer_group` (full su schemi logistici), reader (SELECT su Gold).
**Stato:** writer `Engineering-dev` confermato (gruppo engineering trasversale della piattaforma — vede retail+logistica, scelta intenzionale). Reader (analisti/MicroStrategy) **non ancora creato** → grant reso condizionale (`enable_reader_grants=false`).
**Azione:** quando il gruppo reader esisterà, `enable_reader_grants=true` + `group_readers=<nome>` → apply + test accesso negato.

---

## Riferimenti
- Portfolio: [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md)
- Chiusura fase: [`../milestones/fase_0.md`](../milestones/fase_0.md)
- Checklist infra + mail cliente: [`../12_checklist_infra_setup.md`](../12_checklist_infra_setup.md)
- Handoff DevOps: [`../11_devops_handoff_databricks.md`](../11_devops_handoff_databricks.md)
- Decisioni migrazione: [`../10_piano_migrazione_databricks.md`](../10_piano_migrazione_databricks.md)
