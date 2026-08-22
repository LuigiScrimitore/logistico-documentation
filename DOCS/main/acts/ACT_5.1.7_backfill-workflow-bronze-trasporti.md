# ACT_5.1.7 · Backfill + Workflow Bronze Trasporti (05:00)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 5.1
**Sprint**: 5.1 — Bronze Trasporti
**Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (deploy workflow + esecuzione backfill)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_5.1.2, ACT_5.1.3, ACT_5.1.4, ACT_5.1.5, ACT_5.1.6   **Blocca**: run schedulato Bronze Trasporti
**ADR collegate**: ADR-0009 (job cluster serverless), ADR-0010 (incrementale)   **OP collegati**: OP-26

## Contesto e motivazione
I notebook Bronze Trasporti (5.1.2-5.1.6) sono pronti ma vanno orchestrati in un workflow schedulato e serve il backfill storico. Senza cloud, script e YML restano non eseguibili. Vedi [`../sprint_agile/sprint_5.1.md`](../sprint_agile/sprint_5.1.md) (5.1.7: "script+YML pronti; richiede cloud", PARZ. 20%).

I notebook Bronze presenti oggi sotto `notebooks/bronze/trasporti/`:
- `bronze_spedizioni.py` (5.1.2 — SPEDIZIONI@TRACK via **landing**, DELTA_MERGE null-safe)
- `bronze_trasporti.py` (5.1.3 — `t_trasp_mtv`, CND/STAT)
- `bronze_vettori.py` / `bronze_vettori_track.py` / `bronze_vettori_locale.py` (5.1.5 — anagrafica vettori)
- `bronze_automezzi.py` (5.1.6)
- `bronze_swap.py` (bolle con movimentazioni multiple)

⚠️ **Chiarimento OP-26** (vedi [`../milestones/fase_5.md`](../milestones/fase_5.md) §6): F_TRASPORTO e i suoi Bronze provengono da **SPEDIZIONI@TRACK via landing**, **non** via JDBC diretto. Nel workflow trasporti a regime (`logistica_trasporti.yml`, header) i **4 Bronze JDBC residui sono ESCLUSI dallo scheduling** fino a migrazione: il backfill/scheduling qui riguarda i Bronze alimentati da landing.

## Obiettivo
Workflow Bronze Trasporti schedulato (05:00) attivo su cloud e backfill storico completato. Fatto = job gira su serverless e le tabelle bronze (`bronze.spedizioni`, `bronze.t_trasp_mtv`, `bronze.vettori`, `bronze.automezzi`, `bronze.swap`) contengono lo storico e il run incrementale successivo non duplica.

## Analisi tecnica
- **Orchestrazione**: bundle **DAB** su compute **serverless** ([[adr/0009_job_cluster_serverless]]); dal
  [[ACT_9007]] i workflow non dichiarano `job_clusters` e il wheel `logistica_utils` viaggia nel blocco
  job-level `environments` (`environment_key: default`). NB: al momento nel repo **non esiste** un `workflows/logistica_bronze_trasporti.yml` dedicato; l'ingestion dei Bronze trasporti da landing è coperta da `workflows/logistica_landing_ingestion.yml` (a monte) e i Silver/Gold da `workflows/logistica_trasporti.yml` (05:00, [[ACT_5.4.4_workflow-logistica-trasporti]]). **Da verificare** se il Bronze trasporti va aggiunto come task esplicito o resta dentro landing_ingestion.
- **Backfill**: rerun dei notebook Bronze sullo storico landing. La landing parte dal **2026-06-09** (vedi 07 §P-03) → il backfill copre solo la finestra disponibile. **Da verificare**: non è presente uno script `backfill` dedicato sotto `scripts/`; il pattern è rerun notebook per finestra date.
- **Ingestion incrementale a regime**: [[adr/0010_incrementale_watermark_pattern2_pruning]] — watermark + pattern #2 + pruning `_row_hash`; DELTA_MERGE null-safe + dedup chiave (coerente con memoria `bronze-csv-schema-by-name`: mai `.schema()` posizionale su CSV, MERGE null-safe).

## Sviluppo (diario)
- 2026-07-03 · script + YML pronti; PARZIALE ~20%; esecuzione bloccata su accesso cloud.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Job schedulato eseguito con esito OK su serverless.
- Tabelle bronze trasporti popolate con lo storico landing disponibile (dal 2026-06-09).
- Idempotenza: un secondo run sullo stesso `run_date` non duplica righe (MERGE su chiave, dedup).
- DQ interni verdi ([[adr/0014_dq_alerting_interni]]).

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
- Da chiarire l'orchestrazione Bronze trasporti (task dentro `logistica_landing_ingestion.yml` vs workflow dedicato) → eventuale ACT emergente 9000+.
