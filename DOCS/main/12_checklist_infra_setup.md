# Checklist Infrastruttura & Setup — Logistico 2.0

**Ultimo aggiornamento:** 2026-08-27 (post multi-repo deploy su GitLab — CI in DEV via Managed Identity)  
**Partecipanti call originaria (2026-07-03):** Luigi Scrimitore, Francesco Foconi, Ippazio Alessio (Reply)  
**Scopo:** stato aggiornato di tutti i punti infrastrutturali — risposte ricevute, azioni già implementate, punti ancora aperti.

> **Aggiornamento 2026-08-27 — deploy GitLab eseguito.** I 3 repo di codice sono su GitLab con **CI in DEV via
> Managed Identity** (nessun secret): `logistico-lib` (wheel `v1.0.4` nel Package Registry), `logistico-workflows`
> (`deploy_dev` verde → 7 job in DEV), `logistico-infrastructure` (`terraform plan` verde, 15 add/0 destroy).
> **Unico blocco residuo:** l'`apply` infra attende il grant `CREATE SCHEMA` alla MI sui catalog DEV → **OP-INF-1**
> ([[ACT_0.1.6]]). Dettaglio multi-repo: `16_runbook_multirepo_github_gitlab.md`.

> Dettaglio tecnico sprint → `04_piano_sviluppo.md` | Decisioni architetturali → `10_piano_migrazione_databricks.md` | **Rilascio a fasi post-accesso → `14_release_kit.md`**

---

## Legenda

| Simbolo | Significato |
|---------|-------------|
| ✅ | Ricevuto, implementato nel codice |
| 🟡 | Parzialmente risolto / da completare al momento giusto |
| 🔴 | Ancora bloccante |
| ⏸️ | On hold — decisione esterna in corso |

---

## A. Terraform & IaC

| # | Punto | Stato | Decisione / Risposta | Implementato |
|---|-------|-------|----------------------|--------------|
| A1 | Backend TF state | ✅ | RG: `rg-dev-dataplatform-00` / SA: `stdevdataplatformweu00` / container: `statefile` | Blocco `backend "azurerm"` compilato in `brownfield/main.tf` |
| A2 | URL workspace Databricks DEV | ✅ | `https://adb-3179436993731139.19.azuredatabricks.net` | `terraform.tfvars.example` aggiornato |
| A3 | Tipo cluster compute | ✅ | **SERVERLESS** (confermato Ippazio). "Nasce quando ti serve, viene killato quando finisce." Nessun `node_type_id` necessario. | **Corretto 2026-08-04 (ACT_9007)**: serverless = **nessun compute dichiarato** nei job (`workflows/*.yml`) + `environments`/`environment_key` per il wheel. **Nessuna cluster policy**: non si applicano al serverless (`runtime_engine=SERVERLESS` non è valido) → policy rimossa dal Terraform. Vedi ADR-0009. |
| A4 | Gruppo UC engineer | ✅ | `Engineering-dev` (NON `data-science-dev` che ha meno permessi) | `group_engineers = "Engineering-dev"` in `variables.tf` e `terraform.tfvars.example` |
| A5 | Gruppo UC reader (analisti/MicroStrategy) | 🟡 | **Non esiste ancora** (Ippazio: "per gli analisti ancora non c'è"). Serve per dare accesso in lettura al Gold a MicroStrategy. | Grant reader reso **condizionale** (`enable_reader_grants = false`). Quando il gruppo sarà creato: impostare `enable_reader_grants=true` + `group_readers=<nome>` in `terraform.tfvars` → `terraform apply` |
| A6 | Naming cataloghi PROD/stage (D4) | ✅ | PROD = `_prod`, stage = `_stage`. Cataloghi senza suffisso saranno **eliminati**. Stage non da configurare per ora. | `_CATALOG_MAP["prod"]` aggiornato in `utils.py`. D4 chiuso. |
| A7 | Utenza Azure per navigazione | 🟡 | **Mail inviata a Francesco Giambona (§F.3) — in attesa risposta.** Necessaria per navigare il portale Azure e lanciare `terraform init/plan`. | Sollecito se non arriva risposta |

