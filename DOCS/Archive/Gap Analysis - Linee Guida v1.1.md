# Gap Analysis — Linee Guida v1.1 vs Sviluppo Logistico 2.0

**Data:** 2026-05-30  
**Autore:** Cloud Data Architect  
**Documento sorgente:** `DOCS/01. Preparazione/Linee Guida - Punti di approfondimento v1.1.docx`  
**Versione sviluppo analizzato:** Logistico 2.0 — stato al 2026-05-30

---

## Executive Summary

Su 10 punti di chiarimento, **7 sono coerenti** con quanto sviluppato, **3 richiedono modifiche** al codice o all'infrastruttura.

| # | Punto | Stato | Destinatario |
|---|-------|-------|--------------|
| 1 | Condivisione Anagrafiche | ✅ Coerente | — |
| 2 | Landing Zone (CSV/Parquet) | ⚠️ **DA CORREGGERE** | Data Engineer |
| 3 | Access Connector / Storage Credential | ⚠️ **DA CORREGGERE** | DevOps |
| 4 | Organizzazione Repository GitLab | ⚠️ **DA CORREGGERE** | DevOps |
| 5 | Gestione Secret / Key Vault | ⚠️ **DA CORREGGERE** | DevOps |
| 6 | Naming Convention e Schemi Gold | ✅ Coerente | — |
| 7 | Struttura Repository (1 per area) | ⚠️ **DA ALLINEARE** | DevOps |
| 8a | Libreria Python condivisa (wheel) | ⚠️ **DA VALUTARE** | Data Engineer |
| 8b | SparkSQL consentito | ✅ Coerente | — |
| 9 | Orchestrazione DAB (no Airflow) | ✅ Coerente | — |
| 10 | Sviluppo in Dev (GitFlow) | ✅ Coerente | — |

---

## Analisi Dettagliata

### ✅ 1 — Condivisione Anagrafiche (COERENTE)
**Risposta Retail:** Le anagrafiche condivise sono in `gold` negli schemi relativi (calendario, prodotto, ecc.). Permessi di lettura confermati.  
**Nostra implementazione:** le anagrafiche master Retail sono **condivise in lettura** (naming `LU_*`); il loro schema/percorso definitivo è **da confermare (OP-01/OP-02)**. NON esiste uno schema "condiviso" di nostra proprietà in bronze/silver. Le 4 dim master sono deprecate (`exit DEPRECATED_OP02`); la join master è opzionale via parametro `retail_master_schema`. Workaround temporaneo attivo: `LU_*` da CDT_DW in `cdtdw.condiviso` (placeholder, OP-01).  
**Azione:** confermare con Reply schema/nomi definitivi (OP-02); "condiviso" è un nome-placeholder nostro, non terminologia Retail.

---

### ⚠️ 2 — Landing Zone: Supporto PARQUET (DA CORREGGERE — Data Engineer)

**Risposta Retail:** *"I file saranno CSV o parquet"*

**Gap identificato:** Il nostro `template_bronze.py` e tutti i 26 notebook Bronze leggono **esclusivamente CSV**:
```python
spark.read.format("csv")
    .option("header", "true")
    .option("sep", ";")
    ...
```
Se i sistemi sorgente inviano file Parquet, tutti i Bronze falliscono.

**Correzioni richieste (Data Engineer):**

#### 2a — Template Bronze: aggiungere widget `file_format` e logica auto-detect

Aggiungere in `notebooks/templates/template_bronze.py`:
```python
dbutils.widgets.text("file_format", "csv", "Formato file landing (csv | parquet | auto)")
FILE_FORMAT = dbutils.widgets.get("file_format").strip().lower()  # csv, parquet, auto
```

Sostituire la funzione `read_landing_csv()` con `read_landing_files()`:
```python
def read_landing_files(spark, paths: List[str], file_format: str) -> DataFrame:
    """
    Legge file CSV o Parquet dalla landing zone.
    Se file_format='auto', rileva il formato dal primo file trovato.
    """
    if file_format == "auto":
        # Rileva formato dal primo file disponibile
        for path in paths:
            try:
                files = dbutils.fs.ls(path)
                for f in files:
                    if f.name.endswith(".parquet"):
                        file_format = "parquet"
                        break
                    elif f.name.endswith(".csv"):
                        file_format = "csv"
                        break
                if file_format != "auto":
                    break
            except Exception:
                continue
        if file_format == "auto":
            file_format = "csv"  # fallback
        print(f"[AUTO-DETECT] Formato rilevato: {file_format}")

    if file_format == "parquet":
        df = (
            spark.read.format("parquet")
            .load(paths)
            .withColumn("_source_file", input_file_name())
        )
    else:  # csv
        df = (
            spark.read.format("csv")
            .option("header", "true")
            .option("inferSchema", "false")
            .option("encoding", "UTF-8")
            .option("sep", ";")
            .option("nullValue", "")
            .option("emptyValue", "")
            .option("dateFormat", "yyyy-MM-dd")
            .option("timestampFormat", "yyyy-MM-dd HH:mm:ss")
            .option("mode", "PERMISSIVE")
            .load(paths)
            .withColumn("_source_file", input_file_name())
        )
    return df
```

