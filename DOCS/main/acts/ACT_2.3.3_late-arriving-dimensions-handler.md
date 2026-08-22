# ACT_2.3.3 · Late-Arriving Dimensions handler

**Status**: done   **Type**: feature   **Origin**: sprint 2.3
**Sprint**: 2.3   **Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0011 (LAD via _COD_NAT)   **OP collegati**: OP-32 (LAD resolver generico)

## Contesto
F_CARICO poteva referenziare dimensioni non ancora presenti (late-arriving). Serviva un handler generico per gestire le LAD via chiave naturale `_COD_NAT`. Rif. ACT_2.3.2.

## Obiettivo
Handler `gold_late_arriving_handler` che risolve le dimensioni late-arriving.

## Esito
Consegnato `gold_late_arriving_handler` (LAD resolver generico, ADR-0011/OP-32). Testato in locale.