---

## B. GitLab & CI/CD

| # | Punto | Stato | Decisione / Risposta | Azione |
|---|-------|-------|----------------------|--------|
| B0 | Attivazione utenze GitLab | ✅ | **Accesso confermato** (2026-08-03): utenze attive, accesso al subgroup con ruolo **Maintainer**. | — |
| B1 | Struttura repo | ✅ | Path reale: **`CNO / cno-data-platform / logistico`** (subgroup). **Un progetto = un repository**. **4 repo**: 3 sul GitLab cliente — `logistico-infrastructure` (Terraform), `logistico-workflows` (notebook + DAB + SQL), `logistico-lib` (wheel `logistica_utils`) — + **`logistico-documentation`** che resta **solo sul nostro git** (non sul GitLab cliente). Vedi [[ACT_0.1.6]] / ADR-0016. | ✅ **Split eseguito** (2026-08) — 3 repo pubblicati su GitLab ([[ACT_9011]]/[[ACT_9017]]) |
| B2 | Creazione subgruppo + permessi | ✅ | **Fatto** (2026-08-03): subgroup `CNO/cno-data-platform/logistico` creato, ruolo **Maintainer** assegnato. (Mail §F.1 inviata; risposta ricevuta.) | — |
| B3 | Auth CI/CD | ✅ | **Risolto via Managed Identity** ([[ADR-0022]], 2026-08-27): la CI si autentica verso Azure/Databricks con la **MI del group runner** — **nessun secret di deploy** (no `ARM_CLIENT_SECRET`, no `DATABRICKS_TOKEN`). Terraform: `ARM_USE_MSI=true`; Databricks CLI: stessa MI. Le uniche variabili CI sono **identificativi non sensibili** impostati come **protected** (solo `main`+tag `v*`, [[LL-016]]): `ARM_CLIENT_ID`/`ARM_TENANT_ID`/`ARM_SUBSCRIPTION_ID`, `DATABRICKS_HOST`. I job runtime non usano `dbutils.secrets`/`SecretHelper`; le credenziali Oracle restano solo in `.env` locale (tool dev). | — (fatto). NB: authN ≠ authZ → serve comunque il grant UC alla MI (B6/OP-INF-1) |
| B4 | Branch strategy | ✅ | Seguire `DOCS/linee_guida/CNO_DataPlatform_linee-guida_v1.1.0` (feature branch → main, MR obbligatoria) | Da leggere prima della prima MR |
| B5 | Pipeline Terraform su GitLab | ✅ | **`terraform plan` verde via MSI** (2026-08-27): 15 add, 0 destroy, 0 risorse create (stato invariato). CI `validate`→`plan` operativa. | ✅ plan fatto → resta `apply` (B6) |
| B6 | Deploy CI in DEV (3 repo) | 🟡 | `logistico-lib` wheel `v1.0.4` pubblicato; `logistico-workflows` `deploy_dev` verde (7 job in DEV, sandbox mode:development); `logistico-infrastructure` `plan` verde. **`apply` bloccato** sul grant `CREATE SCHEMA` alla MI → **OP-INF-1** ([[ACT_0.1.6]], mail a Giambona 2026-08-27). | Ottenuto il grant → ri-run pipeline `infrastructure` + clic `apply` |

---

## C. Landing Zone & Ingestion

