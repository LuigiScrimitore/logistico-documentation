# ACT_7.3.3 · Performance baseline (E2E vs finestra batch Oracle)

**Status**: in-progress
**Type**: analysis
**Origin**: sprint 7.3
**Sprint**: 7.3 — Validazione KPI End-to-End
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (misura cloud pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: —   **Blocca**: —
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Occorre una baseline di performance end-to-end della pipeline Databricks (landing → bronze → silver → gold fact
→ aggregati/KPI) da confrontare con la finestra batch Oracle legacy, per dimostrare la sostenibilità del nuovo
flusso. La baseline **locale** è pronta; manca la misura sull'ambiente **cloud reale**.

## Obiettivo
Baseline performance E2E misurata e confrontata con la finestra batch Oracle.
Fatto = tempi E2E cloud misurati e comparati al batch Oracle, entro il target SLA concordato.

## Analisi tecnica
- **Baseline locale già disponibile**; residuo = misurazione sull'ambiente cloud e confronto con la finestra batch Oracle.
- **Target SLA di riferimento** (`02_pipeline_mapping.md` §SLA): completamento di **tutti i workflow entro le 05:30**,
  **dati disponibili in MicroStrategy entro le 06:00**. La catena termina con il workflow `logistica_datamart`
  (schedule 06:00, `workflows/logistica_aggregati.yml`, [[ACT_7.1.6_workflow-logistica-datamart]]) che gira dopo i fact.
- **⚠️ I tempi locali NON sono predittivi del cloud**: i job girano su compute **serverless** (nessun sizing dichiarato
  nei workflow — [[ACT_9007]]), quindi il sizing lo gestisce Databricks e le durate vanno misurate in cloud
  ([[adr/0015_tuning_cloud_non_trasferibile]], [[adr/0009_job_cluster_serverless]]); il locale è single-machine con
  spill anomali (es. storico_bolle_uniche ~57GB) → usare la baseline locale solo come ordine di grandezza/logica, non
  come numero atteso in cloud. Ambito incrementale/pruning che regge la finestra: [[adr/0010_incrementale_watermark_pattern2_pruning]].
- Strumenti misura cloud: durate task/job dai run Databricks (Spark UI, job run history) per wave/workflow; sommare
  i percorsi del DAG giornaliero (fact → aggregati) per il tempo E2E.

## Sviluppo (diario)
- 2026-07-03 · avanzamento 20%: baseline locale ok; misura cloud pendente.

## Verifica
Report tempi E2E cloud vs finestra batch Oracle entro il target concordato (SLA 05:30 workflow / 06:00 MicroStrategy);
evidenza dei tempi per workflow/wave dai run reali.

## Esito
— (misura cloud pendente)

## Follow-up
Nessuna al momento.
