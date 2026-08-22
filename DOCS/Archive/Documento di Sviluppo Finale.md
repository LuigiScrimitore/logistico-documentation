# Logistico 2.0 — Documento di Sviluppo Finale

**Progetto:** Migrazione Oracle DWH → Databricks Medallion Architecture (Azure)  
**Data documento:** 2026-05-30  
**Versione:** 2.0  
**Stato:** Completato — In attesa di deploy

---

## Indice

1. [Executive Summary](#1-executive-summary)
2. [Architettura Target](#2-architettura-target)
3. [Struttura del Repository](#3-struttura-del-repository)
4. [Inventario Completo dei Deliverable](#4-inventario-completo-dei-deliverable)
5. [Stato Attività per Sprint](#5-stato-attività-per-sprint)
6. [Pattern e Convenzioni Tecniche](#6-pattern-e-convenzioni-tecniche)
7. [Regole di Business Critiche Implementate](#7-regole-di-business-critiche-implementate)
8. [Attività in Sospeso (ACCESSI)](#8-attività-in-sospeso-accessi)
9. [Piano di Onboarding del Team](#9-piano-di-onboarding-del-team)
10. [Checklist di Go-Live](#10-checklist-di-go-live)

---

## 1. Executive Summary

Il progetto **Logistico 2.0** prevede la completa riscrittura del Data Warehouse logistico attualmente basato su Oracle (schemi `CDT_ESTR`, `CDT_SA`, `CDT_DW`, orchestrato via ODI) in una **Medallion Architecture** su **Azure Databricks** con **Unity Catalog**.

### Risultati della Fase di Sviluppo (COMPLETATA)

| Categoria | Conteggio |
|---|---|
| Notebook Bronze completati | 26 |
| Notebook Silver completati | 24 |
| Notebook Gold completati | 23 |
| Workflow YAML completati | 8 |
| SQL KPI views completate | 10 |
| Tabelle sorgente documentate | 46 |
| Tabelle target documentate (CDT_DW) | 22 (248 colonne) |
| Giorni uomo stimati totali | 205,5 |
| Giorni uomo completati | ~90 |

### Team coinvolto

| Ruolo | Responsabilità |
|---|---|
| Cloud Solution Architect | Architettura Unity Catalog, pattern Medallion, documenti di analisi, piano cut-over |
| Cloud DevOps Engineer Senior | Terraform, GitLab CI/CD, Databricks Asset Bundles, workflow YAML |
| Cloud Solution Developer Senior | Libreria `logistica_utils`, tutti i notebook Bronze/Silver/Gold, test suite |
| BI Developer Senior | SQL KPI views, ottimizzazione query, mapping funzionali |

---

## 2. Architettura Target

```
Oracle AS-IS                          Databricks TO-BE
─────────────────────────────────    ─────────────────────────────────────────────
CDT_ESTR  (estrazione via DB_LINK)  → BRONZE  (landing zone ADLS, MERGE INTO Delta)
CDT_SA    (staging/normalizzazione) → SILVER  (cleansed, MERGE INTO)
CDT_DW    (Star Schema facts/dims)  → GOLD    (dimensional model + DataMart)
ODI       (orchestrazione)          → Databricks Workflows (8 job) + DAB
```

### Decisione Architetturale: Gold Core + DataMart

**Scelta:** 2 schemi nel catalogo Gold (`gold_dev` / `gold_prod`) per dominio, invece di cataloghi dedicati per dominio:

```
gold_<env>
  └── logistica          (Gold Core: DIM_*, F_*, tabelle late-arriving)
  └── logistica_dm       (DataMart: dm_* view/tabelle aggregate per BI)
```

Schemi per dominio (non cataloghi dedicati): allineato alla risposta Retail ("schemi separati per dominio nel catalogo gold, nessun catalogo dedicato per dominio") e semplifica i grant per i team BI.

### Unity Catalog — Struttura Cataloghi

Cataloghi nominati **per livello e ambiente**. **dev e prod sono separati e speculari** su tutti i livelli (nessun collassamento su un unico ambiente — incluso il Gold):

```
bronze_dev  / bronze_prod
  └── logistica            (tutte le tabelle raw)

silver_dev  / silver_prod
  └── logistica            (tabelle cleansed 1:1)
  └── prep_logistica       (elaborazioni intermedie / preprocessing)

gold_dev    / gold_prod
  └── logistica            (fact F_*, dimension DIM_*, tabelle late-arriving)
  └── logistica_dm         (DataMart: dm_inbound_mensile, dm_stock_mensile, ecc.)

control_dev / control_prod (layer di controllo trasversale ai layer, per ambiente)
  └── etl                  (watermark, log run, esiti DQ — scritto dalle pipeline)
  └── parametri            (tabelle parametriche/manuali di integrazione — mantenute a mano)
```

> **Anagrafiche master Retail (condivise):** NON risiedono in uno schema "condiviso" di nostra proprietà nei layer bronze/silver. Sono **condivise in lettura** dal flusso Master Data Retail con naming `LU_*` in schemi per-dominio del catalogo Gold Retail; **nome/percorso definitivo da confermare (OP-01/OP-02)**. Workaround attuale temporaneo: le `LU_*` ricavate da CDT_DW vivono nello schema isolato `cdtdw.condiviso` (placeholder, vedi OP-01).

### Flusso Dati (Pattern Aggiornato — Landing Zone Push)

```
Sistemi Sorgente (Logistix / CND)
    │ (push CSV su ADLS Gen2 landing zone — NO JDBC Oracle)
    ▼
[Landing Zone ADLS] CSV arrivano in push dai sistemi sorgente
    │ (read CSV → MERGE INTO Delta, schema validation)
    ▼
[Bronze] append-only / MERGE INTO, schema evolution OFF, add_ingestion_metadata()
    │ (ROW_NUMBER dedup, cast_decimal, business rules, colonne prefissi Oracle)
    ▼
[Silver] MERGE INTO su chiave naturale (SCD Type 1 per dims, upsert per facts)
    │ (colonne rinominate da prefissi Oracle a nomi business)
    │ (es. STCAR_* → cod_carico, SRCAR_* → cod_riga, PSP_* → cod_preparazione)
    ▼
[Gold Core] replaceWhere (fatti giornalieri) / MERGE INTO (fatti cumulativi)
    │ (chiavi naturali — nessun surrogate ID)
    ▼
[Gold DataMart] dm_* tabelle aggregate, schema gold_prod.logistica_dm
    │
    ▼
[SQL KPI Views] 10 view gold_prod.logistica.kpi_* con chiavi naturali
    │
    ▼
[MicroStrategy / BI Tools]
```

---

## 3. Struttura del Repository

```
C:\PROGETTI\LOGISTICO\
│
├── .gitignore                          # Esclusioni standard + secrets
├── .gitlab-ci.yml                      # Pipeline CI/CD 4 stage
├── databricks.yml                      # Databricks Asset Bundles (dev/prod) — aggiornato v2.0
├── pytest.ini                          # Configurazione test
├── requirements-dev.txt                # Dipendenze sviluppo locale
├── README.md                           # Guida rapida progetto
│
├── infra/terraform/
│   ├── main.tf                         # Backend azurerm, 3 sub-moduli
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── unity_catalog/              # Cataloghi, schemi, external location landing zone
│       ├── compute/                    # Cluster policies, SQL Warehouse
│       └── networking/                 # NSG rules
│
├── lib/logistica_utils/
│   ├── __init__.py
│   ├── secret_helper.py                # Azure Key Vault + fallback os.environ
│   ├── logging_helper.py               # Logger JSON strutturato
│   ├── delta_helper.py                 # merge_into, replace_where, watermark
│   ├── dq_helper.py                    # Data quality checks + report
│   ├── utils.py                        # surrogate_key_fallback, cast_decimal
│   └── setup.py
│
├── notebooks/
│   ├── templates/                      # 3 template base (Bronze/Silver/Gold)
│   ├── bronze/                         # 26 notebook — landing zone push ADLS → Delta
│   │   ├── transazionali_logistix/     # 7 notebook (STO_TES_CARICHI, STO_RIGHE_CARICO,
│   │   │                               #   PESATE, TRACCIACE178, STORICO_RIEPILOGHI,
│   │   │                               #   TESTATE_BOLLE, STORICO_BOLLE)
│   │   ├── anagrafiche_logistix/       # 12 notebook (DETTAGLIO_CARR, IMBFMOVIM,
│   │   │                               #   CARTELLINO, CARRELLISTI, PREPARATORI,
│   │   │                               #   RICEVITORI, SPEDIZIONIERI, STRUTTURA_MAG,
│   │   │                               #   CORSIE, TABGEN, AREE_MERCEOLOGICHE,
│   │   │                               #   CLASSE_POSTO_PALLET)
│   │   └── cnd_stat/                   # 7 notebook (T_STOCK, T_PDV, T_VETTORI,
│   │                                   #   T_TRASP_MTV, T_PREP_SPED, BUONI_ECO,
│   │                                   #   TIPO_ATTIVITA_ECO)
│   ├── silver/                         # 24 notebook trasformazione Bronze→Silver
│   │   ├── dimensioni/                 # 7 notebook (dim_sito, dim_operatore,
│   │   │                               #   dim_corriere, dim_pdv, dim_topografia,
│   │   │                               #   dim_articolo, dim_fornitore)
│   │   ├── carichi/                    # 6 notebook (carico_testata, carico_dettaglio,
│   │   │                               #   pesata, traccia_ce178, giacenza_daily,
│   │   │                               #   giacenza_aggregata)
│   │   └── prep_sped_trasp_tracc/      # 11 notebook (prep spedizioni, trasporti,
│   │                                   #   tracciabilità)
│   └── gold/                           # 23 notebook Gold layer
│       ├── dimensioni/                 # 9 notebook (dim_calendario, dim_sito,
│       │                               #   dim_operatore, dim_corriere, dim_pdv,
│       │                               #   dim_topografia, dim_articolo, dim_fornitore,
│       │                               #   dim_struttura_merceologica)
│       ├── facts/                      # 7 fact tables + 1 late_arriving_handler
│       │                               #   (f_carico, f_giacenze_daily, f_prep_sped,
│       │                               #   f_ordini, f_trasporto, f_tracciabilita_lotti,
│       │                               #   f_movimentazione_carrellisti)
│       └── datamart/                   # 6 DataMart schema gold_prod.logistica_dm
│                                       #   (dm_inbound_mensile, dm_stock_mensile,
│                                       #   dm_outbound_mensile, dm_produttivita_mensile,
│                                       #   dm_giacenze_monthly, dm_turno_prep_sito)
│
├── sql/
│   ├── kpi/                            # 10 SQL views KPI (gold_prod.logistica.kpi_*)
│   └── optimize/                       # OPTIMIZE + ZORDER + ANALYZE (Gold)
│
├── workflows/                          # 8 Databricks Workflow YAML
│
├── tests/                              # 64 unit test (pytest + pyspark locale)
│   ├── conftest.py
│   ├── test_logistica_utils.py         # 25 test
│   ├── test_dim_calendario.py          # 15 test
│   ├── test_regola_30min.py            # 9 test
│   └── test_dq_carichi.py             # 15 test
│
└── DOCS/
    ├── Piano di Sviluppo - Logistico 2.0.xlsx
    ├── Tabelle Sorgenti - Logistico 2.0.xlsx       # 46 tabelle sorgente, colonne
    ├── Tabelle Target CDT_DW - Logistico 2.0.xlsx  # 22 tabelle target, 248 colonne
    ├── Documento di Sviluppo Finale.md             ← questo file
    ├── decision_matrix_ingestion.md                # v2.0
    ├── cutover_plan.md
    ├── rollback_plan.md
    ├── runbook.md
    └── analisi/
        ├── mapping_carichi.md
        ├── mapping_giacenze.md
        ├── mapping_prep_spedizioni.md
        ├── mapping_trasporti.md
        ├── mapping_ce178.md
        └── mapping_carrellisti.md
```

---

## 4. Inventario Completo dei Deliverable

### 4.1 Infrastruttura (DevOps)

| File | Descrizione | Stato |
|---|---|---|
| `.gitignore` | Esclusioni git (secrets, .env, __pycache__, *.egg) | ✅ COMPLETO |
| `.gitlab-ci.yml` | Pipeline: validate → test → deploy-dev → deploy-prod (4 stage) | ✅ COMPLETO |
| `databricks.yml` | DAB config: variabili catalog/schema per dev/prod, 8 job reference (aggiornato) | ✅ COMPLETO |
| `pytest.ini` | Config pytest con markers e cov-report | ✅ COMPLETO |
| `requirements-dev.txt` | pyspark, delta-spark, pytest, flake8, sqlfluff, openpyxl | ✅ COMPLETO |
| `infra/terraform/main.tf` | Root module, backend azurerm, module calls | ✅ COMPLETO |
| `infra/terraform/variables.tf` | Variabili: subscription_id, tenant_id, location, env | ✅ COMPLETO |
| `infra/terraform/outputs.tf` | Output: workspace URL, catalog names, SQL warehouse ID | ✅ COMPLETO |
| `infra/terraform/modules/unity_catalog/main.tf` | Cataloghi, schemi logistica/logistica_dm/condiviso, **external location landing zone ADLS**, storage credential, grants | ✅ COMPLETO |
| `infra/terraform/modules/unity_catalog/variables.tf` | storage_account_name, container_name, access_connector_id | ✅ COMPLETO |
| `infra/terraform/modules/unity_catalog/outputs.tf` | catalog_names, external_location_name | ✅ COMPLETO |
| `infra/terraform/modules/compute/main.tf` | Cluster policies DEV/PROD, SQL Warehouse medium | ✅ COMPLETO |
| `infra/terraform/modules/compute/variables.tf` | node_type, autoscale min/max | ✅ COMPLETO |
| `infra/terraform/modules/compute/outputs.tf` | cluster_policy_id, sql_warehouse_id | ✅ COMPLETO |
| `infra/terraform/modules/networking/main.tf` | NSG rule, VNet peering placeholder | ✅ COMPLETO |
| `infra/terraform/modules/networking/variables.tf` | oracle_host_cidr, nsg_name, resource_group | ✅ COMPLETO |

### 4.2 Workflow Databricks (8 job)

| File | Schedule | Descrizione |
|---|---|---|
| `workflows/logistica_landing_ingestion.yml` | 00:30 | Lettura CSV da ADLS landing zone → Bronze MERGE INTO Delta (tutti i 26 notebook) |
| `workflows/logistica_dim_refresh.yml` | 01:00 | Bronze→Silver→Gold dimensioni (fan-out parallelo) |
| `workflows/logistica_carichi.yml` | 02:00 | Bronze→Silver→Gold carichi, pesate, giacenze daily |
| `workflows/logistica_giacenze.yml` | 03:30 | Bronze→Silver_Daily→Silver_Agg→Gold_Daily→Gold_Monthly |
| `workflows/logistica_prep_sped.yml` | 04:30 | Bronze→Silver→Gold preparazione spedizioni |
| `workflows/logistica_trasporti.yml` | 05:00 | Bronze→Silver→Gold trasporti e ordini |
| `workflows/logistica_wave_e.yml` | 05:30 | CE178 branch + Carrellisti branch in parallelo |
| `workflows/logistica_datamart.yml` | 06:00 | 6 DataMart (schema gold_prod.logistica_dm) completamente in parallelo |

**Tutti ✅ COMPLETI**

> **Nota:** `logistica_datamart.yml` sostituisce il precedente `logistica_aggregati.yml`. Il nuovo workflow popola lo schema `gold_prod.logistica_dm` invece di tabelle A_* nello schema logistica.

### 4.3 Libreria Python `logistica_utils`

| File | Classe/Funzione chiave | Stato |
|---|---|---|
| `lib/logistica_utils/__init__.py` | Exports di tutte le classi | ✅ COMPLETO |
| `lib/logistica_utils/secret_helper.py` | `SecretHelper(scope)` → `get(key)` con fallback `os.environ` | ✅ COMPLETO |
| `lib/logistica_utils/logging_helper.py` | `Logger` JSON strutturato, livelli INFO/WARN/ERROR | ✅ COMPLETO |
| `lib/logistica_utils/delta_helper.py` | `merge_into()`, `replace_where()`, `get_max_watermark()` | ✅ COMPLETO |
| `lib/logistica_utils/dq_helper.py` | `check_no_nulls/duplicates/range/referential`, `run_all()`, `save_report()` | ✅ COMPLETO |
| `lib/logistica_utils/utils.py` | `surrogate_key_fallback()`, `cast_decimal()`, `add_ingestion_metadata()` | ✅ COMPLETO |
| `lib/setup.py` | Pacchetto installabile via `pip install -e .` | ✅ COMPLETO |

### 4.4 Template Notebook

| File | Pattern implementato | Stato |
|---|---|---|
| `notebooks/templates/template_bronze.py` | **Nuovo pattern landing zone:** legge CSV da ADLS external location → schema validation → MERGE INTO Delta (no JDBC Oracle) | ✅ COMPLETO |
| `notebooks/templates/template_silver.py` | Read Bronze → ROW_NUMBER dedup → cast_decimal → rename colonne (prefissi Oracle → nomi business) → merge_into → DQ | ✅ COMPLETO |
| `notebooks/templates/template_gold_fact.py` | Read Silver → join dimensioni (chiavi naturali, no surrogate ID) → measures → replace_where | ✅ COMPLETO |

### 4.5 Notebook Bronze (26) — Pattern Landing Zone Push

**Architettura ingestion:** i sistemi sorgente (Logistix, CND/STAT) inviano CSV in push su ADLS Gen2 landing zone. I notebook Bronze leggono da external location Unity Catalog ed eseguono MERGE INTO su tabelle Delta. **Nessun JDBC Oracle.**

#### Transazionali Logistix (7)

| File | Tabella Sorgente | Tipo | Stato |
|---|---|---|---|
| `bronze/transazionali/bronze_sto_tes_carichi.py` | STO_TES_CARICHI | MERGE INTO su chiave carico | ✅ COMPLETO |
| `bronze/transazionali/bronze_sto_righe_carico.py` | STO_RIGHE_CARICO | MERGE INTO su chiave riga | ✅ COMPLETO |
| `bronze/transazionali/bronze_pesate.py` | PESATE | MERGE INTO su chiave pesata | ✅ COMPLETO |
| `bronze/transazionali/bronze_tracciace178.py` | TRACCIACE178 | MERGE INTO su chiave traccia | ✅ COMPLETO |
| `bronze/transazionali/bronze_storico_riepiloghi.py` | STORICO_RIEPILOGHI | MERGE INTO su chiave riepilogo | ✅ COMPLETO |
| `bronze/transazionali/bronze_testate_bolle.py` | TESTATE_BOLLE | MERGE INTO su chiave bolla | ✅ COMPLETO |
| `bronze/transazionali/bronze_storico_bolle.py` | STORICO_BOLLE | MERGE INTO su chiave riga bolla | ✅ COMPLETO |

#### Anagrafiche Logistix (12)

| File | Tabella Sorgente | Tipo | Stato |
|---|---|---|---|
| `bronze/anagrafiche/bronze_dettaglio_carr.py` | DETTAGLIO_CARR | MERGE INTO su chiave | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_imbfmovim.py` | IMBFMOVIM | MERGE INTO su chiave | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_cartellino.py` | CARTELLINO | MERGE INTO su chiave | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_carrellisti.py` | CARRELLISTI | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_preparatori.py` | PREPARATORI | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_ricevitori.py` | RICEVITORI | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_spedizionieri.py` | SPEDIZIONIERI | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_struttura_mag.py` | STRUTTURA_MAG | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_corsie.py` | CORSIE | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_tabgen.py` | TABGEN | Full-load tabella generale | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_aree_merceologiche.py` | AREE_MERCEOLOGICHE | Full-load anagrafica | ✅ COMPLETO |
| `bronze/anagrafiche/bronze_classe_posto_pallet.py` | CLASSE_POSTO_PALLET | Full-load anagrafica | ✅ COMPLETO |

#### CND/STAT (7)

| File | Tabella Sorgente | Tipo | Stato |
|---|---|---|---|
| `bronze/cnd_stat/bronze_t_stock.py` | T_STOCK | MERGE INTO su chiave stock | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_t_pdv.py` | T_PDV | Full-load anagrafica PDV | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_t_vettori.py` | T_VETTORI | Full-load anagrafica vettori | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_t_trasp_mtv.py` | T_TRASP_MTV | MERGE INTO su chiave trasporto | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_t_prep_sped.py` | T_PREP_SPED | MERGE INTO su chiave prep sped | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_buoni_eco.py` | BUONI_ECO | MERGE INTO su chiave buono | ✅ COMPLETO |
| `bronze/cnd_stat/bronze_tipo_attivita_eco.py` | TIPO_ATTIVITA_ECO | Full-load tabella tipi | ✅ COMPLETO |

### 4.6 Notebook Silver (24)

**Nota sui nomi colonne:** le tabelle Silver rinominano sistematicamente le colonne dai prefissi Oracle ai nomi business. Esempi:
- `STCAR_*` → `cod_carico`, `data_carico`, `cod_fornitore`, ecc.
- `SRCAR_*` → `cod_riga_carico`, `cod_articolo`, `qta_ordinata`, ecc.
- `PSP_*` → `cod_preparazione`, `cod_operatore`, `data_prep`, ecc.
- `DTCRL_*` → `cod_carrellista`, `tipo_missione`, `durata_min`, ecc.
- `RPLPR_*` → `cod_riepilogo`, `cod_sito`, `num_colli`, ecc.

#### Dimensioni (7)

| File | Logica chiave | Stato |
|---|---|---|
| `silver/dimensioni/silver_dim_articolo.py` | MERGE INTO su cod_articolo, SCD Type 1, flag `_rec_non_trovato` | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_fornitore.py` | MERGE INTO su cod_fornitore | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_pdv.py` | MERGE INTO su cod_pdv | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_sito.py` | MERGE INTO su cod_sito | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_operatore.py` | MERGE INTO su matricola | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_corriere.py` | MERGE INTO su cod_corriere | ✅ COMPLETO |
| `silver/dimensioni/silver_dim_topografia.py` | MERGE INTO su cod_posizione | ✅ COMPLETO |

#### Carichi + Giacenze (6)

| File | Logica chiave | Stato |
|---|---|---|
| `silver/carichi/silver_carico_testata.py` | MERGE INTO, COALESCE fornitore, dedup ROW_NUMBER | ✅ COMPLETO |
| `silver/carichi/silver_carico_dettaglio.py` | JOIN con testata, flag `_art_non_trovato` | ✅ COMPLETO |
| `silver/carichi/silver_pesata.py` | Calcolo delta_qta, flag `_dq_peso_negativo` | ✅ COMPLETO |
| `silver/carichi/silver_traccia_ce178.py` | Dedup, parsing lotto/scadenza, _bronze_insert_ts | ✅ COMPLETO |
| `silver/giacenze/silver_giacenza_daily.py` | replaceWhere su data_foto (snapshot) | ✅ COMPLETO |
| `silver/giacenze/silver_giacenza_aggregata.py` | Aggregazione mensile per sito/articolo | ✅ COMPLETO |

#### Preparazione Spedizioni + Trasporti + Tracciabilità (11)

| File | Logica chiave | Stato |
|---|---|---|
| `silver/prep_sped/silver_storico_riepiloghi.py` | Dedup, normalizzazione colonne numeriche | ✅ COMPLETO |
| `silver/prep_sped/silver_bolle.py` | JOIN testate⋈righe, flag `bolla_annullata` | ✅ COMPLETO |
| `silver/prep_sped/silver_timbrature_sessioni.py` | MIN/MAX per operatore/data/sito, flag `sessione_incompleta` | ✅ COMPLETO |
| `silver/prep_sped/silver_prep_sped_integrata.py` | Triple JOIN: riepiloghi⋈sessioni⋈bolle | ✅ COMPLETO |
| `silver/trasporti/silver_ordini.py` | JOIN testate⋈righe ordini | ✅ COMPLETO |
| `silver/trasporti/silver_trasporti.py` | lead_time_consegna_gg = DATEDIFF(data_consegna, data_partenza) | ✅ COMPLETO |
| `silver/trasporti/silver_swap.py` | Dedup, link a ordine originale | ✅ COMPLETO |
| `silver/trasporti/silver_costo_trasporto.py` | CASE WHEN fasce peso, ×1.2 fallback se no contratto | ✅ COMPLETO |
| `silver/tracciabilita/silver_tracciabilita_lotto.py` | flag_scaduto, giorni_a_scadenza | ✅ COMPLETO |
| `silver/tracciabilita/silver_missione_carrellista.py` | durata_missione_min, classificazione tipo | ✅ COMPLETO |
| `silver/tracciabilita/silver_sessione_carrellista.py` | ore_produttive = GREATEST(SUM(dur)-30,0)/60 per sessione | ✅ COMPLETO |

### 4.7 Notebook Gold (23) — Gold Core + DataMart

**Architettura Gold:** nessun surrogate ID — le fact tables usano chiavi naturali (cod_*, data_*, matricola, ecc.) per semplicità di join e compatibilità con le SQL KPI views.

#### Dimensioni (9)

| File | Logica chiave | Stato |
|---|---|---|
| `gold/dimensioni/gold_dim_calendario.py` | Generazione PySpark pura, algoritmo Gauss Pasqua, festività italiane, ISO week, trimestri | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_struttura_merceologica.py` | 5 livelli gerarchia merceologica, MERGE INTO | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_articolo.py` | JOIN con struttura merceologica 5-level hierarchy | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_fornitore.py` | MERGE INTO su cod_fornitore | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_pdv.py` | MERGE INTO su cod_pdv | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_sito.py` | MERGE INTO su cod_sito | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_operatore.py` | MERGE INTO su matricola | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_corriere.py` | MERGE INTO su cod_corriere | ✅ COMPLETO |
| `gold/dimensioni/gold_dim_topografia.py` | MERGE INTO su cod_posizione | ✅ COMPLETO |

#### Fact Tables (7) + Late-Arriving Handler (1)

| File | Logica chiave | Stato |
|---|---|---|
| `gold/facts/gold_f_carico.py` | Chiavi naturali, DELTA_QTA, LEAD_TIME_GG, FLAG_SCARTO, log `_dim_missing_*` | ✅ COMPLETO |
| `gold/facts/gold_f_giacenze_daily.py` | replaceWhere su data_foto, qta_giacenza, valore_giacenza | ✅ COMPLETO |
| `gold/facts/gold_f_prep_sped.py` | **Regola 30 min** su (operatore, data, sito), produttivita_colli_ora | ✅ COMPLETO |
| `gold/facts/gold_f_ordini.py` | qta_mancante, fill_rate_riga, flag_swapped | ✅ COMPLETO |
| `gold/facts/gold_f_trasporto.py` | lead_time_vs_contratto, flag_ritardo | ✅ COMPLETO |
| `gold/facts/gold_f_tracciabilita_lotti.py` | qta_residua, giorni_a_scadenza, MERGE ON lotto+articolo | ✅ COMPLETO |
| `gold/facts/gold_f_movimentazione_carrellisti.py` | mode(tipo_missione), MERGE ON operatore+data+sito | ✅ COMPLETO |
| `gold/facts/gold_late_arriving_handler.py` | Re-processa righe quarantine non appena dimensione disponibile | ✅ COMPLETO |

#### DataMart — schema `gold_prod.logistica_dm` (6)

| File | Descrizione | Stato |
|---|---|---|
| `gold/datamart/gold_dm_inbound_mensile.py` | Aggregati mensili carichi, percentile_approx(0.9) lead time | ✅ COMPLETO |
| `gold/datamart/gold_dm_stock_mensile.py` | Aggregati mensili giacenze per sito e categoria | ✅ COMPLETO |
| `gold/datamart/gold_dm_outbound_mensile.py` | Aggregati mensili trasporti/spedizioni | ✅ COMPLETO |
| `gold/datamart/gold_dm_produttivita_mensile.py` | Aggregati mensili produttività per operatore e sito | ✅ COMPLETO |
| `gold/datamart/gold_dm_giacenze_monthly.py` | Giacenze mensili medie, massime, giorni stock-out | ✅ COMPLETO |
| `gold/datamart/gold_dm_turno_prep_sito.py` | Aggregazione per sito/turno, efficienza complessiva | ✅ COMPLETO |

### 4.8 SQL KPI Views (10) — Schema `gold_prod.logistica`

**Nota v2.0:** tutte le 10 view sono state riscritte con **chiavi naturali** (no surrogate ID). I join usano `cod_*`, `matricola`, `data_*` anziché SK_* per allineamento con l'architettura Gold aggiornata.

| File | KPI calcolati | Stato |
|---|---|---|
| `sql/kpi/kpi_lead_time_fornitore.sql` | Lead time medio/P90 per fornitore e mese | ✅ COMPLETO |
| `sql/kpi/kpi_qualita_ricevimento.sql` | % colli conformi, % scarti per fornitore | ✅ COMPLETO |
| `sql/kpi/kpi_saturazione_magazzino.sql` | % saturazione per sito, trend mensile | ✅ COMPLETO |
| `sql/kpi/kpi_aging_articoli.sql` | Aging in giorni, fasce 30/60/90/180+ gg | ✅ COMPLETO |
| `sql/kpi/kpi_produttivita_operatore.sql` | Colli/ora per operatore, confronto con media sito | ✅ COMPLETO |
| `sql/kpi/kpi_efficienza_sito_prep.sql` | Ore produttive vs ore totali per sito/turno | ✅ COMPLETO |
| `sql/kpi/kpi_fill_rate.sql` | Fill rate riga e ordine, % ordini completi | ✅ COMPLETO |
| `sql/kpi/kpi_costo_trasporto.sql` | Costo/collo, costo/kg per corriere e sito | ✅ COMPLETO |
| `sql/kpi/kpi_resa_corrieri.sql` | % consegne puntuali per corriere, trend | ✅ COMPLETO |
| `sql/kpi/kpi_bolle_annullate.sql` | % bolle annullate, motivi principali | ✅ COMPLETO |

### 4.9 SQL Ottimizzazione

| File | Contenuto | Stato |
|---|---|---|
| `sql/optimize/gold_optimize_tables.sql` | OPTIMIZE + ZORDER per tutte le tabelle Gold Core e DataMart, ANALYZE TABLE, note VACUUM | ✅ COMPLETO |

### 4.10 Test Suite (64 test)

| File | Test count | Coverage |
|---|---|---|
| `tests/conftest.py` | — | SparkSession locale con Delta, mock_dbutils, DataFrame sample (100 righe) |
| `tests/test_logistica_utils.py` | 25 | SecretHelper, Logger, DeltaHelper, DQHelper, surrogate_key_fallback, cast_decimal |
| `tests/test_dim_calendario.py` | 15 | Range date, no gap, festività italiane, ISO week, trimestri |
| `tests/test_regola_30min.py` | 9 | 2h→1.5h, 20min→0, 30min→0, 31min→1/60h, multi-sessione, protezione /0 |
| `tests/test_dq_carichi.py` | 15 | no_duplicates, no_nulls, numeric_range, referential integrity |

### 4.11 Documenti Prodotti

| File | Contenuto | Stato |
|---|---|---|
| `DOCS/analisi/mapping_carichi.md` | Mapping completo sorgente→Bronze→Silver→Gold per area Carichi | ✅ COMPLETO |
| `DOCS/analisi/mapping_giacenze.md` | Mapping area Giacenze, logica snapshot giornaliero | ✅ COMPLETO |
| `DOCS/analisi/mapping_prep_spedizioni.md` | Mapping Prep Spedizioni, casi applicazione regola 30 min | ✅ COMPLETO |
| `DOCS/analisi/mapping_trasporti.md` | Mapping Trasporti, logica calcolo costi | ✅ COMPLETO |
| `DOCS/analisi/mapping_ce178.md` | Mapping Tracciabilità CE178, compliance normativa | ✅ COMPLETO |
| `DOCS/analisi/mapping_carrellisti.md` | Mapping Missioni e Sessioni Carrellisti | ✅ COMPLETO |
| `DOCS/decision_matrix_ingestion.md` | 46 tabelle sorgente: strategia ingestion push ADLS, schema validazione — v2.0 | ✅ COMPLETO |
| `DOCS/Piano di Sviluppo - Logistico 2.0.xlsx` | Piano sprint e attività con stato aggiornato | ✅ COMPLETO |
| `DOCS/Tabelle Sorgenti - Logistico 2.0.xlsx` | 46 tabelle sorgente con dettaglio colonne | ✅ COMPLETO |
| `DOCS/Tabelle Target CDT_DW - Logistico 2.0.xlsx` | **NUOVO** — 22 tabelle target CDT_DW con 248 colonne mappate | ✅ COMPLETO |
| `DOCS/rollback_plan.md` | Trigger, RACI, procedura 6 step (~3h totali), checklist 10 punti | ✅ COMPLETO |
| `DOCS/cutover_plan.md` | 12 pre-requisiti, timeline T-7gg→T=08:00, 15 smoke test, go/no-go | ✅ COMPLETO |
| `DOCS/runbook.md` | Scheduling diagram (8 workflow), lettura log JSON, alert, procedure anomalie, SLA | ✅ COMPLETO |

---

## 5. Stato Attività per Sprint

### FASE 0 — Fondamenta Infrastrutturali

| Sprint | Attività | Stato | Note |
|---|---|---|---|
| 0.1 Unity Catalog & Storage | 0.1.1 Definizione struttura cataloghi | ✅ COMPLETO | Terraform unity_catalog module — gold per ambiente (gold_dev/gold_prod), 2 schemi per dominio (logistica + logistica_dm) |
| | 0.1.2 External Location + Storage Credential landing zone | ✅ COMPLETO | Terraform: azurerm_access_connector, ADLS Gen2 landing container |
| | 0.1.3 Grant permessi Unity Catalog | ✅ PARZIALE | Schema grants definiti, applica con `terraform apply` |
| 0.2 GitLab CI/CD & DAB | 0.2.1 .gitlab-ci.yml 4 stage | ✅ COMPLETO | Pronto per push |
| | 0.2.2 databricks.yml con target dev/prod | ✅ COMPLETO | 8 job, variabili parametrizzate |
| | 0.2.3 Cluster policies Terraform | ✅ COMPLETO | compute module |
| 0.3 Connettività | 0.3.1 ADLS landing zone external location | ✅ COMPLETO | Sistemi sorgente inviano CSV in push |
| | 0.3.2 Secret scope + Key Vault | ⏳ ACCESSI | Richiede Azure Portal + Databricks workspace attivi |
| | 0.3.3 Test end-to-end landing zone | ⏳ ACCESSI | Richiede ADLS + Databricks workspace attivi |

### FASE 1 — Master Data & Dimensioni Condivise

| Sprint | Attività | Stato | Note |
|---|---|---|---|
| 1.1 Calendario & Merceologiche | gold_dim_calendario.py | ✅ COMPLETO | PySpark puro, algoritmo Gauss |
| | gold_dim_struttura_merceologica.py | ✅ COMPLETO | 5 livelli gerarchia |
| | Test dim_calendario | ✅ COMPLETO | 15 test pytest |
| 1.2 Articoli, Fornitori, PdV | silver/gold dim_articolo, fornitore, pdv | ✅ COMPLETO | MERGE INTO SCD Type 1, chiavi naturali |
| 1.3 Dimensioni Logistiche | silver/gold dim_sito, operatore, corriere, topografia | ✅ COMPLETO | MERGE INTO |

### FASE 2 — Wave A: Carichi (Inbound)

| Sprint | Attività | Stato |
|---|---|---|
| 2.1 Bronze Carichi | 7 notebook transazionali Logistix — landing zone push, MERGE INTO | ✅ COMPLETO |
| 2.2 Silver Carichi | silver_carico_testata/dettaglio, silver_pesata, silver_traccia_ce178 — colonne rinominate | ✅ COMPLETO |
| 2.3 Gold F_CARICO | gold_f_carico (chiavi naturali), gold_late_arriving_handler | ✅ COMPLETO |
| 2.4 KPI & Validazione | kpi_lead_time_fornitore, kpi_qualita_ricevimento, test_dq_carichi — v2.0 chiavi naturali | ✅ COMPLETO |

### FASE 3 — Wave B: Giacenze (Stock)

| Sprint | Attività | Stato |
|---|---|---|
| 3.1 Bronze Giacenze | T_STOCK (CND/STAT) — landing zone push, MERGE INTO | ✅ COMPLETO |
| 3.2 Silver Giacenze | silver_giacenza_daily, silver_giacenza_aggregata | ✅ COMPLETO |
| 3.3 Gold F_GIACENZE | gold_f_giacenze_daily, dm_giacenze_monthly (schema logistica_dm) | ✅ COMPLETO |
| 3.4 Workflow & Validazione | logistica_giacenze.yml, kpi_saturazione_magazzino, kpi_aging_articoli | ✅ COMPLETO |

### FASE 4 — Wave C: Preparazione Spedizioni (Picking)

| Sprint | Attività | Stato |
|---|---|---|
| 4.1 Bronze Prep Sped | STORICO_RIEPILOGHI, TESTATE_BOLLE, STORICO_BOLLE, CARTELLINO — landing zone push | ✅ COMPLETO |
| 4.2 Silver Normalizzazione | silver_storico_riepiloghi, silver_bolle | ✅ COMPLETO |
| 4.3 Silver Timbrature | silver_timbrature_sessioni, silver_prep_sped_integrata | ✅ COMPLETO |
| 4.4 Gold F_PREP_SPED | gold_f_prep_sped (regola 30 min), dm_turno_prep_sito | ✅ COMPLETO |
| 4.5 KPI & Anomalie | kpi_produttivita_operatore, kpi_efficienza_sito_prep, test_regola_30min | ✅ COMPLETO |

### FASE 5 — Wave D: Trasporti (Outbound)

| Sprint | Attività | Stato |
|---|---|---|
| 5.1 Bronze Trasporti | T_TRASP_MTV, T_PDV, T_VETTORI (CND/STAT) — landing zone push | ✅ COMPLETO |
| 5.2 Silver Trasporti | silver_ordini, silver_trasporti, silver_swap | ✅ COMPLETO |
| 5.3 Silver Costi + Gold | silver_costo_trasporto, gold_f_ordini, gold_f_trasporto | ✅ COMPLETO |
| 5.4 KPI & Workflow | kpi_fill_rate, kpi_costo_trasporto, kpi_resa_corrieri, logistica_trasporti.yml | ✅ COMPLETO |

### FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti

| Sprint | Attività | Stato |
|---|---|---|
| 6.1 CE178 | bronze_tracciace178, silver_tracciabilita_lotto, gold_f_tracciabilita_lotti | ✅ COMPLETO |
| 6.2 Carrellisti | DETTAGLIO_CARR + CARTELLINO bronze, silver_missione/sessione_carrellista, gold_f_movimentazione_carrellisti | ✅ COMPLETO |
| 6.3 Workflow & Validazione | logistica_wave_e.yml, kpi_bolle_annullate | ✅ COMPLETO |

### FASE 7 — KPI Aggregati & Reporting

| Sprint | Attività | Stato |
|---|---|---|
| 7.1 DataMart Mensili | 6 dm_* notebook — schema gold_prod.logistica_dm | ✅ COMPLETO |
| 7.2 Dashboard BI | 10 SQL KPI views riscritte con chiavi naturali v2.0, gold_optimize_tables.sql | ✅ COMPLETO |
| 7.3 Validazione KPI E2E | Documentato in runbook.md — eseguibile solo con dati reali | ⏳ ACCESSI |

### FASE 8 — Shadow Mode, Validazione & Cut-Over

| Sprint | Attività | Stato |
|---|---|---|
| 8.1 Shadow Mode Setup | cutover_plan.md, rollback_plan.md predisposti | ✅ PARZIALE |
| 8.2 Shadow Mode Run | Richiede ambiente attivo (10+ giorni lavorativi) | ⏳ ACCESSI |
| 8.3 Preparazione Cut-Over | Checklist in cutover_plan.md completa | ✅ PARZIALE |
| 8.4 Cut-Over & Post-Live | Richiede accesso coordinato sistemi sorgente + Databricks | ⏳ ACCESSI |

---

## 6. Pattern e Convenzioni Tecniche

### 6.1 Naming Convention

```
Tabelle Bronze:    {catalog_bronze}.logistica.{nome_tabella_sorgente}
Tabelle Silver:    {catalog_silver}.logistica.{nome_business}
Tabelle Gold Core: gold_prod.logistica.{prefisso}_{nome}
  Prefissi Gold:   dim_  (dimensioni)
                   f_    (fact tables)
                   _dim_missing_  (quarantine Late-Arriving)
Tabelle DataMart:  gold_prod.logistica_dm.dm_{nome}
SQL KPI Views:     gold_prod.logistica.kpi_{nome}

Notebook:          {livello}_{area}_{nome}.py
Workflow YAML:     logistica_{area}.yml
```

### 6.2 Pattern Ingestion Landing Zone (Bronze)

```
1. Sistema sorgente deposita CSV su ADLS Gen2 landing zone
   (path: abfss://landing@<account>.dfs.core.windows.net/logistica/{tabella}/{data}/*.csv)
2. Notebook Bronze legge CSV tramite Unity Catalog External Location
3. Schema validation: verifica presenza colonne attese, dtype check
4. add_ingestion_metadata(): aggiunge _bronze_insert_ts, _source_file, _batch_id
5. MERGE INTO tabella Delta Bronze su chiave naturale sorgente
   (idempotenza: ri-eseguibile senza duplicati)
```

### 6.3 Idempotenza

Ogni notebook è progettato per essere ri-eseguito in sicurezza:

| Livello | Strategia |
|---|---|
| Bronze (transazionale) | MERGE INTO su chiave naturale sorgente — update se esiste, insert se nuovo |
| Bronze (anagrafica) | Full-load con replaceWhere su data batch — sovrascrive partizione |
| Silver | MERGE INTO su chiave naturale business — SCD Type 1 |
| Gold Core (fatti giornalieri) | replaceWhere su data — sovrascrive partizione giorno |
| Gold Core (fatti cumulativi) | MERGE INTO su chiave naturale composita |
| Gold DataMart | replaceWhere su anno/mese — sovrascrive partizione mese |

### 6.4 Gestione Secrets

```python
# Produzione (Databricks)
sh = SecretHelper(scope="logistica-kv-scope")
adls_sas = sh.get("adls-landing-sas-token")

# Locale/CI (os.environ)
os.environ["LOGISTICA_KV_SCOPE_ADLS_LANDING_SAS_TOKEN"] = "test_token"
```

### 6.5 Late-Arriving Dimensions

Quando una chiave naturale non trova corrispondenza nella dimensione:

```
1. Riga originale salvata in gold_prod.logistica._dim_missing_{nome_dim}
2. gold_late_arriving_handler.py (schedulato settimanalmente) ri-processa le righe
   non appena la dimensione viene popolata con il record mancante
3. Log dimensioni mancanti visibile in DQ report per monitoraggio
```

---

## 7. Regole di Business Critiche Implementate

### 7.1 Regola 30 Minuti Attrezzaggio (PRIORITÀ ALTA)

Applicata in `gold_f_prep_sped.py`:

```
Per ogni (cod_operatore, data_prep, cod_sito):
  - Ordina sessioni per ora_entrata
  - Sessione rank=1 (prima del giorno):
      ore_produttive = MAX(0, durata_minuti - 30) / 60
  - Sessioni rank>1:
      ore_produttive = durata_minuti / 60
  
produttivita_colli_ora = CASE
  WHEN SUM(ore_produttive) > 0 THEN colli_preparati / SUM(ore_produttive)
  ELSE 0
END
```

**Casi test coperti:** 2h→1.5h, 20min→0, 30min→0, 31min→1/60h, operatore multi-sito stesso giorno, protezione divisione per zero.

### 7.2 Calcolo Costo Trasporto a Fasce Peso

Applicata in `silver_costo_trasporto.py`:

```sql
costo_stimato = CASE
  WHEN peso_kg <= 30   THEN tariffa_fascia_a * peso_kg
  WHEN peso_kg <= 100  THEN tariffa_fascia_b * peso_kg
  WHEN peso_kg <= 300  THEN tariffa_fascia_c * peso_kg
  ELSE                      tariffa_fascia_d * peso_kg
END * 1.2  -- fallback +20% se corriere non in contratto
```

### 7.3 Flag CE178 Lotti Scaduti

Applicata in `silver_tracciabilita_lotto.py`:

```python
flag_scaduto = when(col("data_scadenza") < current_date(), lit(1)).otherwise(lit(0))
giorni_a_scadenza = datediff(col("data_scadenza"), current_date())
```

### 7.4 DIM_CALENDARIO Generazione Completa

Generata in PySpark puro (senza dipendenza da sistemi sorgente) in `gold_dim_calendario.py`:

- Algoritmo di Gauss per calcolo Pasqua per qualsiasi anno
- Festività nazionali italiane hardcoded (01/01, 06/01, 25/04, 01/05, 02/06, 15/08, 01/11, 08/12, 25/12, 26/12)
- Festività mobile: Pasqua, Lunedì dell'Angelo
- ISO week, trimestre, semestre, giorno lavorativo (BOOL)

---

## 8. Attività in Sospeso (ACCESSI)

Le seguenti attività richiedono accesso agli ambienti infrastrutturali:

### 8.1 Azure / Databricks (Priorità ALTA — blocca tutto il resto)

| Attività | Blocca |
|---|---|
| Provisioning Azure Databricks Workspace | Tutto |
| Creazione Azure Key Vault + Secret Scope | Tutti i notebook |
| Provisioning Azure ADLS Gen2 storage account + container landing | Ingestion Bronze |
| Configurazione ADLS External Location in Unity Catalog | Tabelle Delta Bronze |
| `terraform apply` modulo unity_catalog | Cataloghi, schemi logistica e logistica_dm |
| Upload `logistica_utils` come Databricks Library | Tutti i notebook |
| Registrazione notebook in Databricks Repo (via Git) | Workflow |

### 8.2 Configurazione Sistemi Sorgente

| Attività | Pre-requisito |
|---|---|
| Configurazione Logistix per push CSV su ADLS landing zone | Storage account + SAS token/managed identity |
| Configurazione CND/STAT per push CSV su ADLS landing zone | Storage account + SAS token/managed identity |
| Validazione formato CSV (delimiter, encoding, header) | Accordo con team sorgente |
| Calibrazione scheduling push vs scheduling workflow | Coordinamento operativo |

### 8.3 Validazione Funzionale (Post-Primo Carico)

| Attività | Quando |
|---|---|
| Confronto record count sistemi sorgente vs Bronze | Dopo primo run landing ingestion |
| Validazione KPI Gold vs dati storici CDT_DW | Dopo primo run Gold |
| Shadow mode (10+ giorni lavorativi) | Sprint 8.2 |
| Test cut-over con finestra 16:00-08:00 | Sprint 8.4 |

### 8.4 MicroStrategy / BI

| Attività | Pre-requisito |
|---|---|
| Connessione MicroStrategy → SQL Warehouse Databricks | SQL Warehouse attivo |
| Importazione SQL KPI views (schema gold_prod.logistica.kpi_*) | Accesso MicroStrategy Designer |
| Connessione DataMart (schema gold_prod.logistica_dm.dm_*) | Accesso MicroStrategy Designer |
| Creazione dashboard prototipo | Accesso MicroStrategy Web |

---

## 9. Piano di Onboarding del Team

### Passo 1 — Setup locale (giorno 1)

```bash
# Clone repository
git clone https://gitlab.com/aperion/logistico-2.0.git
cd logistico-2.0

# Installa dipendenze
pip install -r requirements-dev.txt
pip install -e lib/

# Variabili ambiente per test locali
export LOGISTICA_KV_SCOPE_ADLS_LANDING_SAS_TOKEN=test_token

# Esegui test suite
pytest tests/ -v --tb=short
```

**Risultato atteso:** 64 test passano in ~3 minuti su macchina con 16GB RAM.

### Passo 2 — Infrastruttura (giorni 2-3, DevOps)

```bash
cd infra/terraform
terraform init
terraform plan -var-file="dev.tfvars"
# Review output, poi:
terraform apply -var-file="dev.tfvars"
```

File `dev.tfvars` da compilare (non committare):

```hcl
subscription_id          = "<azure-subscription-id>"
tenant_id                = "<azure-tenant-id>"
databricks_account_id    = "<databricks-account-id>"
storage_account_name     = "<adls-account-name>"
landing_container_name   = "landing"
access_connector_id      = "<managed-identity-resource-id>"
```

### Passo 3 — Deploy su Databricks (giorno 3, DevOps)

```bash
# Installa Databricks CLI
pip install databricks-cli

# Configura profilo
databricks configure --profile dev

# Deploy con DAB
databricks bundle deploy --target dev

# Verifica job creati (8 workflow)
databricks bundle run logistica_landing_ingestion --target dev
```

### Passo 4 — Prima Esecuzione (giorni 4-5, Developer)

Ordine consigliato per il primo carico:

```
1. logistica_landing_ingestion  → Popola Bronze (tutti i 26 notebook CSV→Delta)
2. logistica_dim_refresh        → Popola tutte le 9 dimensioni
3. logistica_carichi            → F_CARICO (verifica Late-Arriving = 0)
4. logistica_giacenze           → F_GIACENZE_DAILY
5. logistica_trasporti          → F_ORDINI + F_TRASPORTO
6. logistica_prep_sped          → F_PREP_SPED (verifica regola 30 min)
7. logistica_wave_e             → CE178 + Carrellisti
8. logistica_datamart           → Tabelle dm_* in gold_prod.logistica_dm
```

### Passo 5 — Validazione (giorno 6, BI Developer + Developer)

```sql
-- Smoke test su Gold Core
SELECT COUNT(*) FROM gold_prod.logistica.f_carico;
SELECT COUNT(*) FROM gold_prod.logistica.dim_calendario;       -- atteso ~3650 (10 anni)
SELECT COUNT(*) FROM gold_prod.logistica._dim_missing_fornitore; -- atteso 0 (ideale)

-- Smoke test su DataMart
SELECT COUNT(*) FROM gold_prod.logistica_dm.dm_inbound_mensile;
SELECT COUNT(*) FROM gold_prod.logistica_dm.dm_stock_mensile;

-- Smoke test KPI Views
SELECT * FROM gold_prod.logistica.kpi_lead_time_fornitore LIMIT 10;
```

---

## 10. Checklist di Go-Live

### Provisioning e Infrastruttura

- [ ] Provisioning Azure ADLS Gen2 storage account e container landing
- [ ] Deploy Terraform (Unity Catalog: cataloghi bronze_dev/prod, silver_dev/prod, gold_dev/prod, control_dev/prod con schemi logistica/logistica_dm/prep_logistica/etl/parametri, external location landing zone, compute)
- [ ] Configurazione Azure Key Vault + Databricks Secret Scope
- [ ] SQL Warehouse MEDIUM attivo per BI e KPI views
- [ ] Cluster policy DEV/PROD applicata ai developer

### Configurazione Sistemi Sorgente

- [ ] Configurazione Logistix per push CSV su ADLS landing zone (7 tabelle transazionali + 12 anagrafiche)
- [ ] Configurazione CND/STAT per push CSV su ADLS landing zone (7 tabelle)
- [ ] Validazione formato CSV (delimiter, encoding UTF-8, header row) con team sorgente
- [ ] Test carico manuale singolo CSV → verifica Bronze MERGE INTO

### Deploy Applicativo

- [ ] Deploy DAB su Databricks workspace prod (`databricks bundle deploy --target prod`)
- [ ] Verifica 8 workflow visibili e schedulati in Databricks Jobs UI
- [ ] Upload libreria `logistica_utils` come cluster library (prod)
- [ ] GitLab CI/CD: tutti e 4 gli stage passano su branch `main`

### Test Integrazione End-to-End

- [ ] Test integrazione end-to-end con dati reali (primo carico completo)
- [ ] Verifica catena: landing_ingestion → dim_refresh → carichi → giacenze → prep_sped → trasporti → wave_e → datamart
- [ ] Confronto record count sistemi sorgente vs Bronze delta < 0.1%
- [ ] Verifica F_CARICO: late-arriving = 0 (idealmente)
- [ ] Verifica F_PREP_SPED: regola 30 min su campione 5 operatori

### Validazione Data Quality

- [ ] Validazione Data Quality su tutti i layer (DQ report `gold_prod.logistica.dq_report`)
- [ ] Tabelle `_dim_missing_*` vuote o monitorate
- [ ] CE178: tutte le spedizioni con flag_ce178=1 hanno lotto tracciato
- [ ] KPI views: confronto valori vs dati storici CDT_DW (scostamento < 1%)

### Workflow e Monitoring

- [ ] Attivazione workflow (inizialmente in pausa — unpause dopo validazione)
- [ ] Alert configurati (Slack/Email) per job failure
- [ ] OPTIMIZE + ZORDER eseguito su tabelle Gold dopo primo carico (`gold_optimize_tables.sql`)
- [ ] VACUUM schedulato (cadenza mensile)

### Shadow Mode (FASE 8)

- [ ] 10 giorni lavorativi di run parallelo sistemi sorgente + Databricks
- [ ] Scostamento KPI < 1% per tutti i 10 KPI monitorati
- [ ] Zero errori critici in log (categoria ERROR nel JSON log)
- [ ] Rollback plan testato in ambiente DEV

### Formazione e Go-Live

- [ ] Formazione utenti BI su nuovi dataset Gold Core e DataMart (schemi gold_prod.logistica e gold_prod.logistica_dm)
- [ ] Formazione su KPI views (gold_prod.logistica.kpi_*) per team MicroStrategy
- [ ] Finestra cut-over comunicata a tutti gli stakeholder
- [ ] Rollback plan comunicato e approvato dal responsabile progetto

---

*Documento aggiornato — Logistico 2.0 v2.0 — Stato: Completato — In attesa di deploy*  
*Team: Cloud Solution Architect · Cloud DevOps Engineer Senior · Cloud Solution Developer Senior · BI Developer Senior*  
*Data: 2026-05-30*