| # | Punto | Stato | Decisione / Risposta | Azione |
|---|-------|-------|----------------------|--------|
| C1 | Meccanismo push | ✅ | **SFTP** su `stdevdataplatformweudata.blob.core.windows.net:22`. Stesso schema di G5/PJ — un container/username per sorgente. | Richiedere credenziali Logistico-specific (template §F.2) |
| C2 | Formato file | ✅ | Logistico usa **CSV** oggi. Il codice è **già pronto anche per Parquet**: i Bronze notebook rilevano il formato automaticamente (`detect_format()`) e il widget `file_format` accetta `csv`/`parquet`/`auto`. Nessuna azione richiesta ora. Il passaggio a Parquet è un'opzione futura lato push — zero modifiche al nostro codice quando avverrà. | Nessuna — completato per la scope attuale (CSV). |
| C3 | Struttura cartelle | ✅ | **`YYYY/MM/DD`** (3 livelli separati). Confermato dalla call — il YYYYMMDD era riferito a un altro progetto. | Già corretto nel codice (`storage.py`, notebook Bronze) |
| C4 | SLA completamento push | ✅ | **04:00**. Potrà essere rivisto al go-live. Schedule Databricks Workflows da spostare: landing check → 04:30, primo processing → 05:00. | Aggiornare YAML schedule quando i Workflows saranno creati (DBR-06) |
| C5 | Alimentazione landing (SFTP vs Blob) | 🟡 | **Thread mail analizzato** (`DOCS/altro/logistico azure sftp.pdf`, 6 lug→3 ago 2026): Reply spinge per **Blob via AzCopy/API** (evita fee SFTP ~195€/mese); Conad cauta (volumi ~1 GB/sett). **Aperto, call da fissare.** Per **noi trasparente** (stesso container ADLS in entrambi i casi). Analisi + punti-call in [[ACT_9012]]. | Portare alla call: SFTP vs Blob + **chi estrae i file** (vero nodo). La nostra richiesta: container + path + accesso lettura UC + formato |
| C7 | Trasporto ≠ estrazione | 🟡 | AzCopy/API = **trasporto** (spostano file già esistenti); l'**estrazione** Oracle→file sta a monte e per D5 **non gira su Databricks** (host on-prem). Nostri script `send_to_sftp` (→ pluggable `send_to_landing`), `cdtdw_lookup_extractor` (ponte OP-02), `quadratura` (export CDT_DW). | Definire ownership estrazione dati operativi + CDT_DW (Conad / host on-prem) → [[ACT_9012]] |
| C6 | Riconciliazione `landing_mode` (managed vs external) | 🟡 | Il Terraform modella la landing come **Volume MANAGED in `landing_dev`** (`landing_mode="volume"`), ma il push SFTP arriva su un **container dedicato** (`logisticolanding`). Se il push è esterno, UC deve leggerlo via **external** location/volume (un managed volume non vede file pushati esternamente). Direzione probabile: `landing_mode="external"`. | **Dipende da C5** (risposta SFTP di Tech Reply: container + storage credential). Poi flip `landing_mode` → external + compilare path. Nessun apply in corso: non urgente. |

---

## D. Service Principal & Identità

| # | Punto | Stato | Decisione / Risposta | Azione |
|---|-------|-------|----------------------|--------|
| D1 | Service Principal | ⏸️ | On hold. Technology sta valutando **un SP unico per tutta la data platform** (non per singolo progetto). Non può essere creato da Reply — deve passare per Technology. | Attendere comunicazione da Ippazio. Probabilmente un SP condiviso → comunicarci l'ID quando pronto. |

---

## E. Sequenza di sblocco aggiornata

```
✅ A1 backend state     → terraform init pronto
✅ A2 URL workspace     → terraform plan pronto
✅ A3 cluster serverless → nessun compute nei job (policy rimossa, ADR-0009)
✅ A4 gruppo engineer   → grants writer pronti
✅ A6 naming PROD       → utils.py aggiornato, D4 chiuso
🟡 A7 utenza Azure      → solo per navigazione portale in locale; il plan/apply gira in CI via MSI (non più bloccante)
✅ B2 subgruppo GitLab  → CNO/cno-data-platform/logistico, Maintainer (2026-08-03)
✅ B3 auth CI/CD        → Managed Identity (no secret) — 2026-08-27
✅ B5 pipeline → plan   → terraform plan verde via MSI (15 add, 0 destroy)
🔴 B6 apply infra       → BLOCCA: serve grant CREATE SCHEMA alla MI sui catalog DEV → OP-INF-1
🟡 C5 SFTP Logistico    → mail inviata, risposta parziale (tema SFTP dedicato)
🟡 A5 reader group      → da fare quando il gruppo sarà creato (non bloccante per apply)
```

