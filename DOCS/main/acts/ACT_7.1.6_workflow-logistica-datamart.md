# ACT_7.1.6 · Workflow `logistica_datamart` (fan-out, 06:00)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 7.1
**Sprint**: 7.1 — Aggregati Mensili DataMart
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD (deploy workflow pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_7.1.2, ACT_7.1.3, ACT_7.1.4, ACT_7.1.5   **Blocca**: —
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto e motivazione
Gli aggregati DataMart mensili in `gold_prod.logistica_dm.A_*` (solo `GROUP BY` sui fact `F_*`, che
devono quindi essere già calcolati) vanno orchestrati da un unico workflow Databricks schedulato con
fan-out sui task e schedule giornaliera alle 06:00 Europe/Rome. Senza il workflow deployato in cloud i
DataMart non si aggiornano in automatico e le viste KPI (`kpi_*`) e MicroStrategy leggono dati fermi.

La definizione del workflow è **già scritta** in `workflows/logistica_aggregati.yml` (v3.0.0, 2026-06-08,
il `name:` interno è `logistica_datamart` — ex `logistica_aggregati`). Il residuo è **solo il deploy sul
workspace cloud** via Asset Bundle (DAB), bloccato dall'accesso infra Azure/Databricks.

## Obiettivo
Workflow `logistica_datamart` operativo in cloud: fan-out sui 6 task DataMart, schedule 06:00.
Fatto = workflow deployato (`databricks bundle deploy -t dev`) ed eseguito con successo su un run schedulato,
con le 6 tabelle `A_*` aggiornate al giorno corrente.

## Analisi tecnica
Sorgente di verità del workflow: **`workflows/logistica_aggregati.yml`**. Elementi reali già definiti:
- **Schedule**: `quartz_cron_expression: "0 0 6 * * ?"`, `timezone_id: Europe/Rome`, `pause_status: UNPAUSED`.
- **Fan-out — 6 task** (non 4: gli aggregati sono 6), ciascuno `notebook_task` verso `notebooks/gold/aggregati/`:
  - `a_inbound_mensile` → `gold_a_inbound_mensile` (da `F_CARICO`, grana `FORNITORE_COD+SITO_COD+ANNO_MESE`)
  - `a_giacenze_monthly` → `gold_dm_giacenze_monthly` (da `F_GIACENZE_DAILY`)
  - `a_stock_mensile` → `gold_a_stock_mensile` (**`depends_on: a_giacenze_monthly`**, passthrough DM→DM)
  - `a_outbound_mensile` → `gold_a_outbound_mensile` (full outer `F_ORDINI`/`F_TRASPORTO`)
  - `a_produttivita_mensile` → `gold_a_produttivita_mensile` (da `F_PREP_SPED`, cartoni/quintali — OP-27)
  - `a_turno_prep_sito` → `gold_dm_turno_prep_sito` (giornaliero, `SITO_COD+DATA_PREPARAZ`)
- **Idempotenza**: `replaceWhere` su `ANNO_MESE`/`DATA_PREPARAZ` (dichiarato nella `description` del job).
- **Parametri**: `env` (default `dev`), `run_date` (`{{job.start_time.iso_date}}`); passati ai notebook via `base_parameters`.
- **Compute**: **serverless** ([[adr/0009_job_cluster_serverless]]), allineato in [[ACT_9007]]: nessun `job_clusters`
  nel YML: i task non dichiarano compute (Photon e autoscaling gestiti da Databricks) e prendono il wheel
  `logistica_utils` dal blocco job-level `environments` (`environment_key: default`, `environment_version: "2"`,
  `dependencies: [../lib/dist/logistica_utils-*.whl]`). Rimossi `spark_conf` (eventuali conf a livello **sessione**
  nel notebook, ADR-0015) e `custom_tags` (costi via serverless usage/budget policy, [[ACT_9013]]). Il **sizing** non
  è più dichiarato: lo gestisce Databricks e il tuning **si ri-tara a fresco in cloud**
  ([[adr/0015_tuning_cloud_non_trasferibile]]).
- **Retry/timeout**: `max_retries: 2`, `timeout_seconds` 3600–5400 per task.
- **Notifiche**: on_failure/on_success → `luigi.scrimitore@aperion.it`; `max_concurrent_runs: 1`.
- **Precedenza globale**: gli aggregati leggono i fact → questo workflow gira **dopo** i workflow giornalieri
  `F_*` (cfr. `milestones/fase_7.md` §3 "aggregati per ultimi"; `run_all_gold.py` ordina già aggregati dopo fact).

Deploy (da `11_devops_handoff_databricks.md` FASE B): `databricks bundle validate -t dev` → `databricks bundle deploy -t dev`;
il workflow è tra gli **8 job DAB** (`databricks.yml` + `workflows/*.yml`), compute **serverless** (nessun `node_type_id`
nel YML). `bundle validate` e run reali sono **cloud-gated** (nessun CLI in locale): da eseguire al gate ACT_GATE-1.

## Sviluppo (diario)
- 2026-07-03 · workflow al 90%: definizione fan-out pronta (`logistica_aggregati.yml` v3.0.0), deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Run schedulato (o `databricks bundle run logistica_datamart -t dev`) che completa i 6 task in SUCCESS.
- Controllo freschezza tabelle in `gold_prod.logistica_dm` (6 `A_*`) al `run_date` corrente.
- `a_stock_mensile` parte solo dopo `a_giacenze_monthly` (dipendenza rispettata).
- Coerenza con i fact: quadratura aggregati vs `F_*` (già verificata offline sul run 2026-06-19, cfr. `milestones/fase_7.md` §6).

## Esito
— (deploy cloud pendente; definizione workflow completa e validata offline)

## Follow-up
Nessuna al momento.
