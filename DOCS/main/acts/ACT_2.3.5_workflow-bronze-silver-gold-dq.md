# ACT_2.3.5 · Aggiornamento workflow Bronze→Silver→Gold→DQ

**Status**: in-progress
**Type**: infra
**Origin**: sprint 2.3
**Sprint**: 2.3
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD — deploy workflow su Databricks pendente
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.2.7, ACT_2.3.2, ACT_2.3.3   **Blocca**: —
**ADR collegate**: ADR-0009 (job cluster serverless), ADR-0014 (DQ interni)   **OP collegati**: —

## Contesto e motivazione
Il workflow `logistica_carichi` va completato con i task Gold e DQ, per orchestrare l'intera catena Bronze→Silver→Gold→DQ sui 22 siti. Definizione presente in `workflows/logistica_carichi.yml` (v3.0.0); deploy cloud pendente. Supera [[ACT_2.1.7]] e [[ACT_2.2.7]] come versione end-to-end.

## Obiettivo
Workflow completo Bronze→Silver→Gold→DQ deployato ed eseguibile. Fatto = run end-to-end verde su Databricks con gate DQ.

## Analisi tecnica
- **Task Gold in `workflows/logistica_carichi.yml`**:
  - `gold_f_carico` → `notebooks/gold/carichi/gold_f_carico` — `depends_on: silver_carico_testata, silver_carico_dettaglio, silver_pesata` — params `env`, `run_date`, `retail_master_schema` — `retries 2`, `7200s`. Legge SOLO `silver.logistica_curated.carico` (standard 2-notebook, [[ADR-0007]]); grain **etichetta** ([[ADR-0006]]); replaceWhere su ANNO_MESE. Target `gold_dev.logistica.F_CARICO`.
  - `gold_late_arriving` → `gold_late_arriving_handler` — `depends_on: gold_f_carico` — `lookback_days: 90`, `retries 1`, `3600s`. Riprocessa ANNO_MESE passati nella finestra (gestisce gap "solo in ODI" da timing, cfr. `fase_2.md` OP-CAR-5). **Nota**: l'handler oggi legge i Silver clean invece di `silver_prep_carico` e ha select disallineata dal fact principale — da rifattorizzare (vedi `07_certifica_gold_vs_cdtdw.md`, nota "divergenza gold_late_arriving_handler").
  - `gold_f_tracciabilita_lotti` → `notebooks/gold/tracciabilita/gold_f_tracciabilita_lotti` — `depends_on: silver_tracciabilita_lotto` — replaceWhere ANNO_MESE.
- **DQ**: [[ADR-0014]] (DQ & alerting interni). La DQ è implementata nella libreria `lib/logistica_utils/dq_monitor.py` (+ `dq_helper.py`, `acceptance.py`) — **il YML v3.0.0 corrente NON contiene ancora un task DQ standalone** in coda alla chain: va aggiunto (es. task `dq_carichi` con `depends_on: gold_f_carico, gold_f_tracciabilita_lotti`, gate on-failure). **Da verificare** il notebook/entrypoint DQ da schedulare (release kit KIT-03/04).
- **Compute**: `carichi_cluster`; [[ADR-0009]] serverless da allineare. Deploy via DAB (`databricks bundle deploy -t dev`), non offline.

## Sviluppo (diario)
- 2026-07-03 · task Gold+DQ aggiunti; avanzamento ~90%; deploy cloud pendente.

## Verifica
- `databricks bundle run logistica_carichi` → run end-to-end verde Bronze→Silver→Gold→(DQ) su Databricks.
- `gold_dev.logistica.F_CARICO` popolato per il `run_date`; orphan rate 0.0% (obiettivo sprint 2.3).
- Gate DQ attivo: violazioni oltre soglia fanno fallire il task DQ e triggerano l'alert on_failure ([[ADR-0014]]).

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
Nessuna al momento.