**Stato mail (tutte inviate):**
1. **Francesco Giambona** → utenza Azure (§F.3) — 🟡 in attesa; + **grant `CREATE SCHEMA` alla MI** (mail 2026-08-27, OP-INF-1)
2. **Extrared** (Ippazio CC) → subgruppo GitLab (§F.1) — ✅ **risolto**: subgroup + Maintainer
3. **team DevOps/Azure** → credenziali SFTP (§F.2) — 🟡 risposta parziale (da chiudere)

**Prossimo passo attivo:** ottenere il **grant `CREATE SCHEMA` alla Managed Identity** sui 5 catalog DEV
(**OP-INF-1** — mail a Giambona del 2026-08-27) → ri-run pipeline `infrastructure` + `apply`. Lo split
multi-repo e il deploy CI in DEV sono **fatti**.

---

## F. Mail da inviare

### F.1 — A Extrared (GitLab) + Ippazio Alessio in CC

**Oggetto:** Richiesta creazione subgroup GitLab — Progetto Logistico 2.0

Buongiorno,

nell'ambito del progetto **Logistico 2.0** sulla Data Platform aziendale, vi chiediamo quanto segue.

**1. Attivazione utenze sul GitLab aziendale**  
Attivare/abilitare gli account GitLab per i membri del team Logistico (lista nomi/email in calce), così da poter accedere alla piattaforma. È il prerequisito per tutto il resto.

**2. Creazione subgroup**  
Creare un **subgroup** dedicato `logistico` sotto il macro-gruppo della Data Platform, con i permessi per accedervi e per creare autonomamente i progetti (repository) al suo interno.

**Struttura richiesta** (un progetto = un repository):
```
subgroup: logistico
  ├── progetto: logistico-infrastructure   (codice Terraform)
  ├── progetto: logistico-workflows        (notebook + Databricks Asset Bundles)
  └── progetto: logistico-lib              (libreria condivisa logistica_utils)
```

**Posizione:** sotto il macro-gruppo della Data Platform.  
**Visibilità:** Internal, allineata agli altri gruppi.

**3. Permessi richiesti per il team Logistico**  
Ruolo **Maintainer o Owner** sul subgroup. In particolare, qualunque sia il modo in cui strutturate i grant, ci serve che includano esplicitamente:
- **creare progetti/repository** dentro il subgroup;
- **lanciare e controllare le pipeline CI/CD** (eseguire, ri-eseguire, annullare pipeline e job manuali);
- **gestire le variabili CI/CD** dei progetti (masked/protected) e le **protected branches**;
- gestire le **pipeline schedules**.

> Nota: preferiamo il ruolo standard **Maintainer/Owner** anziché un set di grant custom ristretti, per evitare di scoprire in corso d'opera che manca una capability sulle pipeline.

**4. Verifica tecnica**
- Sono disponibili **GitLab Runner** (shared o di gruppo) assegnati al subgroup, così le pipeline possano effettivamente eseguire?

> Le variabili CI/CD (secret di deploy) le configuriamo noi a livello di progetto — già confermato da DevOps: ci basta avere il ruolo con i permessi al punto 3.

Ippazio Alessio (in CC) ha già confermato l'inserimento sotto il macro-gruppo data-platform e ci comunicherà il path esatto dopo la creazione.

**Utenze da attivare:**
- [Nome Cognome] — [email]
- [Nome Cognome] — [email]

Grazie,  
[firma]

---

### F.2 — Al team DevOps/Azure (SFTP credenziali Logistico)

**Oggetto:** Richiesta credenziali SFTP — Progetto Logistico 2.0

