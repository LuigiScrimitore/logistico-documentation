# Piano di migrazione — da Docker/Spark locale ad Azure Databricks

**Data:** 2026-07-02 (agg. 2026-07-03 post-call DevOps) · **Ultimo aggiornamento:** 2026-08-27 (multi-repo su GitLab eseguito — vedi §7)
**Contesto:** il flusso Logistico gira oggi in locale (container `logistico-spark`, Delta su
filesystem, metastore Hive/Derby). Va migrato su un **Azure Databricks già esistente** (DWH
aziendale con Unity Catalog), **integrandosi senza rompere** ciò che c'è. Repo: **multi-repo** in un
subgroup GitLab dedicato `logistico` (un progetto = un repository — vedi §7).

---

## 0. TL;DR — la buona notizia

Il codice dei notebook è **già scritto per Unity Catalog a 3 livelli**. Esempio reale
(`silver_carichi_dettagli.py`):

```python
BRONZE_CATALOG = get_catalog("bronze", env)   # -> "bronze_dev"
SILVER_CATALOG = get_catalog("silver", env)   # -> "silver_dev"
SCHEMA         = "logistica"
SOURCE_TABLE   = f"{BRONZE_CATALOG}.{SCHEMA}.sto_righe_carico"   # bronze_dev.logistica.sto_righe_carico
TARGET_TABLE   = f"{SILVER_CATALOG}.{SCHEMA}.carico_dettaglio"   # silver_dev.logistica.carico_dettaglio
```

I nomi catalog prodotti da `get_catalog()` (`bronze_dev`, `silver_dev`, `gold_dev`) **coincidono
già** con i catalog dello screenshot del DWH. Localmente funziona perché il runner di test
`tests/local_bronze/run_notebook.py` ha uno **shim** che collassa `catalog.schema.table` →
`catalog_schema.table` per il metastore Hive (righe 60-98). Su Databricks lo shim **non serve**: i
notebook girano nativi.

**Conseguenza:** la migrazione NON è una riscrittura. È (a) creare gli schemi nei catalog esistenti,
(b) parametrizzare i path di landing, (c) impacchettare la lib e definire i Jobs, (d) creare i repo
nel subgroup GitLab. Effort stimato: **2-3 settimane**, rischio principale = allineamento naming e
governance UC con il team DWH.

---

## 1. Mappa dei gap (locale → Databricks)

| # | Area | Oggi (locale) | Databricks | Intervento |
|---|---|---|---|---|
| G1 | **Naming tabelle** | shim collassa a `cat_schema.table` | 3-level nativo `cat.schema.table` | Nessuno sul codice; disattivare shim (è solo nel runner locale) |
| G2 | **Schemi** | DB Hive `bronze_dev_logistica` ecc. | schema `logistica` dentro `bronze_dev` | `CREATE SCHEMA` una tantum (§3) |
| G3 | **Catalog control** | `control_dev` (in `_CATALOG_MAP`) | screenshot mostra `config_dev` | **DECISIONE D1**: rinominare o creare `control_dev` |
| G4 | **Anagrafiche cdt_dw** | catalog hardcoded `cdtdw.condiviso` | non esiste `cdtdw` nel DWH | **DECISIONE D2**: riusare `bronze_dev.prodotto/fornitore/pdv` esistenti o creare `condiviso` |
| G5 | **Landing / ingestion** | CSV in `C:\...\landing`, letti da bronze | push dai sorgenti → volume/`landing_dev` | Astrarre path (§4); landing simulator diventa tool solo-dev |
| G6 | **Lib Python** | `sys.path` al `lib/` locale | wheel o import da Repos | Build wheel o `%pip`/Repos (§5) |
| G7 | **Orchestrazione** | `run_all_bronze.py` + PowerShell | Databricks Workflows/Jobs | Definire job YAML (§6) |
| G8 | **Quadratura** | pyarrow legge parquet + hack tombstone | Spark legge Gold nativo | Su Databricks il tombstone-hack è inutile (Spark legge `_delta_log`); il legacy DWH si legge dal suo catalog o via export |
| G9 | **Credenziali Oracle** | `.env` + `oracledb` | **non serve** (push dai sorgenti) | Elimina un'intera classe di problemi (no secret scope, no VNet) |

