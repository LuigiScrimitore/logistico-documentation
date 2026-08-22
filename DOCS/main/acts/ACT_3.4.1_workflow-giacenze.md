# ACT_3.4.1 · Workflow logistica_giacenze (03:30)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 3.4
**Sprint**: 3.4 — Workflow & Validazione Giacenze
**Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD (deploy workflow Databricks pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_3.1.6 (bronze giacenze), ACT_3.2.4, ACT_3.3.2   **Blocca**: ACT_3.4.2 (validazione BA)
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
L'area giacenze deve girare silver→gold in un workflow schedulato alle 03:30, a valle
dell'ingestion bronze (`logistica_landing_ingestion`, che carica T_STOCK in Bronze SNAPSHOT —
vedi [[ACT_3.1.6_workflow-bronze-giacenze]]). La definizione (`workflows/logistica_giacenze.yml`,
v3.0.0) è pronta ma il deploy in cloud è pendente.

## Obiettivo
Workflow Databricks `logistica_giacenze` schedulato alle 03:30 (Europe/Rome) che orchestra silver e
gold giacenze e produce `F_GIACENZE_DAILY` del giorno. Fatto = job schedulato e verde in ambiente cloud.

## Analisi tecnica
Dal file reale `workflows/logistica_giacenze.yml`:
- **Schedule**: `quartz_cron_expression: "0 30 3 * * ?"`, `timezone_id: Europe/Rome`, `pause_status:
  UNPAUSED`, `max_concurrent_runs: 1`. Notifica `on_failure` → luigi.scrimitore@aperion.it.
- **Parametri**: `env` (default `dev`), `run_date` (default `{{job.start_time.iso_date}}`).
- **Compute**: **serverless** (ADR-0009), allineato in [[ACT_9007]]: nessun `job_clusters` nel yml, i
  task non dichiarano compute; il wheel `logistica_utils` arriva dal blocco job-level `environments`
  (`environment_key: default`, `environment_version: "2"`, `dependencies: [../lib/dist/logistica_utils-*.whl]`)
  con `environment_key: default` su ogni task. Rimossi `spark_conf` e `custom_tags`: sizing gestito da
  Databricks, tuning da ritarare in cloud ([[adr/0015_tuning_cloud_non_trasferibile]]), eventuali Spark
  conf a livello **sessione** nel notebook.
- **Task (DAG)**:
  1. `silver_giacenza_daily` → notebook `notebooks/silver/giacenze/silver_giacenze_daily`
     (max_retries 2, timeout 7200s). **Da verificare naming**: sul filesystem il notebook prep giacenze
     è `silver_prep_giacenze.py` (sorgente `silver.logistica.t_stock` → `silver.logistica_curated.giacenze`,
     replaceWhere/dyn-overwrite su `DATA_FOTO`); confermare che il path del yml risolva a questo notebook.
  2. `silver_giacenza_aggregata` (depends_on daily) → `silver_giacenze_aggregata` (aggregati
     cross-magazzino, GROUP BY `MAG_COD`+`DATA_FOTO`), timeout 3600s.
  3. `gold_f_giacenze_daily` (depends_on daily, parallelo all'aggregata) →
     `notebooks/gold/giacenze/gold_f_giacenze_daily`, timeout 7200s. Legge
     `silver.logistica_curated.giacenze` filtrando `DATA_FOTO = run_date`, scrive
     `gold.logistica.F_GIACENZE_DAILY` con `replaceWhere DATA_FOTO`, `partitionBy DATA_FOTO`.
- **Libreria**: wheel `logistica_utils` da `../lib/dist/logistica_utils-*.whl` (dichiarato nelle
  `environments`; il vecchio `libraries:` job-level è stato rimosso perché non valido nel Jobs API).
- **Nota**: l'aggregato mensile `A_GIACENZE_MONTHLY` NON è in questo workflow — sta nel workflow
  `logistica_datamart` (06:00). Questo job copre solo silver+gold daily.
- **Dipendenza dati bronze**: il workflow assume T_STOCK già in Bronze SNAPSHOT (da landing_ingestion);
  se la landing CND del giorno è assente i silver escono `NO_DATA` graceful (non bloccano).
- **Ordering (OP-29)**: in cloud il DAG garantisce l'ordine `catena_unificata → t_stock → prep_giacenze
  → gold`; il problema di ordinamento è solo locale (`run_all_silver` alfabetico, fisiologico — vedi
  pipeline_mapping §"Dipendenze di ordinamento Silver"). Il workflow è la soluzione produttiva a OP-29.
- Definizione al ~90%; manca deploy/apply in cloud (non eseguibile offline).

## Sviluppo (diario)
- 2026-07-03 · avanzamento ~90%; definizione workflow pronta, deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Run schedulato completo verde end-to-end (3 task); `F_GIACENZE_DAILY` con partizione `DATA_FOTO=run_date`
  popolata (~54.7k righe nel big re-run come ordine di grandezza).
- DQ verdi (`check_not_null` su `MAG_SITO_COD`/`ART_COD`, `check_row_count`).
- Nessun errore accesso landing/UC; idempotenza replaceWhere verificata su re-run.

## Esito
— (in attesa di deploy cloud)

## Follow-up
- Sblocca la validazione funzionale BA [[ACT_3.4.2_validazione-ba-giacenze]] e la quadratura
  [[ACT_3.3.6_quadratura-giacenze-oracle]].
- Risolvere discrepanza naming notebook `silver_giacenza_daily` (yml) vs `silver_prep_giacenze.py`
  (filesystem) → ACT emergente 9000+ se è un refuso da correggere.
- Allineamento serverless (ADR-0009 vs yml) **fatto** in [[ACT_9007]]; resta `databricks bundle validate`
  e il primo run al gate cloud.