#### 2b — Check presenza file: estendere per .parquet

Nel blocco di check `dbutils.fs.ls()`, aggiornare:
```python
# PRIMA (solo CSV):
csv_files = [f for f in files if f.name.endswith(".csv")]

# DOPO (CSV e Parquet):
data_files = [f for f in files if f.name.endswith(".csv") or f.name.endswith(".parquet")]
```

#### 2c — Notebook Bronze specifici

Applicare la stessa modifica (`file_format` widget + lettura duale) a tutti i 26 notebook Bronze in:
- `notebooks/bronze/carichi/` (4 file)
- `notebooks/bronze/prep_spedizioni/` (3 file)
- `notebooks/bronze/giacenze/` (2 file)
- `notebooks/bronze/trasporti/` (2 file)
- `notebooks/bronze/anagrafiche/` (9 file)
- `notebooks/bronze/carrellisti/` (2 file)
- `notebooks/bronze/stat/` (2 file)
- `notebooks/bronze/tracciabilita/` (1 file)

#### 2d — Workflow YAML: aggiungere parametro `file_format`

In `workflows/logistica_landing_ingestion.yml`, aggiungere ai parametri job-level:
```yaml
parameters:
  - name: file_format
    default: "auto"  # auto-detect dal primo file trovato
```
E propagarlo a ogni task Bronze come `base_parameters`.

---

### ⚠️ 3 — Access Connector / Storage Credential (DA CORREGGERE — DevOps)

**Risposta Retail:** *"È possibile utilizzare l'Access Connector in maniera condivisa, tuttavia per lo Storage Credential sarebbe meglio crearne uno diverso"*

**Gap identificato:** Il Terraform attuale in `infra/terraform/modules/unity_catalog/main.tf` usa (o eredita) la Storage Credential del team Retail. Dobbiamo creare una Storage Credential separata per il dominio Logistica.

**Correzioni richieste (DevOps):**

#### 3a — Aggiungere Storage Credential dedicata in Terraform

In `infra/terraform/modules/unity_catalog/main.tf`, aggiungere:
```hcl
# Storage Credential dedicata al dominio Logistica
# (Access Connector condiviso con Retail, credential separata per segregazione)
resource "databricks_storage_credential" "logistica_sc" {
  name = "logistica-storage-credential-${var.environment}"
  azure_managed_identity {
    access_connector_id = var.access_connector_id  # condiviso con Retail
  }
  comment = "Storage Credential dedicata al dominio Logistica. Gestisce accesso ADLS logistica-landing e logistica-delta."
}

resource "databricks_grants" "logistica_sc_grants" {
  storage_credential = databricks_storage_credential.logistica_sc.id
  grant {
    principal  = "data-engineers-logistica"
    privileges = ["ALL_PRIVILEGES"]
  }
}
```

#### 3b — Aggiornare External Location per usare la nuova credential

Aggiornare `databricks_external_location.logistica_landing`:
```hcl
resource "databricks_external_location" "logistica_landing" {
  name            = "logistica-landing-${var.environment}"
  url             = "abfss://landing@${var.storage_account_name}.dfs.core.windows.net/logistica"
  credential_name = databricks_storage_credential.logistica_sc.name  # <-- credential separata
  comment         = "Landing zone ADLS Gen2 per push CSV/Parquet da sistemi Logistix, CND, STAT"
}
```

#### 3c — Aggiungere variabile `access_connector_id` in `variables.tf`

```hcl
variable "access_connector_id" {
  description = "ID dell'Azure Databricks Access Connector condiviso con il team Retail"
  type        = string
}
```

---

### ⚠️ 4 — Organizzazione Repository GitLab (DA CORREGGERE — DevOps)

**Risposta Retail:** *"L'ideale sarebbe andare a creare un repository dentro il sottogruppo dei repository ETL della data platform."*

**Gap identificato:** Il nostro repository è attualmente strutturato come repo standalone. Deve essere posizionato come sottogruppo del gruppo `data-platform` su GitLab.

**Struttura target:**
```
data-platform/
  etl/
    logistica/            ← NOSTRO REPO (unico per ora, poi valutare split per area)
      notebooks/
      workflows/
      infra/
      lib/
      sql/
      .gitlab-ci.yml
      databricks.yml
```

