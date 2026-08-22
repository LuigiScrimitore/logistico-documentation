# Workflow YAML (DAB) — Revision Spec

**Data:** 2026-06-08 · **Autore:** Cloud Data Architect · **Scope:** layer orchestrazione (Databricks Asset Bundles)
**Riferimenti:** `Landing & Bronze - Revision Spec.md`, `Silver - Revision Spec.md`, `Gold - Revision Spec.md`, `Open Points - Logistico 2.0.md` (OP-02, OP-06, OP-07, OP-09, OP-19, OP-23, OP-26).

## 1. Principi

1. **Parametri uniformi** allineati ai widget standard dei notebook v3.0:
   - `env` (dev/prod) — propagato a tutti i task
   - `run_date` (YYYY-MM-DD, default `{{job.start_time.iso_date}}`) — sostituisce il vecchio `load_date`
   - `landing_base_path` (solo Bronze) — pattern `<source>-landing` (OP-07)
   - `file_format` (solo Bronze) — `auto`/`csv`/`parquet`
   - `siti` (solo Bronze Logistix multi-sito) — comma-separated, default tutti i 9
   - `retail_master_schema` (solo Gold) — placeholder per le lookup master Retail (OP-02)
2. **Rimuovere** parametri obsoleti `load_date`, `catalog_bronze`/`catalog_silver`/`catalog_gold`: i cataloghi derivano da `get_catalog(layer, env)` dentro i notebook.
3. **Eliminare/disabilitare** task verso notebook **DEPRECATI** (master Retail OP-02, ex-fact spostati in datamart, JDBC legacy OP-26).
4. **Allineare nomi target** ai nuovi: `LU_*` (lookup), `F_*` (fact), `A_*` (aggregati in `logistica_dm`).
5. **Cluster (OP-19, raccomandazione):** allineare a Reply quando confermato — DBR `15.4.x-scala2.12`, VM `Standard_D4s_v3`. Mantenere il pattern attuale ma esporre le caratteristiche come variabili.
6. **Multi-environment:** ambienti riconosciuti **solo `dev` e `prod`** (separati e speculari). Mantenere il `default: env=dev`; il deploy `prod` si fa via `databricks bundle deploy --target prod`. Un eventuale terzo ambiente sarà deciso in seguito.
7. **Idempotenza:** `max_concurrent_runs: 1` su tutti i workflow.

## 2. Mappatura workflow → notebook (post-revisione)

### `logistica_landing_ingestion` (00:30) — Bronze CND + STAT
| task_key | notebook |
|----------|----------|
| `bronze_t_stock` | `notebooks/bronze/giacenze/bronze_giacenze_snapshot` |
| `bronze_t_pdv` | `notebooks/bronze/anagrafiche/bronze_pdv` |
| `bronze_t_vettori` | `notebooks/bronze/trasporti/bronze_vettori` |
| `bronze_t_trasp_mtv` | `notebooks/bronze/trasporti/bronze_trasporti` |
| `bronze_t_prep_sped` | `notebooks/bronze/prep_spedizioni/bronze_timbrature` |
| `bronze_buoni_eco` | `notebooks/bronze/stat/bronze_buoni_eco` |
| `bronze_tipo_attivita_eco` | `notebooks/bronze/stat/bronze_tipo_attivita` |
| `bronze_storico_riepiloghi` (**nuovo**, OP-16) | `notebooks/bronze/prep_spedizioni/bronze_prep_riepiloghi` |
| `bronze_testate_bolle` (**nuovo**, OP-16) | `notebooks/bronze/prep_spedizioni/bronze_prep_bolle_testate` |
| `bronze_storico_bolle` (**nuovo**, OP-16) | `notebooks/bronze/prep_spedizioni/bronze_prep_bolle_righe` |

**Rimosso:** task `landing_ingestion_gate` (notebook non esistente). Il gate logico è la naturale dipendenza `depends_on` dei workflow downstream sull'intero job di landing.

