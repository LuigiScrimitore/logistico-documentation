# ACT_1.3.7 · Workflow `logistica_dim_refresh` (01:00)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 1.3
**Sprint**: 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)
**Fase / Wave**: FASE 1 — Master Data & Dimensioni
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (deploy workflow pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_1.3.6 (Gold DIM logistiche), FASE 0 (ambiente cloud)   **Blocca**: —
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
Le DIM logistiche vanno rinfrescate schedulate prima dei fact. Il workflow `logistica_dim_refresh`
orchestra il refresh giornaliero delle **dimensioni logistiche** alle 01:00 (dopo
`logistica_landing_ingestion` delle 00:30, che carica i Bronze). Precisazione OP-02: le DIM master
Retail (articolo/fornitore/pdv/calendario → `LU_ART_RADICE`, `LU_FORNITORE`, `LU_PDV`,
`LU_GIORNO/LU_MESE`) **NON sono in questo workflow** — sono deprecate/read-only dal flusso Master Data
Retail. Qui restano solo: sito, operatore, corriere, topografia + `LU_AREA_MERCL_LOGIS`. Il YML è
scritto ma il deploy in cloud è pendente (dipende da FASE 0).

## Obiettivo
Workflow `logistica_dim_refresh` schedulato alle 01:00 Europe/Rome e deployato in cloud.
Fatto = il job gira in cloud e completa senza errori il refresh di tutte le DIM logistiche (Silver +
Gold LU_*), dopo il completamento della landing ingestion.

## Analisi tecnica
**File**: `workflows/logistica_dim_refresh.yml` (v3.0.0). `name: logistica_dim_refresh`.
- **Schedule**: `quartz_cron_expression: "0 0 1 * * ?"`, `timezone_id: Europe/Rome`,
  `pause_status: UNPAUSED`. `max_concurrent_runs: 1`. `email_notifications.on_failure:
  luigi.scrimitore@aperion.it`.
- **Parametri**: `env` (default `dev`), `run_date` (default `{{job.start_time.iso_date}}`).
- **Dipendenza upstream**: `logistica_landing_ingestion` (Bronze anagrafiche logistix/CND caricati —
  vedi [[ACT_1.3.1_bronze-siti-operatori-corrieri]]).
- **Compute**: **serverless** ([[ADR-0009]], allineato con [[ACT_9007]]): nessun `job_clusters` nel YML,
  i task non dichiarano compute e girano su serverless (Photon e autoscaling gestiti da Databricks).
  Blocco job-level `environments` con `environment_key: default`, `spec.environment_version: "2"` e
  `dependencies: [../lib/dist/logistica_utils-*.whl]`; ogni task porta `environment_key: default`.
  Rimossi `spark_conf` (su serverless le Spark conf si impostano a livello **sessione** nel notebook —
  ADR-0015) e `custom_tags` (attribuzione costi via serverless usage/budget policy, [[ACT_9013]]).
  Il **sizing** non è più dichiarato: lo gestisce Databricks e il tuning si ritara in cloud
  ([[adr/0015_tuning_cloud_non_trasferibile]]).
- **Task Silver** (`max_retries: 2`, `timeout_seconds: 1800`):
  `silver_dim_sito` (da `struttura_mag`, distinct `MAG_SITO_COD`),
  `silver_dim_operatore` (UNION 4 anagrafiche carrellisti/preparatori/ricevitori/spedizionieri — OP-15,
  + self-healing OP-28 e membro `ND`),
  `silver_dim_corriere` (da `t_vettori`/`vettori_track`),
  `silver_dim_topografia` (`CELLA_COD` da concat `STRM_*`).
- **Task Gold LU_*** (`depends_on` la rispettiva Silver, tranne l'area merceologica):
  `gold_lu_sito` ← silver_dim_sito, `gold_lu_operatore` ← silver_dim_operatore (chiave
  `OPERATORE_COD+SITO_COD+TIPO_OPERATORE`), `gold_lu_corriere` ← silver_dim_corriere,
  `gold_lu_topografia` ← silver_dim_topografia,
  `gold_lu_area_mercl_logis` (notebook `gold_dim_struttura_merceologica`, **senza depends_on** — legge
  direttamente `bronze.aree_merceologiche`; vedi [[ACT_1.1.3_dim-struttura-merceologica]]).
Il residuo è il deploy sull'ambiente Databricks cloud, non disponibile fino a FASE 0.

## Sviluppo (diario)
- 2026-07-03 · YML scritto; parziale al 90%, deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Deploy del workflow (Databricks Asset Bundle / job API) senza errori di validazione YML.
- Run schedulato alle 01:00 (o trigger manuale) che completa **tutti** i task Silver→Gold in stato
  Success, dopo `logistica_landing_ingestion`.
- Grafo dipendenze rispettato (ogni `gold_lu_*` parte solo dopo la sua Silver).
- Tabelle Gold `LU_SITO`, `LU_OPERATORE`, `LU_CORRIERE`, `LU_TOPOGRAFIA`, `LU_AREA_MERCL_LOGIS`
  aggiornate (`DWH_UPDATED_AT`/`_silver_ts` del giorno), righe > 0.

## Esito
— (in attesa di ambiente cloud FASE 0)

## Follow-up
- Divergenza serverless vs cluster classico **risolta** in [[ACT_9007]]; resta da eseguire
  `databricks bundle validate` e il primo run al gate cloud ([[ACT_GATE-1]]).
- Al deploy completato → passare a record e chiudere.
