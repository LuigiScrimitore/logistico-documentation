# ACT_4.1.2 · bronze_storico_liste (DELTA_MERGE + row_hash)

**Status**: done   **Type**: feature   **Origin**: sprint 4.1
**Sprint**: 4.1   **Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-30

## Contesto
Ingestion Bronze dello storico liste di picking. La lettura CSV va fatta per header (mai `.schema()`
posizionale) — fix OP-30. Vedi sprint [`../sprint_agile/sprint_4.1.md`](../sprint_agile/sprint_4.1.md).

## Obiettivo
Notebook `bronze_storico_liste` con MERGE Delta idempotente e `row_hash`.

## Esito
`bronze_storico_liste` in DELTA_MERGE con `row_hash`; lettura CSV per header (OP-30). Consegnato.