Buongiorno,

per il progetto **Logistico 2.0** dobbiamo configurare il canale SFTP per il push dei file dalla sorgente verso la landing zone su Azure Blob Storage, replicando il modello già usato per G5 e PJ.

**Informazioni di cui abbiamo bisogno (sul modello G5/PJ):**
1. **Username SFTP** dedicato al flusso Logistico
2. **Container / path ADLS** di destinazione (es. `stdevdataplatformweudata.logisticolanding`)
3. **Credenziali di accesso** (chiave SSH o password, con le stesse modalità usate per G5/PJ)

**Struttura path attesa:**
```
<sorgente>-landing/<tabella>/YYYY/MM/DD/
```
sorgenti: `logistix-landing`, `cdtdw-landing`, `stat-landing`

Formato file: **CSV** (con supporto futuro Parquet).

Grazie,  
[firma]

---

### F.3 — A Francesco Giambona (PM) — utenza Azure

**Oggetto:** Richiesta utenza Azure — Progetto Logistico 2.0

Buongiorno Francesco,

per procedere con il deploy dell'infrastruttura Terraform del progetto **Logistico 2.0**, ho bisogno di un'utenza Azure con accesso (anche in sola lettura) alle risorse del gruppo `rg-dev-dataplatform-00`, in particolare allo Storage Account `stdevdataplatformweu00`.

L'accesso mi serve per:
- Verificare la configurazione del backend Terraform state (container `statefile`)
- Eseguire `terraform init` e `terraform plan` in locale durante la fase di setup
- Navigare il portale Azure per verificare le risorse create

Puoi procedere con la creazione o indicarmi a chi rivolgermi?

Grazie,  
[firma]

---

## G. Punti ancora aperti dopo la call del 2026-07-03

| Punto | Responsabile | Cosa serve | Priorità |
|-------|-------------|------------|----------|
| A7 Utenza Azure | Francesco Giambona (PM) | Account Azure per navigazione e terraform init/plan | 🟡 mail inviata, in attesa |
| B2 Subgruppo GitLab | Extrared + Ippazio | ✅ **Fatto** — `CNO/cno-data-platform/logistico`, Maintainer (2026-08-03) | ✅ |
| C5 SFTP Logistico | Team DevOps/Azure | Username + container + credenziali per sorgenti Logistix/STAT/CND | 🟡 risposta parziale |
| A5 Reader UC group | Cliente (quando creato) | Nome gruppo analisti/MicroStrategy → `enable_reader_grants=true` + `terraform apply` | 🟡 non urgente |
| B3 Auth CI/CD | Team Logistico | **Risolto**: Managed Identity del runner, nessun secret (2026-08-27) | ✅ |
| **OP-INF-1 Grant UC alla MI** | **Reply / F. Giambona** | **`USE CATALOG` + `CREATE SCHEMA` alla MI sui 5 catalog DEV** (mail 2026-08-27) → sblocca `apply` | 🔴 **bloccante** |
| D1 Service Principal | Ippazio / Technology | SP condiviso data platform → comunicare ID | ⏸️ ping mensile |
| B5 Review plan | Ippazio | `terraform plan` verde via MSI; review + `apply` dopo il grant (OP-INF-1) | 🟡 |
| H1 Tagging costi Databricks | Data Reply (Ippazio) | Standard naming tag (min. `business_unit=logistica`) + **serverless budget policy a livello di account** per applicare i tag ai job. Il tagging trasversale per applicazione Azure è governance di piattaforma (non nostro). | 🟡 (call 2026-07-03, tema costi sollevato da Silvio/Marcello) |
| H2 Retention & governance storage | Team Logistico + piattaforma | Definire e **schedulare** retention: ~90 gg su landing (UC Volume → job cleanup/lifecycle policy), 3-5 anni sul data lake; VACUUM Delta per pulizia fisica versioni. | 🟡 (governo di lungo periodo, sollevato da Silvio) |
