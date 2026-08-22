# ACT_4.5.4 · Stress test idempotenza (30 gg backfill + re-run)

**Status**: proposed
**Type**: dq
**Origin**: sprint 4.5
**Sprint**: 4.5 — Edge Cases Prep Spedizioni
**Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)
**Gg (stima)**: 2
**Blocco**: 🏗️ infra — richiede PROD + storico su ADLS
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_4.4.3 (workflow prep sped)   **Blocca**: chiusura Wave C
**ADR collegate**: ADR-0010 (incrementale)   **OP collegati**: OP-35 (watermark)

## Contesto e motivazione
Verifica finale della Wave C: eseguire un backfill di 30 giorni seguito da re-run per confermare
l'idempotenza dell'intera pipeline (bronze→gold, watermark OP-35). Non avviabile offline — richiede
PROD con storico su ADLS. Sprint
[`../sprint_agile/sprint_4.5.md`](../sprint_agile/sprint_4.5.md) (4.5.4, ⏳ PENDENTE): "edge case
gestiti in codice; lo stress test richiede PROD con storico su ADLS". Dipende da [[ACT_4.4.3]]
(workflow). Vedi [[ADR-0010]] (incrementale) e OP-35 (watermark).

## Obiettivo
Backfill 30 gg + re-run senza duplicati né derive. Fatto = conteggi e misure identici tra run,
watermark coerente (avanzato senza regressioni, non ri-avanzato su re-run).

## Analisi tecnica
- **Meccanismi di idempotenza da stressare** (OP-30 🟢, [`../05_open_points.md`](../05_open_points.md)):
  1. **Bronze pruning `_row_hash`** su tutti i 14 bronze MERGE (propaga solo il delta reale, chiavi
     MERGE null-safe `<=>`); 2. **Clean incrementale** (filtro `_bronze_load_date == run_date` +
     MERGE upsert null-safe + `dropDuplicates(MERGE_KEYS)`); 3. **Pattern #2 prep chiavi-impattate**
     (`storico_liste_uniche`, `storico_bolle_uniche`, `prep_sped`: ricalcolo solo dei gruppi toccati,
     validato incrementale == full).
- **Watermark OP-35** (🟢 rollout completo): tabella `control_<env>.etl.watermark`, chiave
  `(stage, sistema, tabella, sito)`; helper `utils.py` (`ensure/read/update_watermark`,
  `pending_landing_dates`) — `update` transazionale: **su FAIL non avanza**. Test di riferimento
  [`tests/local_bronze/test_watermark.py`](../../../tests/local_bronze/test_watermark.py) (ALL_OK):
  copre avanzamento OK/FAIL, upsert (una sola riga per chiave), `pending_landing_dates` (catch-up
  range) e isolamento per-sito. Pendente W-05 `landing_to_bronze` (dipende da control catalog cloud).
- **Procedura**: backfill 30 gg su tutta la catena prep sped (loop `run_date`), poi re-run completo
  dello stesso range; confrontare conteggi/misure pre e post. Riferimento pattern offline:
  [`tests/local_bronze/rebuild_prep_sped.py`](../../../tests/local_bronze/rebuild_prep_sped.py)
  (drop bronze/clean → re-ingest CTAS giorno 1 + MERGE upsert giorno 2 = una copia → uniche/prep →
  blocco VERIFICA NO-DUP con distinct-count su chiavi) e `run_big_rerun.py` / `run_b_newday.py`.
- **Richiede** accesso PROD + storico ADLS (backfill logistix multisito + STAT).

## Sviluppo (diario)
- 2026-07-03 · pendente: richiede PROD + storico ADLS.

## Verifica
- **No-dup**: per ogni tabella clean/uniche/fact, `count == distinct(MERGE_KEYS)` dopo re-run
  (pattern `rebuild_prep_sped.py` blocco VERIFICA NO-DUP; es. `storico_liste_clean` 8 chiavi,
  `storico_bolle_clean` 4 chiavi).
- **Invarianza misure**: SUM misure Gold (`F_PREP_SPED`: QTA_PREP, VAL_PREP_CES, VAL_PREP_VEN)
  identiche tra run 1 e run 2.
- **Watermark**: valore coerente, non regredisce; su FAIL simulato non avanza (semantica
  `test_watermark.py`).

## Esito
— (pendente)

## Follow-up
- Anomalie idempotenza → eventuali ACT emergenti 9000+.
