# ACT_5.2.2 · silver_prep_trasporto (LEAD_TIME, fill-down vettore)

**Status**: done   **Type**: feature   **Origin**: sprint 5.2
**Sprint**: 5.2 — Silver Trasporti   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Serviva il Silver di preparazione trasporto con calcolo LEAD_TIME e riempimento del vettore mancante. Vedi sprint 5.2.

## Obiettivo
`silver_prep_trasporto` con LEAD_TIME e fill-down del vettore.

## Esito
Consegnato. Fill-down vettore con `first_value(ignore_nulls)` (no MAX arbitrario). Target `logistica_curated`.
