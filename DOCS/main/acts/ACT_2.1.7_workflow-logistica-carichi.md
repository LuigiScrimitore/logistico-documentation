# ACT_2.1.7 · Workflow logistica_carichi (task chain + retry)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 2.1
**Sprint**: 2.1
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD — deploy workflow su Databricks pendente
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.1.2, ACT_2.1.3, ACT_2.1.4, ACT_2.1.5   **Blocca**: —
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
I 4 notebook Bronze Carichi (`notebooks/bronze/carichi/bronze_carichi_testate`, `bronze_carichi_dettagli`, `bronze_pesate`, `bronze_traccia_ce178`) vanno orchestrati in un workflow Databricks con catena di task e retry, per l'esecuzione schedulata sui 22 siti. Il YML esiste già (`workflows/logistica_carichi.yml`, v3.0.0) ma il deploy richiede l'ambiente cloud.

## Obiettivo
Workflow `logistica_carichi` deployato ed eseguibile: task chain Bronze con retry configurati. Fatto = job visibile e schedulabile su Databricks, run verde sui task Bronze. Nota: il YML corrente contiene già anche i task Silver ([[ACT_2.2.7]]) e Gold ([[ACT_2.3.5]]) — questa ACT copre il sotto-blocco Bronze; la versione end-to-end Bronze→Silver→Gold è tracciata in [[ACT_2.3.5]].

## Analisi tecnica
- **Definizione**: `workflows/logistica_carichi.yml` (v3.0.0, 2026-06-08). Incluso nel bundle root `databricks.yml` via `include: workflows/*.yml`.
- **Schedule**: quartz `0 0 2 * * ?` Europe/Rome (02:00), `max_concurrent_runs: 1`. Dipende a monte da `logistica_landing_ingestion` (00:30) e `logistica_dim_refresh` (01:00).
- **Task Bronze (DELTA_MERGE)** — anchor YAML `&bronze_logistix` (params `env`, `run_date`, `landing_base_path`, `file_format`, `siti`):
  - `bronze_sto_tes_carichi` → `bronze_carichi_testate` — `max_retries: 2`, `timeout 7200s`
  - `bronze_sto_righe_carico` → `bronze_carichi_dettagli` — `max_retries: 2`, `timeout 7200s`
  - `bronze_pesate` → `bronze_pesate` — `max_retries: 2`, `timeout 3600s`
  - `bronze_tracciace178` → `bronze_traccia_ce178` — `max_retries: 2`, `timeout 3600s`
  I 4 task Bronze sono paralleli (nessun `depends_on` reciproco); i Silver dipendono ciascuno dal proprio Bronze.
- **Compute**: **serverless** ([[ADR-0009]], allineamento fatto in [[ACT_9007]]): nessun `job_clusters` nel YML; i task senza compute dichiarato girano su serverless (Photon/autoscaling gestiti da Databricks). Il wheel arriva dal blocco job-level `environments` (`environment_key: default`, `spec.environment_version: "2"`, `dependencies: [../lib/dist/logistica_utils-*.whl]`), con `environment_key: default` su ogni task. Rimossi `spark_conf` (eventuali conf a livello **sessione** nel notebook — ADR-0015) e `custom_tags` (costi via serverless usage/budget policy, [[ACT_9013]]). Sizing gestito da Databricks; tuning da ritarare in cloud ([[adr/0015_tuning_cloud_non_trasferibile]]).
- **Param `siti`**: default nel YML = sottoinsieme dev (`lgax,lgcx,lcax,lccx,lexx,locx,lscx,lslx`); a regime va portato ai 22 siti (memory `runner-siti-default-22`).
- **Libreria**: wheel `logistica_utils` da `../lib/dist/logistica_utils-*.whl`, dichiarato nelle `environments` job-level (il vecchio `libraries:` a livello job è stato rimosso: nel Jobs API `libraries` è per-task). Alert on_failure a luigi.scrimitore@aperion.it.
- **Deploy via DAB** (release kit, [[ADR-0017]]): `databricks bundle deploy -t dev` (target `dev` default in `databricks.yml`); non eseguibile offline.

## Sviluppo (diario)
- 2026-07-03 · YML scritto; avanzamento ~90%; deploy cloud pendente.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- `databricks bundle validate` OK; `databricks bundle deploy -t dev` senza errori; job `logistica_carichi` visibile e schedulabile su Databricks Workflows.
- `databricks bundle run logistica_carichi` → run verde sui 4 task Bronze end-to-end.
- Retry funzionanti su fallimento simulato (max_retries=2 rispettati).

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
Nessuna al momento.