**Correzioni richieste (DevOps):**

#### 4a — Aggiornare `.gitlab-ci.yml` per compatibilità sottogruppo

Verificare e aggiornare in `.gitlab-ci.yml`:
- I path di `include:` che potrebbero puntare a template del gruppo parent
- Le variabili di ambiente GitLab che referenziano il repo (es. `$CI_PROJECT_PATH`)
- La registrazione del runner se è specifico per gruppo

#### 4b — Aggiornare `databricks.yml` (DAB) con il nuovo percorso

In `databricks.yml`, verificare che `bundle.name` e i `workspace.root_path` riflettano la nuova struttura:
```yaml
bundle:
  name: logistica_etl  # coerente con naming data-platform

targets:
  dev:
    workspace:
      root_path: /Workspace/data-platform/etl/logistica/${bundle.target}
  prod:
    workspace:
      root_path: /Workspace/data-platform/etl/logistica/${bundle.target}
```

---

### ⚠️ 5 — Gestione Secret / Key Vault (DA CORREGGERE — DevOps)

**Risposta Retail:** *"Corretto: possiamo creare e gestire le credenziali tramite pipeline CI/CD e segreti su GitLab."*

**Gap identificato:** Il nostro `secret_helper.py` in `lib/logistica_utils/` legge esclusivamente da Azure Key Vault tramite Databricks Secret Scope. La risposta indica che le credenziali vanno gestite anche tramite **GitLab CI/CD secrets** e propagate al deployment.

**Correzioni richieste:**

#### 5a — Pipeline GitLab: aggiungere stage di propagazione secrets (DevOps)

In `.gitlab-ci.yml`, aggiungere uno stage `secrets-sync` che:
1. Legge i segreti da GitLab CI/CD Variables (marcate come `protected` + `masked`)
2. Li scrive nel Databricks Secret Scope tramite Databricks CLI

```yaml
secrets-sync:
  stage: validate
  script:
    - databricks secrets put-secret logistica/scope landing_sas_token --string-value "$LANDING_SAS_TOKEN"
    - databricks secrets put-secret logistica/scope logistix_sftp_key --string-value "$LOGISTIX_SFTP_KEY"
  only:
    - main
    - develop
```

#### 5b — `secret_helper.py`: mantenere come wrapper (Data Engineer, priorità bassa)

Il `secret_helper.py` è corretto nella sua logica (legge dal Secret Scope Databricks). Non va modificato: i segreti GitLab vengono scritti nel Secret Scope dalla pipeline CI/CD (5a), poi letti dai notebook tramite `secret_helper.py`. La catena è:

```
GitLab CI Variable → [pipeline secrets-sync] → Databricks Secret Scope → secret_helper.py → notebook
```

---

### ✅ 6 — Naming Convention e Schemi Gold (COERENTE)

**Risposta Retail:** Schemi separati per dominio nel catalogo gold. Nessun prefisso aggiuntivo previsto. Non sono previsti cataloghi dedicati per dominio.  
**Nostra implementazione:** `gold_<env>.logistica.*`, `gold_<env>.logistica_dm.*` (con `gold_dev`/`gold_prod` **separati e speculari**). Le anagrafiche master Retail sono condivise in lettura (`LU_*`, schema TBD OP-01/02), non uno schema "condiviso" di nostra proprietà.  

**⚠️ Azione preventiva (da concordare con Retail):** Verificare che gli schemi `logistica`, `logistica_dm` non collidano con schemi già esistenti/pianificati nei cataloghi gold. Confermare schema/percorso del master Retail condiviso (OP-02).

---

### ⚠️ 7 — Struttura Repository (1 per area — DA ALLINEARE)

**Risposta Retail:** *"Concordo con la proposta: un repository per area, ma verifico."* La questione sulla definizione di "flusso" è ancora aperta.

**Impatto:** La struttura attuale (unico repo `logistica`) è accettabile nella fase attuale. Quando la definizione di "flusso" sarà chiarita, potrebbe essere necessario suddividere il repo per area funzionale. Non blocca lo sviluppo attuale.

**Azione (DevOps — bassa priorità, post go-live):** Tenere la struttura attuale come repo unico. Predisporre la cartella `notebooks/` già organizzata per area (come attualmente è) per facilitare un eventuale split futuro.

---

### ⚠️ 8a — Libreria Python: Wheel condivisa vs logistica_utils (DA VALUTARE — Data Engineer)

**Risposta Retail:** *"Se per voi utilizzare la nostra wheel è utile, potete utilizzarla direttamente."*

