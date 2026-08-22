# Logistico 2.0 — Migrazione DWH Oracle → Databricks Medallion Architecture

[![Databricks](https://img.shields.io/badge/Databricks-14.3%20LTS-FF3621?logo=databricks)](https://databricks.com)
[![Azure](https://img.shields.io/badge/Azure-ADLS%20Gen2-0078D4?logo=microsoft-azure)](https://azure.microsoft.com)
[![Terraform](https://img.shields.io/badge/Terraform-Unity%20Catalog-7B42BC?logo=terraform)](https://terraform.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python)](https://python.org)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-MERGE%20INTO-00ADD8)](https://delta.io)

> Migrazione completa dell'architettura Oracle DWH (CDT\_ESTR → CDT\_SA → CDT\_DW, orchestrata con ODI) verso **Databricks Medallion Architecture** (Bronze → Silver → Gold → DataMart) su **Azure**.

---

## Indice

- [Panoramica](#panoramica)
- [Architettura](#architettura)
- [Struttura del Repository](#struttura-del-repository)
- [Layer Bronze](#layer-bronze)
- [Layer Silver](#layer-silver)
- [Layer Gold e DataMart](#layer-gold-e-datamart)
- [Workflow di Orchestrazione](#workflow-di-orchestrazione)
- [SQL KPI Views](#sql-kpi-views)
- [Infrastruttura Terraform](#infrastruttura-terraform)
- [CI/CD GitLab](#cicd-gitlab)
- [Libreria logistica\_utils](#libreria-logistica_utils)
- [Testing](#testing)
- [Prerequisiti e Setup](#prerequisiti-e-setup)
- [Sviluppo e GitFlow](#sviluppo-e-gitflow)
- [Documentazione](#documentazione)
- [Stato del Progetto](#stato-del-progetto)

---

## Panoramica

Il progetto **Logistico 2.0** migra l'intero stack di Data Warehousing del dominio logistico da Oracle/ODI a Databricks su Azure, seguendo l'architettura **Medallion** (Bronze → Silver → Gold) e le linee guida della Data Platform Reply.

### Sistemi Sorgente

| Sistema | Tipo | Siti | Tabelle principali |
|---------|------|------|-------------------|
| **Logistix** | WMS | 9 siti: `lgax` `lgcx` `lcax` `lccx` `lexx` `locx` `lonx` `lscx` `lslx` | STO\_TES\_CARICHI, PESATE, DETTAGLIO\_CARR, CARTELLINO, STRUTTURA\_MAG, ... |
| **CND / CDT\_SOURCE** | Gestione ordini e stock | Centralizzato | T\_STOCK, T\_PDV, T\_VETTORI, T\_TRASP\_MTV, T\_PREP\_SPED |
| **STAT** | Sistema statistico | Centralizzato | BUONI\_ECO, TIPO\_ATTIVITA\_ECO |

### Pattern di Ingestion — No JDBC Oracle

I sistemi sorgente inviano il delta giornaliero **in push** sulla Landing Zone ADLS Gen2 via SFTP. I file sono in formato **CSV o Parquet**. Nessuna connessione JDBC ad Oracle.

```
Logistix / CND / STAT
        |  push SFTP (delta giornaliero — CSV o Parquet)
        v
Landing Zone ADLS Gen2
  landing/logistix/{sito}/{tabella}/YYYY/MM/DD/
  landing/cnd/{tabella}/YYYY/MM/DD/
  landing/stat/{tabella}/YYYY/MM/DD/
        |  00:30  Bronze Ingestion (MERGE INTO Delta)
        v
Bronze Delta Tables (26)
        |  01:00-05:30  Silver + Gold pipelines
        v
Silver Delta Tables (24)  -->  Gold Core (star schema)  -->  Gold DataMart
                                                                    |
                                                                    v
                                                            10 KPI SQL Views --> BI
```

---

## Architettura

### Unity Catalog — Struttura Cataloghi

```
bronze_dev / bronze_prod
  └── logistica.*          26 tabelle Delta (landing zone MERGE INTO)

silver_dev / silver_prod
  └── logistica.*          24 tabelle Delta (cleansed, typed, renamed)

gold_prod
  ├── condiviso.*          4 dim condivise (calendario, articolo, fornitore, struttura_merc)
  ├── logistica.*          5 dim dominio + 7 fact tables (star schema)
  └── logistica_dm.*       6 aggregazioni DataMart mensili/giornaliere
```

### Star Schema Gold

Le **chiavi sono naturali (string)** — nessun surrogate ID numerico.

```
dim_calendario          dim_articolo
      |                      |
dim_fornitore --- f_carico --+-- dim_sito --- f_giacenze_daily --- dim_topografia
                      |
dim_operatore --- f_prep_sped (regola 30 min attrezzaggio) --- dim_pdv
                      |
dim_corriere --- f_trasporto
```

---

## Struttura del Repository

```
Logistico2.0/
|
+-- notebooks/
|   +-- templates/           Template Bronze/Silver/Gold riutilizzabili
|   +-- bronze/              26 notebook (ingestion landing zone -> MERGE INTO)
|   |   +-- carichi/         STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE, TRACCIACE178
|   |   +-- prep_spedizioni/ STORICO_RIEPILOGHI, TESTATE_BOLLE, STORICO_BOLLE, T_PREP_SPED
|   |   +-- giacenze/        T_STOCK, IMBFMOVIM
|   |   +-- trasporti/       T_TRASP_MTV, T_VETTORI
|   |   +-- carrellisti/     DETTAGLIO_CARR, CARTELLINO
|   |   +-- anagrafiche/     10 tabelle anagrafiche (operatori, struttura mag, aree, ecc.)
|   |   +-- stat/            BUONI_ECO, TIPO_ATTIVITA_ECO
|   |
|   +-- silver/              24 notebook (cleansing + cast + rename + MERGE)
|   |   +-- carichi/         carico_testata, carico_dettaglio, pesata, traccia_ce178
|   |   +-- giacenze/        giacenza_daily, giacenza_aggregata
|   |   +-- prep_spedizioni/ prep_riepilogo, bolla_testata/dettaglio, timbrature, integrata
|   |   +-- trasporti/       ordine, trasporto, swap, costo_trasporto
|   |   +-- tracciabilita/   tracciabilita_lotto, missione/sessione_carrellista
|   |   +-- dimensioni/      7 dim Silver (sito, operatore, corriere, pdv, topo, articolo, forn)
|   |
|   +-- gold/                23 notebook (star schema + DataMart)
|       +-- dimensioni/      9 dimensioni SCD Type 1
|       +-- carichi/         f_carico + late_arriving_handler
|       +-- giacenze/        f_giacenze_daily
|       +-- prep_spedizioni/ f_prep_sped (regola 30 min attrezzaggio)
|       +-- trasporti/       f_ordini, f_trasporto
|       +-- tracciabilita/   f_tracciabilita_lotti
|       +-- carrellisti/     f_movimentazione_carrellisti
|       +-- aggregati/       6 DataMart: dm_inbound/stock/outbound/produttivita + dm_giacenze_monthly + dm_turno_prep_sito
|
+-- sql/
|   +-- kpi/                 10 view SQL KPI per BI (gold_prod.logistica.kpi_*)
|   +-- optimize/            OPTIMIZE + ZORDER per tutte le tabelle Delta
|
+-- lib/
|   +-- logistica_utils/     Libreria Python custom
|       +-- secret_helper.py    Databricks Secret Scope
|       +-- logging_helper.py   Logger strutturato
|       +-- delta_helper.py     Delta Lake utilities
|       +-- dq_helper.py        Data Quality checks
|       +-- utils.py            get_catalog e utilities generali
|
+-- workflows/               8 workflow Databricks Asset Bundle YAML
|   +-- logistica_landing_ingestion.yml   00:30 Bronze CND+STAT
|   +-- logistica_dim_refresh.yml         01:00 Dimensioni Silver+Gold
|   +-- logistica_carichi.yml             02:00 Pipeline carichi
|   +-- logistica_giacenze.yml            03:30 Pipeline giacenze
|   +-- logistica_prep_sped.yml           04:30 Prep spedizioni + carrellisti
|   +-- logistica_trasporti.yml           05:00 Trasporti + tracciabilita
|   +-- logistica_wave_e.yml              05:30 CE178 wave
|   +-- logistica_aggregati.yml           06:00 DataMart aggregazioni
|
+-- infra/terraform/         Infrastructure as Code
|   +-- main.tf              Provider azurerm + databricks
|   +-- variables.tf
|   +-- outputs.tf
|   +-- modules/
|       +-- unity_catalog/   Cataloghi, schemi, storage credential, external location
|       +-- compute/         Cluster policies, instance pools
|       +-- networking/      VNet injection, private endpoints
|
+-- tests/                   64 test pytest
+-- DOCS/                    Tutta la documentazione di progetto
+-- databricks.yml           DAB config (dev/prod targets)
+-- .gitlab-ci.yml           Pipeline CI/CD 5 stage
+-- requirements-dev.txt
+-- pytest.ini
```

---

## Layer Bronze

Bronze legge file **CSV o Parquet** dalla Landing Zone e fa **MERGE INTO** su Delta.

### Widget del template Bronze

| Widget | Default | Descrizione |
|--------|---------|-------------|
| `catalog_bronze` | `bronze_dev` | Catalogo target |
| `source_system` | `logistix` | `logistix` / `cnd` / `stat` |
| `landing_base_path` | — | Base URL ADLS Gen2 |
| `load_date` | oggi | Data di riferimento YYYY-MM-DD |
| `merge_keys` | — | Chiavi naturali comma-separated |
| `logistix_sites` | `*` | Siti o wildcard (solo Logistix) |
| `file_format` | `auto` | `csv` / `parquet` / `auto` (auto-detect) |

### Metadati aggiunti da Bronze

```python
_bronze_load_date   # data dal path landing (non da Oracle)
_bronze_insert_ts   # current_timestamp() — preservato negli UPDATE MERGE
_source_file        # input_file_name()
_sito_cod           # estratto dal path con regexp_extract (solo Logistix)
```

### Tabelle Bronze (26)

| Area | Tabella Bronze | Fonte Oracle |
|------|---------------|-------------|
| Carichi | `sto_tes_carichi` | STO\_TES\_CARICHI |
| Carichi | `sto_righe_carico` | STO\_RIGHE\_CARICO |
| Carichi | `pesate` | PESATE |
| Carichi | `tracciace178` | TRACCIACE178 |
| Prep Sped | `storico_riepiloghi` | STORICO\_RIEPILOGHI (solo lgax) |
| Prep Sped | `testate_bolle` | TESTATE\_BOLLE (solo lgax) |
| Prep Sped | `storico_bolle` | STORICO\_BOLLE (solo lgax) |
| Prep Sped | `t_prep_sped` | T\_PREP\_SPED (CND) |
| Carrellisti | `dettaglio_carr` | DETTAGLIO\_CARR |
| Carrellisti | `cartellino` | CARTELLINO |
| Giacenze | `t_stock` | T\_STOCK (CND) |
| Giacenze | `imbfmovim` | IMBFMOVIM |
| Trasporti | `t_trasp_mtv` | T\_TRASP\_MTV (CND) |
| Trasporti | `t_vettori` | T\_VETTORI (CND) |
| Anagrafiche | `carrellisti` | CARRELLISTI |
| Anagrafiche | `preparatori` | PREPARATORI |
| Anagrafiche | `ricevitori` | RICEVITORI |
| Anagrafiche | `spedizionieri` | SPEDIZIONIERI |
| Anagrafiche | `struttura_mag` | STRUTTURA\_MAG |
| Anagrafiche | `corsie` | CORSIE |
| Anagrafiche | `tabgen` | TABGEN |
| Anagrafiche | `aree_merceologiche` | AREE\_MERCEOLOGICHE |
| Anagrafiche | `classe_posto_pallet` | CLASSE\_POSTO\_PALLET |
| Anagrafiche | `t_pdv` | T\_PDV (CND) |
| STAT | `buoni_eco` | BUONI\_ECO |
| STAT | `tipo_attivita_eco` | TIPO\_ATTIVITA\_ECO |

---

## Layer Silver

Silver applica: cast espliciti da StringType, rinomina colonne da prefissi Oracle a nomi business, deduplica con Window su `_bronze_insert_ts DESC`, MERGE INTO Delta.

### Mapping prefissi Oracle → Silver

| Prefisso | Tabella | Esempio |
|----------|---------|---------|
| `STCAR_*` | STO\_TES\_CARICHI | `STCAR_NRO_CARICO` → `CARICO_NRO` |
| `SRCAR_*` | STO\_RIGHE\_CARICO | `SRCAR_QTA_RICEVUTA` → `QTA_RICEVUTA` |
| `PSP_*` | PESATE | `PSP_PESONETTO` → `PESO_NETTO` |
| `CE178_*` | TRACCIACE178 | `CE178_NRO_ETICHETTA` → `ETICHET_NRO` |
| `RPLPR_*` | STORICO\_RIEPILOGHI | `RPLPR_ORE_EFFETTIVE` → `ORE_EFFETTIVE` |
| `TEBO_*` | TESTATE\_BOLLE | `TEBO_NRO_BOLLA` → `BOLLA_NRO` |
| `BOL_*` | STORICO\_BOLLE | `BOL_NRO_RIGA` → `RIGA_NRO` |
| `DTCRL_*` | DETTAGLIO\_CARR | `DTCRL_DURATA` → `DURATA_SEC` |
| `CARTE_*` | CARTELLINO | `CARTE_ORA_ENTRATA` → `ORA_ENTRATA` |
| `CRLLS_*` | CARRELLISTI | `CRLLS_COGNOME` → `COGNOME` |
| `STRM_*` | STRUTTURA\_MAG | `STRM_TIPO_CELLA` → `TIPO_CELLA` |
| `STK*` | T\_STOCK | `STKQGIAC` → `QTA_GIACENZA` |
| `VET_*` | T\_VETTORI | `VET_RAGIONE_SOC` → `RAGIONE_SOCIALE` |
| `PUV*` | T\_PDV | `PUVCODICE` → `PDV_COD` |
| `SP_*` | T\_TRASP\_MTV | `SP_CODVET` → `CORRIERE_COD` |

---

## Layer Gold e DataMart

**Principio**: chiavi naturali string, nessun surrogate ID numerico. Tutti i lookup dimensionali sono per validazione, non per sostituire chiavi.

### Dimensioni Gold Core — `gold_prod.logistica.*`

| Tabella | Chiave | Fonte Silver |
|---------|--------|-------------|
| `dim_sito` | SITO\_COD | struttura\_mag |
| `dim_operatore` | OPERATORE\_COD + SITO\_COD + TIPO\_OPERATORE | UNION 4 tabelle anagrafiche operatori |
| `dim_corriere` | CORRIERE\_COD | dim\_corriere (da t\_vettori) |
| `dim_pdv` | PDV\_COD | dim\_pdv (da t\_pdv) |
| `dim_topografia` | CELLA\_COD | struttura\_mag (key = concat sito+mag+corsia+col+piano) |

### Dimensioni Condivise — `gold_prod.condiviso.*`

| Tabella | Chiave | Fonte |
|---------|--------|-------|
| `dim_calendario` | GIORNO\_ID (YYYYMMDD) | Generata in PySpark puro (2018-2030, festività IT incluse) |
| `dim_articolo` | ART\_COD | aree\_merceologiche + sto\_righe\_carico |
| `dim_fornitore` | FORNITORE\_COD | sto\_tes\_carichi |
| `dim_struttura_merceologica` | CODICE\_MERCE | aree\_merceologiche |

### Fact Tables — `gold_prod.logistica.*`

| Tabella | Grain | Pattern | Partizione |
|---------|-------|---------|------------|
| `f_carico` | 1 riga dettaglio carico | replaceWhere | ANNO\_MESE |
| `f_giacenze_daily` | (DATA\_FOTO, ART\_COD, MAG\_COD) | replaceWhere | DATA\_FOTO |
| `f_prep_sped` | riepilogo per operatore/giorno | replaceWhere | DATA\_PREPARAZ |
| `f_ordini` | (ordine, articolo) | replaceWhere | DATA\_CARICO |
| `f_trasporto` | bolla spedizione per vettore | replaceWhere | DATA\_BOLLA |
| `f_tracciabilita_lotti` | (lotto/carico, articolo) | replaceWhere | ANNO\_MESE |
| `f_movimentazione_carrellisti` | (carrellista, data, sito) | replaceWhere | DATA\_PRESENZA |

#### Regola 30 Minuti Attrezzaggio

La **prima sessione del giorno** per ogni operatore/sito sconta 30 min da `ORE_PRODUTTIVE`:

```python
w = Window.partitionBy("OPERATORE_COD","DATA_PREPARAZ","SITO_COD").orderBy("ORA_INIZIO")
df = df.withColumn("sessione_rank", F.row_number().over(w))
df = df.withColumn("ORE_PRODUTTIVE",
    F.when(F.col("sessione_rank") == 1,
        F.greatest(F.lit(0.0), (F.col("DURATA_MIN") - 30) / 60.0)
    ).otherwise(F.col("DURATA_MIN") / 60.0)
)
```

### DataMart — `gold_prod.logistica_dm.*`

Aggregazioni pre-calcolate per BI (solo GROUP BY su Gold Core — nessuna logica aggiuntiva):

| Tabella | Sorgente | Grain |
|---------|----------|-------|
| `dm_inbound_mensile` | f\_carico | FORNITORE\_COD + SITO\_COD + ANNO\_MESE |
| `dm_stock_mensile` | dm\_giacenze\_monthly | ART\_COD + MAG\_COD + ANNO\_MESE |
| `dm_outbound_mensile` | f\_ordini + f\_trasporto | SITO\_COD + CORRIERE\_COD + ANNO\_MESE |
| `dm_produttivita_mensile` | f\_prep\_sped | SITO\_COD + ANNO\_MESE |
| `dm_giacenze_monthly` | f\_giacenze\_daily | ART\_COD + MAG\_COD + ANNO\_MESE |
| `dm_turno_prep_sito` | f\_prep\_sped | SITO\_COD + DATA\_PREPARAZ + TURNO |

---

## Workflow di Orchestrazione

8 workflow **Databricks Asset Bundles** con scheduling a cascata (Europe/Rome):

| Orario | Workflow | Contenuto |
|--------|----------|-----------|
| 00:30 | `logistica_landing_ingestion` | Bronze CND + STAT (7 task paralleli + gate) |
| 01:00 | `logistica_dim_refresh` | Silver + Gold tutte le 9 dimensioni |
| 02:00 | `logistica_carichi` | Silver carichi → Gold f\_carico → late\_arriving → DQ |
| 03:30 | `logistica_giacenze` | Silver giacenze → Gold f\_giacenze\_daily |
| 04:30 | `logistica_prep_sped` | Silver riepiloghi/bolle/timbrature → Gold f\_prep\_sped + f\_movimentazione\_carrellisti |
| 05:00 | `logistica_trasporti` | Silver trasporti/ordini → Gold f\_trasporto + f\_ordini + f\_tracciabilita\_lotti |
| 05:30 | `logistica_wave_e` | Silver/Gold CE178 wave |
| 06:00 | `logistica_aggregati` | DataMart: 6 aggregazioni in parallelo |

> I Bronze Logistix (multi-sito) sono gestiti all'interno dei rispettivi workflow di dominio. `logistica_landing_ingestion` è dedicato a CND + STAT.

---

## SQL KPI Views

10 view `gold_prod.logistica.kpi_*` per consumo diretto da strumenti BI (Power BI, Tableau, ecc.):

| View | KPI | Sorgente |
|------|-----|---------|
| `kpi_lead_time_fornitore` | Lead time e tasso scarto mensile per fornitore | `dm_inbound_mensile` |
| `kpi_qualita_ricevimento` | Qualità ricevimento: scarto quantità e colli | `f_carico` |
| `kpi_saturazione_magazzino` | % saturazione celle per magazzino | `f_giacenze_daily` + `dim_topografia` |
| `kpi_aging_articoli` | Giorni in giacenza dalla prima ricezione | `f_giacenze_daily` |
| `kpi_produttivita_operatore` | Colli/ora con ranking per sito e mese | `f_prep_sped` + `dim_operatore` |
| `kpi_efficienza_sito_prep` | Produttività e % ore attrezzaggio per sito | `dm_produttivita_mensile` |
| `kpi_fill_rate` | Fill rate spedizioni per sito e corriere | `dm_outbound_mensile` |
| `kpi_costo_trasporto` | Costo trasporto stimato per corriere | `f_trasporto` + `dim_corriere` |
| `kpi_resa_corrieri` | % consegne puntuali con ranking corrieri | `f_trasporto` |
| `kpi_bolle_annullate` | Bolle annullate per sito e mese | `f_ordini` |

---

## Infrastruttura Terraform

```bash
cd infra/terraform
terraform init
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

### Moduli e risorse principali

| Modulo | Risorse |
|--------|---------|
| `unity_catalog` | Cataloghi bronze/silver/gold\_prod, schemi logistica/condiviso/logistica\_dm, **Storage Credential dedicata Logistica** (Access Connector condiviso con Retail, credential separata per segregazione), External Location landing zone |
| `compute` | Cluster policies per ogni dominio, instance pools |
| `networking` | VNet injection, private endpoints ADLS Gen2 |

### Variabili principali

| Variabile | Descrizione |
|-----------|-------------|
| `environment` | `dev` o `prod` |
| `storage_account_name` | Nome storage account ADLS Gen2 |
| `access_connector_id` | Azure Resource ID dell'Access Connector Databricks (condiviso con Retail) |

---

## CI/CD GitLab

Pipeline `.gitlab-ci.yml` su 5 stage:

| Stage | Attività | Branch |
|-------|---------|--------|
| `validate` | Linting Python (Ruff), validazione YAML DAB | tutti |
| `secrets-sync` | GitLab CI Variables → Databricks Secret Scope `logistica` | main, develop |
| `test` | 64 test pytest | tutti |
| `deploy-dev` | `databricks bundle deploy --target dev` | develop |
| `deploy-prod` | `databricks bundle deploy --target prod` | main (tag vX.Y.Z) |

### Gestione Secrets

```
GitLab CI Variable (protected + masked)
  |  [stage secrets-sync]
  v
Databricks Secret Scope "logistica"
  |  [notebook runtime]
  v
dbutils.secrets.get("logistica", "landing_sas_token")
```

---

## Libreria logistica\_utils

```python
from lib.logistica_utils.logging_helper import get_logger
from lib.logistica_utils.dq_helper      import check_not_null, check_row_count
from lib.logistica_utils.delta_helper   import optimize_table
from lib.logistica_utils.secret_helper  import SecretHelper
from lib.logistica_utils.utils          import get_catalog

# Installazione sviluppo locale
# cd lib && pip install -e .
```

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --tb=short
```

| File test | N. test | Area |
|-----------|---------|------|
| `test_dim_calendario.py` | 18 | Generazione calendario, festività italiane, settimana ISO |
| `test_regola_30min.py` | 15 | Regola 30 min attrezzaggio (prima sessione del giorno) |
| `test_dq_carichi.py` | 16 | Check DQ su f\_carico (null check, range, referential integrity) |
| `test_logistica_utils.py` | 15 | Unit test secret\_helper, logging, utils |
| **Totale** | **64** | |

---

## Prerequisiti e Setup

### Software richiesto

- Python 3.11+
- Databricks CLI 0.200+
- Terraform 1.5+
- Node.js 18+ (solo per generazione documenti)

### Setup ambiente di sviluppo

```bash
# 1. Clona il repository
git clone https://github.com/LuigiScrimitore/Logistico2.0.git
cd Logistico2.0

# 2. Installa dipendenze Python
pip install -r requirements-dev.txt
cd lib && pip install -e . && cd ..

# 3. Configura Databricks CLI
databricks configure --token
# Host: https://adb-xxx.azuredatabricks.net
# Token: dapi...

# 4. Valida DAB
databricks bundle validate

# 5. Esegui test
pytest tests/ -v
```

### Deploy in dev

```bash
databricks bundle deploy --target dev
databricks bundle run logistica_carichi --target dev
```

---

## Sviluppo e GitFlow

```
main          release stabili (tag vX.Y.Z) -> deploy automatico in prod
  |
  +-- develop    integrazione continua -> deploy automatico in dev
        |
        +-- feature/nome-feature
        +-- bugfix/nome-bug
        +-- hotfix/nome-hotfix
```

### Principi architetturali

- **Idempotenza**: ogni notebook può essere rieseguito su `run_date` già processato senza corrompere dati
- **No JDBC Oracle**: tutti i dati arrivano dalla landing zone ADLS Gen2 (push dai sistemi sorgente)
- **StringType in Bronze**: nessun cast in Bronze, tutti i cast avvengono in Silver
- **Chiavi naturali**: Gold usa chiavi string, nessun surrogate ID numerico
- **MERGE INTO**: Bronze e Silver usano MERGE (no append, no truncate/reload)
- **replaceWhere**: Gold usa replaceWhere per partizione (idempotenza + performance)
- **max\_concurrent\_runs: 1**: garantisce idempotenza a livello di workflow

---

## Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [`DOCS/Documento di Sviluppo Finale.md`](DOCS/Documento%20di%20Sviluppo%20Finale.md) | Handoff document completo — architettura v2.0, go-live checklist |
| [`DOCS/Gap Analysis - Linee Guida v1.1.md`](DOCS/Gap%20Analysis%20-%20Linee%20Guida%20v1.1.md) | Conformità vs linee guida Data Platform Reply |
| [`DOCS/decision_matrix_ingestion.md`](DOCS/decision_matrix_ingestion.md) | Decision matrix ingestion v2.0 (no JDBC, landing zone) |
| [`DOCS/Piano di Sviluppo - Logistico 2.0.xlsx`](DOCS/Piano%20di%20Sviluppo%20-%20Logistico%202.0.xlsx) | 171 attività, 34 sprint, stato avanzamento |
| [`DOCS/Tabelle Sorgenti - Logistico 2.0.xlsx`](DOCS/Tabelle%20Sorgenti%20-%20Logistico%202.0.xlsx) | 46 tabelle sorgente con colonne e prefissi Oracle |
| [`DOCS/Tabelle Target CDT\_DW - Logistico 2.0.xlsx`](DOCS/Tabelle%20Target%20CDT_DW%20-%20Logistico%202.0.xlsx) | 22 tabelle Gold con 248 colonne documentate |
| [`DOCS/runbook.md`](DOCS/runbook.md) | Procedure operative (riavvio job, replay date, troubleshooting) |
| [`DOCS/cutover_plan.md`](DOCS/cutover_plan.md) | Piano migrazione da ODI a Databricks |
| [`DOCS/rollback_plan.md`](DOCS/rollback_plan.md) | Procedura di rollback al sistema Oracle |
| [`DOCS/01. Preparazione/Linee Guida - Punti di approfondimento v2.0.docx`](DOCS/01.%20Preparazione/) | 18 domande aperte per il team Retail Data Platform |

---

## Stato del Progetto

| Componente | N. | Stato |
|------------|-----|-------|
| Bronze notebooks | 26 | ✅ Completato |
| Silver notebooks | 24 | ✅ Completato |
| Gold Core (dim + fact + late arriving) | 16 | ✅ Completato |
| Gold DataMart | 6 | ✅ Completato |
| SQL KPI Views | 10 | ✅ Completato |
| Workflow YAML (DAB) | 8 | ✅ Completato |
| Terraform (3 moduli) | 3 moduli | ✅ Completato |
| CI/CD GitLab (5 stage) | 1 pipeline | ✅ Completato |
| Test suite | 64 test | ✅ Completato |
| Documentazione | Piano, tabelle sorgenti/target, runbook, cutover, rollback | ✅ Completato |
| Provisioning Azure (ADLS, Access Connector, VNet) | — | 🔵 Pre-deploy |
| Configurazione SFTP sistemi sorgente | — | 🔵 Pre-deploy |
| Go-live (deploy prod + attivazione workflow) | — | 🔵 Pianificato |

---

## Contatti

**Team Logistico 2.0** — luigi.scrimitore@aperion.it

---

*Sviluppato seguendo le linee guida della Data Platform Reply (v1.1) e l'architettura Medallion Databricks.*
