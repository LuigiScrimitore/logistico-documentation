# ACT_7.2.4 · Tuning SQL Warehouse (size, auto-suspend)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 7.2
**Sprint**: 7.2 — MicroStrategy & Ottimizzazione Query
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (richiede SQL Warehouse cloud)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: —   **Blocca**: —
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Il SQL Warehouse che serve MicroStrategy (ACT_7.2.1) e le viste KPI (`gold_prod.logistica.kpi_*`) va
dimensionato (size del cluster / scaling min-max) e configurato per l'**auto-suspend**, per bilanciare
prestazioni di reporting e costo. Attività eseguibile **solo sul warehouse cloud reale**: i parametri non
sono ricavabili offline né trasferibili dal collaudo locale (vedi Analisi tecnica).

## Obiettivo
SQL Warehouse tarato: size adeguata al carico reporting e auto-suspend impostato.
Fatto = parametri (size, min/max cluster, auto-suspend, eventuale Photon/serverless) applicati sul warehouse
cloud e validati sotto carico reale MicroStrategy.

## Analisi tecnica
- **Richiede warehouse cloud attivo** → non avviabile offline.
- **Tuning NON ereditabile dal locale** ([[adr/0015_tuning_cloud_non_trasferibile]]): il sizing (memoria, spill,
  cluster) si **ri-tara a fresco** partendo dai default e osservando gli Spark UI / profilo costi reali; è la
  **logica** algoritmica (non il sizing) a migrare. Vale sia per il compute serverless dei job ([[adr/0009_job_cluster_serverless]])
  sia per il SQL Warehouse di reporting. NB: i workflow non dichiarano più alcun sizing di cluster (compute serverless,
  [[ACT_9007]]) → nessun riferimento di sizing è ereditabile dai job verso il warehouse, che va tarato a sé.
- Leve tipiche da tarare sul warehouse (da verificare in cloud): **cluster size** (2X-Small…), **scaling** min/max
  cluster per la concorrenza MSTR, **auto-suspend** (minuti di inattività), abilitazione **serverless/Photon**,
  result cache. Precondizione dati: `sql/optimize/gold_optimize_tables.sql` (OPTIMIZE + ZORDER + ANALYZE) eseguito
  sulle tabelle sotto le viste `kpi_*` (già pronto — ACT_7.2.2).
- Riferimento operativo checklist "cosa NON portare dal locale": `14_release_kit.md` §3.G (cfr. ADR-0015 §Riferimenti).

## Sviluppo (diario)
- 2026-07-03 · avanzamento 20%: linee guida definite; tuning effettivo bloccato su cloud.

## Verifica
- Misura tempi query delle viste KPI / carico MicroStrategy con la size scelta (baseline vs size incrementata).
- Verifica che l'auto-suspend scatti dopo la soglia di inattività impostata (controllo stato warehouse).
- Trade-off costo/latenza documentato; target freschezza reporting entro le 06:00 (cfr. `02_pipeline_mapping.md`).

## Esito
— (richiede cloud)

## Follow-up
Nessuna al momento.