### `logistica_carichi` (02:00)
| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_sto_tes_carichi` | `notebooks/bronze/carichi/bronze_carichi_testate` | — |
| `bronze_sto_righe_carico` | `notebooks/bronze/carichi/bronze_carichi_dettagli` | — |
| `bronze_pesate` | `notebooks/bronze/carichi/bronze_pesate` | — |
| `bronze_tracciace178` | `notebooks/bronze/carichi/bronze_traccia_ce178` | — |
| `silver_carico_testata` | `notebooks/silver/carichi/silver_carichi_testate` | bronze_sto_tes_carichi |
| `silver_carico_dettaglio` | `notebooks/silver/carichi/silver_carichi_dettagli` | bronze_sto_righe_carico |
| `silver_pesata` | `notebooks/silver/carichi/silver_pesate` | bronze_pesate |
| `silver_traccia_ce178` | `notebooks/silver/carichi/silver_traccia_ce178` | bronze_tracciace178 |
| `silver_tracciabilita_lotto` | `notebooks/silver/tracciabilita/silver_tracciabilita_lotto` | silver_traccia_ce178 |
| `gold_f_carico` | `notebooks/gold/carichi/gold_f_carico` | silver_carico_testata, silver_carico_dettaglio, silver_pesata |
| `gold_late_arriving` | `notebooks/gold/carichi/gold_late_arriving_handler` | gold_f_carico |
| `gold_f_tracciabilita_lotti` | `notebooks/gold/tracciabilita/gold_f_tracciabilita_lotti` | silver_tracciabilita_lotto |

### `logistica_giacenze` (03:30)
| task_key | notebook | depends_on |
|----------|----------|------------|
| `silver_giacenza_daily` | `notebooks/silver/giacenze/silver_giacenze_daily` | — (bronze già fatto da landing) |
| `silver_giacenza_aggregata` | `notebooks/silver/giacenze/silver_giacenze_aggregata` | silver_giacenza_daily |
| `gold_f_giacenze_daily` | `notebooks/gold/giacenze/gold_f_giacenze_daily` | silver_giacenza_daily |

**Rimossi:** task `silver_dim_pdv` (DEPRECATO OP-02), `silver_dim_corriere` (spostato in `dim_refresh`), `gold_f_giacenze_monthly` (deprecato → A_GIACENZE_MONTHLY in datamart).

### `logistica_prep_sped` (04:30)
| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_dettaglio_carr` | `notebooks/bronze/carrellisti/bronze_missioni_carr` | — |
| `bronze_imbfmovim` | `notebooks/bronze/giacenze/bronze_movimenti_magazzino` | — |
| `bronze_cartellino` | `notebooks/bronze/carrellisti/bronze_cartellino` | — |
| `silver_prep_riepilogo` | `notebooks/silver/prep_spedizioni/silver_prep_riepiloghi` | — |
| `silver_prep_bolle` | `notebooks/silver/prep_spedizioni/silver_prep_bolle` | — |
| `silver_timbrature_sessioni` | `notebooks/silver/prep_spedizioni/silver_timbrature_sessioni` | — |
| `silver_prep_sped_integrata` | `notebooks/silver/prep_spedizioni/silver_prep_sped_integrata` | silver_prep_riepilogo, silver_timbrature_sessioni |
| `silver_missione_carrellista` | `notebooks/silver/tracciabilita/silver_missione_carrellista` | bronze_dettaglio_carr |
| `silver_sessione_carrellista` | `notebooks/silver/tracciabilita/silver_sessione_carrellista` | bronze_cartellino |
| `gold_f_prep_sped` | `notebooks/gold/prep_spedizioni/gold_f_prep_sped` | silver_prep_riepilogo, silver_timbrature_sessioni |
| `gold_f_movimentazione_carrellisti` | `notebooks/gold/carrellisti/gold_f_movimentazione_carrellisti` | silver_missione_carrellista, silver_sessione_carrellista |

**Rimosso:** task verso `gold_f_turno_prep_sito` (deprecato → A_TURNO_PREP_SITO in datamart).

### `logistica_trasporti` (05:00)
| task_key | notebook | depends_on |
|----------|----------|------------|
| `silver_ordini` | `notebooks/silver/trasporti/silver_ordini` | — (Bronze sto_tes_carichi da workflow carichi) |
| `silver_trasporti` | `notebooks/silver/trasporti/silver_trasporti` | — (Bronze t_trasp_mtv da landing) |
| `silver_swap` | `notebooks/silver/trasporti/silver_swap` | silver_trasporti |
| `silver_costo_trasporto` | `notebooks/silver/trasporti/silver_costo_trasporto` | silver_trasporti |
| `gold_f_ordini` | `notebooks/gold/trasporti/gold_f_ordini` | silver_ordini |
| `gold_f_trasporto` | `notebooks/gold/trasporti/gold_f_trasporto` | silver_trasporti, silver_costo_trasporto |

