# ACT_3.1.6 · Workflow Bronze Giacenze (03:00)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 3.1
**Sprint**: 3.1 — Bronze Giacenze
**Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD (deploy workflow Databricks pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_3.1.2, ACT_3.1.3, ACT_3.1.4   **Blocca**: ACT_3.4.1 (workflow giacenze end-to-end)
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
I bronze giacenze devono girare schedulati ogni notte per popolare lo snapshot del giorno prima del
layer silver/gold. In produzione l'ingestion dei bronze giacenze avviene tramite il workflow
`logistica_landing_ingestion` (che carica T_STOCK in Bronze SNAPSHOT): il workflow giacenze end-to-end
[[ACT_3.4.1_workflow-giacenze]] a 03:30 **dipende** dal fatto che i bronze siano già popolati. Questa
ACT copre la parte bronze/ingestion (schedulazione ~03:00, upstream del silver/gold). Il workflow è
definito ma non ancora deployato in cloud.

## Obiettivo
Bronze giacenze schedulati (~03:00, a monte del workflow silver/gold delle 03:30) che popolano gli
snapshot `t_stock`, `catena`, `catena_esterni`, `struttura_mag`. Fatto = job schedulato e verde in
ambiente cloud, con partizioni `_bronze_load_date` del giorno popolate.

## Analisi tecnica
- **Notebook orchestrati** (da `02_pipeline_mapping.md` §Giacenze):
  - `bronze_giacenze_snapshot.py` → `bronze.logistica.t_stock` (source `cnd`, SNAPSHOT, ~150k righe).
    Widget: `env`, `run_date`, `landing_base_path`, `file_format`. Scrittura `replaceWhere`
    su `_bronze_load_date`, `partitionBy("_bronze_load_date")`. Esce `NO_DATA` se landing assente.
  - `bronze_catena.py` → `bronze.logistica.catena` (source `logistix`, SNAPSHOT, ~158k/g, multisito).
  - `bronze_catena_esterni.py` → `bronze.logistica.catena_esterni` (SNAPSHOT, ~5.3k/g).
  - `bronze_struttura_mag.py` (in `notebooks/bronze/anagrafiche/`) → `bronze.logistica.struttura_mag`
    (anagrafica FULL, mappa locazioni per il join in `silver_t_stock`).
- **Compute**: **serverless** (ADR-0009), allineato in [[ACT_9007]]: anche
  `workflows/logistica_giacenze.yml` non dichiara più `job_clusters` — i task girano su serverless con
  il wheel `logistica_utils` fornito dal blocco `environments` (`environment_key: default`). Sizing
  gestito da Databricks; tuning da ritarare in cloud ([[adr/0015_tuning_cloud_non_trasferibile]]),
  eventuali Spark conf a livello **sessione** nel notebook.
- **Landing path**: `{base}/{source}-landing/{table}/{YYYY}/{MM}/{DD}/`; struttura *pending OP-07*
  (convenzione Foconi da confermare con Reply) → validare prima dello schedule PROD.
- Definizione pronta al ~90%; manca il deploy/apply in cloud (non eseguibile offline).

## Sviluppo (diario)
- 2026-07-03 · avanzamento ~90%; definizione workflow pronta, deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Run schedulato completo verde; per ogni tabella partizione `_bronze_load_date = run_date` popolata
  (`SELECT COUNT(*) ... WHERE _bronze_load_date = run_date`).
- Nessun errore di accesso landing ADLS / Unity Catalog; conteggi righe coerenti con gli ordini di
  grandezza attesi (t_stock ~150k, catena ~158k, esterni ~5.3k).
- Idempotenza: re-run stesso giorno non raddoppia (verifica `replaceWhere`).

## Esito
— (in attesa di deploy cloud)

## Follow-up
- Si integra a monte del workflow silver/gold giacenze [[ACT_3.4.1_workflow-giacenze]] (03:30).
- Backfill storico degli stessi bronze: [[ACT_3.1.5_backfill-storico-giacenze]].
- Divergenza cluster serverless vs classic (ADR-0009 vs yml) **risolta** in [[ACT_9007]]; resta la
  validazione `databricks bundle validate` / run reale al gate cloud.