---

## 2. Architettura target (integrazione nel DWH esistente)

```
Catalog (Unity Catalog, già esistenti)
├── landing_dev/                    # push dai sorgenti (Logistix + cdt_dw)
│   └── logistica/                  # <- nuovo schema o Volume per i file logistici
├── bronze_dev/
│   ├── customer, fornitore, pdv, prodotto, promo, dm_vendite   # ESISTENTI (DWH)
│   ├── logistica/                  # <- NOSTRO: sto_*, pesate, storico_*, tabgen, struttura_mag
│   └── condiviso/                  # <- NOSTRO (se D2=b): LU_* da cdt_dw
├── silver_dev/
│   ├── logistica/                  # <- NOSTRO: carico_dettaglio/testata, pesata, storico_*_uniche
│   └── logistica_curated/             # <- NOSTRO: carico (grain etichetta), prep_sped
├── gold_dev/
│   └── logistica/                  # <- NOSTRO: F_CARICO, F_PREP_SPED, dim_*, A_* aggregati
└── config_dev/                     # <- D1: watermark (schema logistica_etl) + parametriche
```

Principio: **schemi nostri accanto a quelli del DWH, mai dentro/sopra**. Le anagrafiche condivise
del DWH (`bronze_dev.prodotto`, `.fornitore`, `.pdv`) sono un'**opportunità di riuso** (D2).

---

## 3. Decisioni da prendere (bloccanti per il setup)

> ✅ **Tutte CHIUSE (02-03/07/2026).** Questa sezione conserva il razionale storico "prima→dopo". Per gli esiti e l'implementazione vedi la **Checklist decisioni in fondo al documento** e `12_checklist_infra_setup.md`.

- **D1 — Catalog di controllo**: il DWH ha `config_dev`, noi usiamo `control_dev`. Opzioni:
  (a) allineare `_CATALOG_MAP` a `config_dev` e mettere watermark in `config_dev.logistica_etl`;
  (b) chiedere al team DWH di creare `control_dev`. → **(a) consigliata** (non chiede nuovi catalog).
- **D2 — Anagrafiche cdt_dw**: oggi `cdtdw.condiviso.LU_*`. Il DWH ha già `bronze_dev.prodotto`,
  `.fornitore`, `.pdv`, `.promo`. Opzioni:
  (a) **riusare** le anagrafiche del DWH (meno duplicazione, ma va mappato lo schema colonne);
  (b) mantenere il nostro `bronze_dev.condiviso` popolato dal push cdt_dw (isolamento totale).
  → decisione da concordare col team DWH; **(b) per il primo rilascio** (rischio minore), valutare
  (a) in un secondo momento.
- **D3 — Landing storage**: i file pushati arrivano in un **UC Volume** (`landing_dev`) o in un
  path ADLS esterno? Determina come `run_notebook`/bronze leggono (§4).
- **D4 — Ambienti**: esiste già `_prod` speculare? `_CATALOG_MAP` prevede dev+prod. Confermare che i
  catalog `bronze`/`silver`/`gold` (senza `_dev`) siano i prod e allineare.
- **D5 — Quadratura vs DWH**: canale diretto per leggere il DWH legacy (CDT_DW) da Databricks, o
  export su landing? Confermare per portare `quadratura_fact.py` su Spark.

---

## 4. Interventi codice da fare SUBITO (a basso rischio, in locale)

Questi si possono fare ora, restano compatibili col locale e preparano il terreno.

### 4.1 Astrazione storage (`lib/logistica_utils/storage.py`)
Centralizzare il path di landing (oggi sparso tra runner e landing simulator):
```python
def get_landing_root(env: str = "dev") -> str:
    if _on_databricks():
        return "/Volumes/landing_dev/logistica/files"   # o abfss://... (dipende da D3)
    return os.environ.get("LOGISTICO_DATA", r"C:\PROGETTI\LOGISTICO_DATA") + r"\data\landing"

def _on_databricks() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ
```

### 4.2 Riconciliare `control` (D1)
In `_CATALOG_MAP` allineare la chiave `control` al catalog reale del DWH (`config_dev`/`config`),
così i notebook di watermark puntano al posto giusto senza modifiche.