**Gap identificato:** Abbiamo sviluppato `lib/logistica_utils/` con: `secret_helper`, `logging_helper`, `delta_helper`, `dq_helper`, `utils`. Il team Reply ha una loro wheel con logica analoga.

**Valutazione architetturale:**

| Opzione | Pro | Contro |
|---------|-----|--------|
| **Usare wheel Reply** | Meno codice da mantenere, allineamento piattaforma | Dipendenza esterna, possibili API diverse, meno controllo |
| **Mantenere logistica_utils** | Autonomia, già sviluppata e testata, API note | Duplicazione di codice con Reply |
| **Ibrido: logistica_utils wrappa wheel Reply** | Migliore dei due mondi | Complessità aggiuntiva |

**Raccomandazione:** Richiedere al team Reply la documentazione della loro wheel (API, versioning, compatibilità Spark). Prima di eventuale migrazione, mantenere `logistica_utils` attuale che è già funzionante e testata (64 test). **Non modificare ora** — da pianificare come attività Sprint dedicato.

**Azione (Data Engineer — post go-live):** Ottenere documentazione wheel Reply, valutare compatibilità API, pianificare eventuale migrazione.

---

### ✅ 8b — SparkSQL consentito (COERENTE)
Le 10 view KPI in `sql/kpi/` e l'uso di `spark.sql()` nei notebook sono conformi. Nessuna modifica.

---

### ✅ 9 — Orchestrazione DAB, no Airflow (COERENTE)
I nostri 8 workflow YAML in `workflows/` usano Databricks Asset Bundles. Dipendenze tra job gestite tramite scheduling a cascata (00:30 → 06:00). Coerente con la risposta.

**Nota:** Le dipendenze verticali tra domini (es. Gold Prep Spedizioni dipende da Master Data Retail) non sono ancora esplicitate. Vanno definite con il team Retail quando sarà disponibile il calendario di aggiornamento dei dati condivisi.

---

### ✅ 10 — Sviluppo in Dev (GitFlow — COERENTE)
Infrastruttura condivisa in dev, branch-based per job ad hoc, merge alla fine dello sviluppo. Coerente con quanto previsto nel nostro `.gitlab-ci.yml`.

---

## Priorità delle Correzioni

| Priorità | ID | Titolo | Destinatario | Effort stimato |
|----------|-----|--------|--------------|----------------|
| 🔴 Alta | 2 | Supporto file Parquet in Bronze | Data Engineer | 3-4 gg |
| 🔴 Alta | 3 | Storage Credential separata Terraform | DevOps | 0.5 gg |
| 🟡 Media | 4 | Struttura repo GitLab (sottogruppo) | DevOps | 1 gg |
| 🟡 Media | 5 | GitLab secrets → Databricks Secret Scope | DevOps | 1 gg |
| 🟢 Bassa | 6 | Verifica collisione schemi con Retail | Architettura | 0.5 gg (meeting) |
| 🟢 Bassa | 7 | Split repo per area (post go-live) | DevOps | 2 gg (futuro) |
| 🟢 Bassa | 8a | Valutazione wheel Reply vs logistica_utils | Data Engineer | 0.5 gg (analisi) |

---

## File coinvolti per le correzioni

### Data Engineer (priorità ALTA — punto 2)
```
notebooks/templates/template_bronze.py                    ← modifica principale
notebooks/bronze/carichi/bronze_carichi_testate.py
notebooks/bronze/carichi/bronze_carichi_dettagli.py
notebooks/bronze/carichi/bronze_pesate.py
notebooks/bronze/carichi/bronze_traccia_ce178.py
notebooks/bronze/prep_spedizioni/bronze_prep_riepiloghi.py
notebooks/bronze/prep_spedizioni/bronze_prep_bolle_testate.py
notebooks/bronze/prep_spedizioni/bronze_prep_bolle_righe.py
notebooks/bronze/giacenze/bronze_giacenze_snapshot.py
notebooks/bronze/giacenze/bronze_movimenti_magazzino.py
notebooks/bronze/trasporti/bronze_trasporti.py
notebooks/bronze/trasporti/bronze_vettori.py
notebooks/bronze/anagrafiche/*.py                         (9 file)
notebooks/bronze/carrellisti/*.py                         (2 file)
notebooks/bronze/stat/*.py                                (2 file)
workflows/logistica_landing_ingestion.yml                 ← aggiungere file_format param
```

### DevOps (priorità ALTA — punti 3, 4, 5)
```
infra/terraform/modules/unity_catalog/main.tf             ← Storage Credential separata
infra/terraform/variables.tf                              ← nuova variabile access_connector_id
.gitlab-ci.yml                                            ← stage secrets-sync + sottogruppo
databricks.yml                                            ← workspace root_path aggiornato
```
