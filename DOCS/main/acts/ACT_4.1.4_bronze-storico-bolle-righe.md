# ACT_4.1.4 · bronze_storico_bolle_righe (MERGE null-safe)

**Status**: done   **Type**: feature   **Origin**: sprint 4.1
**Sprint**: 4.1   **Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-30

## Contesto
Ingestion Bronze delle righe delle bolle. La chiave `BOL_NRO_RIGA` può essere null → il MERGE deve
usare confronto null-safe `<=>`. Vedi sprint [`../sprint_agile/sprint_4.1.md`](../sprint_agile/sprint_4.1.md).

## Obiettivo
Notebook `bronze_storico_bolle_righe` con MERGE null-safe sulla chiave.

## Esito
`bronze_storico_bolle_righe` consegnato con MERGE null-safe (`<=>`) su `BOL_NRO_RIGA`.