### 4.3 Parametrizzare il catalog `cdtdw` (D2)
Togliere l'hardcoded `cdtdw.condiviso` (11 occorrenze) e derivarlo da una costante centralizzata
(es. `get_catalog("bronze", env) + ".condiviso"`), così la destinazione è configurabile.

### 4.4 Quadratura Spark-native
Aggiungere a `quadratura_fact.py` un backend Spark (quando gira su Databricks legge `gold_dev.
logistica.*` via `spark.table`, niente pyarrow/tombstone). Il codice pyarrow+`live_delta_files()`
resta per il locale. Selezione backend via `_on_databricks()`.

---

## 5. Setup infrastruttura Databricks

1. **Schemi** (una tantum, con i permessi UC concordati):
   ```sql
   CREATE SCHEMA IF NOT EXISTS bronze_dev.logistica;
   CREATE SCHEMA IF NOT EXISTS bronze_dev.condiviso;      -- se D2=b
   CREATE SCHEMA IF NOT EXISTS silver_dev.logistica;
   CREATE SCHEMA IF NOT EXISTS silver_dev.logistica_curated;
   CREATE SCHEMA IF NOT EXISTS gold_dev.logistica;
   CREATE SCHEMA IF NOT EXISTS config_dev.logistica_etl;  -- watermark (D1)
   ```
2. **Volume landing** (se D3=Volume): `CREATE VOLUME landing_dev.logistica.files;`
3. **Lib**: pubblicare `logistica_utils` come **wheel** (cluster library o job dependency) oppure
   importarla via **Databricks Repos** (path relativo). Wheel = più pulito per i Jobs.
4. **Cluster policy**: runtime con Delta ≥ 3.x (già lo usiamo: `delta-spark 3.2.0`); confermare le
   librerie extra (`oracledb` NON serve più su Databricks — solo nel tool locale).
5. **Permessi UC**: GRANT su schemi logistici al service principal dei job e ai team.

---

## 6. Orchestrazione (Databricks Workflows)

Rimpiazzare `run_all_bronze.py` / `run_all_gold.py` con Jobs. Un workflow per catena, con task
dipendenti che ricalcano l'ordine già codificato negli script `run_all_*`:

```
Job "logistico_daily"
  ├─ task bronze_ingest   (per tabella / per sito, da landing)
  ├─ task silver_clean    (dipende da bronze)
  ├─ task silver_prep     (dipende da silver_clean)
  ├─ task gold_facts      (dipende da silver_prep)
  └─ task quadratura      (dipende da gold; opzionale, non bloccante)
```

Trigger: schedule giornaliero o **file arrival** sul Volume landing. I widget `dbutils.widgets`
(`env`, `run_date`, `full_refresh`) diventano **job parameters** — già compatibili, nessuna modifica.

---

## 7. Git — strategia multi-repo (subgroup)

> ✅ **Eseguito (2026-08-27):** i 3 repo sono su GitLab con CI in DEV via **Managed Identity**. Runbook operativo
> completo (flusso GitHub SoT → GitLab release, promote script, lezioni): `16_runbook_multirepo_github_gitlab.md`.

**Decisione DevOps 2026-07-03: NON mono-repo.** Subgroup GitLab `logistico` sotto il macro-gruppo
data-platform, con **un progetto = un repository** per componente:
```
subgroup: logistico   (sotto macro-gruppo data-platform)
├── logistico-infrastructure   # infra/terraform/brownfield/ (Terraform)
├── logistico-workflows        # notebooks/ + resources/ (DAB + job YAML)
└── logistico-lib              # lib/logistica_utils/ (build → wheel)
```
(`scripts/` e `tests/local_bronze/` sono solo-dev; restano nel repo di sviluppo o in workflows.)

- **Creazione**: mail a Extrared per il subgroup + permessi Maintainer/Owner (creare repo + gestire
  pipeline). Path esatto confermato da Ippazio. Vedi `12_checklist_infra_setup.md`.
- **Databricks Asset Bundles**: usare **DAB** (`databricks.yml` + `resources/*.yml`) per versionare
  job e target dev. Compute = job cluster **serverless**.
- **Branching**: seguire il documento di best practice del cliente
  (`DOCS/linee_guida/CNO_DataPlatform_linee-guida_v1.1.0`).
