# ACT_4.5.1 · Operatori non in DIM_OPERATORE (sentinel ND/−1)

**Status**: done   **Type**: feature   **Origin**: sprint 4.5
**Sprint**: 4.5   **Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold), ADR-0011 (LAD via _COD_NAT)   **OP collegati**: —

## Contesto
Gestione edge case: operatori presenti nei fatti ma assenti in `DIM_OPERATORE` → sentinel ND/−1
(surrogate_key_fallback). Vedi sprint [`../sprint_agile/sprint_4.5.md`](../sprint_agile/sprint_4.5.md).

## Obiettivo
Operatori orfani mappati a sentinel senza scarto del fatto.

## Esito
Sentinel ND/−1 (`surrogate_key_fallback`) implementato per operatori non in DIM_OPERATORE.
