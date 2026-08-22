# ACT_4.2.3 · silver_storico_bolle_clean

**Status**: done   **Type**: feature   **Origin**: sprint 4.2
**Sprint**: 4.2   **Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0010 (incrementale)   **OP collegati**: —

## Contesto
Pulizia Silver dello storico bolle. `BOL_NRO_RIGA` esclusa dai controlli not_null (può essere null).
Vedi sprint [`../sprint_agile/sprint_4.2.md`](../sprint_agile/sprint_4.2.md).

## Obiettivo
Notebook `silver_storico_bolle_clean` idempotente.

## Esito
`silver_storico_bolle_clean` consegnato; `BOL_NRO_RIGA` esclusa da not_null.