**Rimossi (OP-26):** task verso Bronze JDBC residui (`contratti_corrieri`, `ordini_righe`, `ordini_testate`, `swap`) — esclusi dallo scheduling fino a migrazione.

### `logistica_dim_refresh` (01:00)
| task_key | notebook | note |
|----------|----------|------|
| `silver_dim_sito` | `notebooks/silver/dimensioni/silver_dim_sito` | |
| `silver_dim_operatore` | `notebooks/silver/dimensioni/silver_dim_operatore` | |
| `silver_dim_corriere` | `notebooks/silver/dimensioni/silver_dim_corriere` | |
| `silver_dim_topografia` | `notebooks/silver/dimensioni/silver_dim_topografia` | |
| `gold_lu_sito` | `notebooks/gold/dimensioni/gold_dim_sito` | target LU_SITO |
| `gold_lu_operatore` | `notebooks/gold/dimensioni/gold_dim_operatore` | target LU_OPERATORE |
| `gold_lu_corriere` | `notebooks/gold/dimensioni/gold_dim_corriere` | target LU_CORRIERE |
| `gold_lu_topografia` | `notebooks/gold/dimensioni/gold_dim_topografia` | target LU_TOPOGRAFIA |
| `gold_lu_area_mercl_logis` | `notebooks/gold/dimensioni/gold_dim_struttura_merceologica` | target LU_AREA_MERCL_LOGIS |

**Rimossi (OP-02):** task verso le 4 master `silver_dim_articolo`/`fornitore`/`pdv` e i corrispondenti `gold_dim_articolo`/`fornitore`/`pdv`/`calendario` → tutti DEPRECATI, master letti da Retail. **Rimossi anche** i task `silver_dim_struttura_merceologica` (la silver è stata confluita) e `gold_dim_calendario` (deprecato OP-02).

### `logistica_wave_e` (05:30) — CE178 wave (può essere assorbito da carichi)
| task_key | notebook |
|----------|----------|
| `silver_tracciabilita_lotto` | (già nel carichi) |
| `gold_f_tracciabilita_lotti` | (già nel carichi) |

**Decisione:** mantenere il workflow come "stub" disabilitato (alias) finché non ci sono task specifici dell'area "wave E" non già coperti da `logistica_carichi`. In alternativa **rimuovere il workflow** e mantenere solo il pass dai carichi.

### `logistica_datamart` (06:00) — ex `logistica_aggregati`
| task_key | notebook | target |
|----------|----------|--------|
| `a_inbound_mensile` | `notebooks/gold/aggregati/gold_a_inbound_mensile` | A_INBOUND_MENSILE |
| `a_giacenze_monthly` | `notebooks/gold/aggregati/gold_dm_giacenze_monthly` | A_GIACENZE_MONTHLY |
| `a_stock_mensile` | `notebooks/gold/aggregati/gold_a_stock_mensile` | A_STOCK_MENSILE (dep. a_giacenze_monthly) |
| `a_outbound_mensile` | `notebooks/gold/aggregati/gold_a_outbound_mensile` | A_OUTBOUND_MENSILE |
| `a_produttivita_mensile` | `notebooks/gold/aggregati/gold_a_produttivita_mensile` | A_PRODUTTIVITA_MENSILE |
| `a_turno_prep_sito` | `notebooks/gold/aggregati/gold_dm_turno_prep_sito` | A_TURNO_PREP_SITO |

## 3. Header file YAML standard

Ogni file deve riportare in cima:
```
###############################################################################
# Logistico 2.0 — Workflow: <nome>
# Versione: 3.0.0 — 2026-06-08
# Schedule: <quartz_cron> Europe/Rome
# Dipende da: <lista>
###############################################################################
```

## 4. `databricks.yml` root
Verificare:
- include di tutti i file `workflows/*.yml` rivisti
- variabili globali `env`, `landing_base_path`, `retail_master_schema`
- target `dev`/`prod` (ambienti riconosciuti: solo questi due) con workspace path coerenti
- nessuna referenza a notebook deprecati

## 5. QA finale
- Tutti i `notebook_path` puntano a file esistenti (esclusi quelli deprecati)
- Tutti i `task_key` univoci per workflow
- Tutti i `depends_on.task_key` referenziano task definiti
- Tutti i task usano `env` + `run_date` (+ eventuali parametri specifici)
- Nessun riferimento a `load_date`, `catalog_bronze`/`catalog_silver`/`catalog_gold`
- Nessun riferimento a notebook deprecati nei `notebook_path`
- YAML sintatticamente valido
