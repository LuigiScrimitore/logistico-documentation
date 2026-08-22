# ACT_5.4.4 · Workflow logistica_trasporti (05:00)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 5.4
**Sprint**: 5.4 — KPI Trasporti & Workflow
**Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (deploy workflow pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_5.1.7, ACT_5.3.2, ACT_5.4.1, ACT_5.4.2, ACT_5.4.3   **Blocca**: esercizio schedulato trasporti end-to-end
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
Il workflow end-to-end trasporti (silver→gold) è definito ma il deploy in cloud è pendente. Vedi [`../sprint_agile/sprint_5.4.md`](../sprint_agile/sprint_5.4.md) (5.4.4: "deploy cloud pendente", PARZ. 90%).

La definizione è già nel repo: **`workflows/logistica_trasporti.yml`** (v3.0.0, 2026-06-08).

## Obiettivo
Workflow `logistica_trasporti` schedulato (05:00 Europe/Rome) attivo su cloud. Fatto = job gira su serverless e produce i Gold trasporti (`F_ORDINI`, `F_TRASPORTO`).

## Analisi tecnica
- **Definizione**: `workflows/logistica_trasporti.yml` — `schedule.quartz_cron_expression: "0 0 5 * * ?"`, tz Europe/Rome, `pause_status: UNPAUSED`, `max_concurrent_runs: 1`, alert on_failure → luigi.scrimitore@aperion.it. Parametri `env` (dev), `run_date`.
- **Compute**: **serverless** ([[adr/0009_job_cluster_serverless]]), allineato in [[ACT_9007]]: nel YML non c'è più alcun `job_clusters`; i task girano su serverless e prendono il wheel `logistica_utils` dal blocco job-level `environments` (`environment_key: default`, `environment_version: "2"`, `dependencies: [../lib/dist/logistica_utils-*.whl]`). Rimossi `spark_conf` (eventuali conf a livello **sessione** nel notebook, ADR-0015) e `custom_tags` (costi via serverless usage/budget policy, [[ACT_9013]]); sizing gestito da Databricks, tuning da ritarare in cloud ([[adr/0015_tuning_cloud_non_trasferibile]]).
- **Task (DAG reale)**:
  - `silver_ordini` (← `bronze.sto_tes_carichi`, logistix)
  - `silver_trasporti` (← `bronze.t_trasp_mtv` CND) → `silver_swap`, `silver_costo_trasporto`
  - `gold_f_ordini` (replaceWhere `ANNO_MESE`, dep. `silver_ordini`)
  - `gold_f_trasporto` (replaceWhere `DATA_BOLLA`/`GIORNO_BOLLA_SPED_ID`, grana MTV [[adr/0013_scope_trasporti_mtv]], dep. `silver_trasporti`+`silver_costo_trasporto`)
- **Dipendenze upstream**: `logistica_carichi` (bronze `sto_tes_carichi` → silver_ordini) e `logistica_landing_ingestion` (bronze `t_trasp_mtv`). ⚠️ I **4 Bronze JDBC residui (OP-26) sono ESCLUSI dallo scheduling** (header del YML) fino a migrazione — cfr. [[ACT_5.1.7_backfill-workflow-bronze-trasporti]].
- **KPI**: ⚠️ correzione — le viste KPI (5.4.1-3) **non** sono task di questo workflow. Sono **viste SQL** in `sql/kpi/` (`gold_kpi_fill_rate.sql`, `gold_kpi_costo_trasporto.sql`, `gold_kpi_resa_corrieri.sql`) su schema `gold_prod.logistica`, deployate separatamente. Il workflow si ferma ai Gold. `COSTO_STIMATO_EUR` è placeholder (`peso*0.15`, OP-27/listini assenti).

## Sviluppo (diario)
- 2026-07-03 · PARZIALE ~90%; `logistica_trasporti.yml` pronto; deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Run schedulato (05:00) o on-demand con esito OK; tutti i task del DAG verdi.
- Gold `F_ORDINI` e `F_TRASPORTO` aggiornati (replaceWhere sulla partizione del `run_date`).
- Viste KPI (`kpi_fill_rate`, `kpi_costo_trasporto`, `kpi_resa_corrieri`) leggibili a valle.
- DQ interni verdi ([[adr/0014_dq_alerting_interni]]).

## Esito
— (in attesa di deploy cloud/PROD)

## Follow-up
- Allineamento compute a serverless **fatto** in [[ACT_9007]]; resta `databricks bundle validate` e il primo run al gate di deploy (cloud-gated).