- **Auth CI/CD**: ✅ **Managed Identity** del group runner (`ARM_USE_MSI=true`; Databricks CLI via MSI) —
  **nessun secret di deploy**. Solo identificativi non sensibili come variabili CI protected ([[LL-016]]).

---

## 8. Sequenza di migrazione consigliata

1. **Assessment/decisioni** D1-D5 con il team DWH (mezza giornata).
2. **Interventi 4.1-4.4** in locale (restano retro-compatibili), test locale verde.
3. **Setup UC** (§5): schemi, volume, permessi, wheel.
4. **Multi-repo** (§7): ✅ **fatto** — split in 3 repo GitLab + DAB + CI in DEV via MSI.
5. **Migrazione Bronze**: puntare la landing al Volume, primo run bronze su Databricks; validare
   conteggi vs locale.
6. **Silver → Gold** layer per layer; ad ogni layer, **quadratura** (ora Spark-native) vs CDT_DW.
7. **Workflows**: cablare il job daily, trigger, alert.
8. **Prod**: replicare su catalog `_prod` (D4), promozione via DAB target.

---

## 9. Cosa NON cambia (rassicurazione)

- Logica di business dei notebook (join, grain, formule ODI): invariata.
- `get_catalog()` come unico punto di astrazione dei catalog: già c'è.
- Widget/parametri: già compatibili con i job parameters.
- Delta Lake: stessa versione, stesso formato tabelle.
- Le anagrafiche/tabelle del DWH esistente: **non le tocchiamo**, al più le leggiamo (D2).

---

## Checklist decisioni

| ID | Decisione | Scelta | Stato | Implementazione |
|---|---|---|---|---|
| D1 | Catalog controllo (`control_dev` vs `config_dev`) | **`config_dev`** con schema `logistica_etl` dedicato | ✅ DECISO 2026-07-02 | `_CATALOG_MAP["dev"]["control"] = "config_dev"` — `utils.py` aggiornato (DBR-03 ✅) |
| D2 | Anagrafiche cdt_dw (riuso DWH vs `condiviso` proprio) | **Schema proprio `bronze_dev.condiviso`** (opzione B, isolamento totale). In futuro aggancio a Gold quando pronte. | ✅ DECISO 2026-07-02 | Widget default `cdtdw.condiviso` → `bronze_dev.condiviso` su 7 notebook; `get_condiviso_schema(env)` in `utils.py` (DBR-02 ✅) |
| D3 | Landing storage (Volume UC vs ADLS esterno) | **UC Volume in `landing_dev`** (al 99% confermato) | ✅ DECISO 2026-07-02 | `landing_mode = "volume"` già default Terraform; path `/Volumes/landing_dev/logistica/files` in `storage.py` |
| D4 | Ambiente prod (`bronze`/`silver`/`gold` senza `_dev` sono i prod?) | **`_prod` / `_stage`** — i catalog senza suffisso saranno eliminati. Solo DEV configurato ora. | ✅ DECISO 2026-07-03 | `_CATALOG_MAP["prod"]` = `bronze_prod`/`silver_prod`/`gold_prod`/`config_prod` in `utils.py`. PROD non deployato per ora. |
| D5 | Lettura DWH legacy per quadratura | **Export su landing** per ora. In futuro valutare connessione diretta Oracle. | ✅ DECISO 2026-07-02 | `quadratura_fact.py`: pyarrow locale resta; su Databricks leggerà export CSV da Volume landing via `spark.read`. DBR-04 aggiornato di conseguenza. |
| — | Compute | **Job cluster SERVERLESS** | ✅ DECISO 2026-07-03 | Implementazione **corretta 2026-08-04** (ACT_9007): serverless = **nessun compute dichiarato** nei `workflows/*.yml` + `environments`/`environment_key` per il wheel. Cluster policy rimossa (non applicabile al serverless). Vedi ADR-0009. |
| — | Git | **Multi-repo** in subgroup `logistico` (NON mono-repo) | ✅ DECISO 2026-07-03 | 3 repo: `logistico-infrastructure`/`-workflows`/`-lib`. Vedi `11_devops_handoff_databricks.md` e `12_checklist_infra_setup.md` |
