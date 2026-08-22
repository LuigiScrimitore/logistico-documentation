# ACT_3.2.2 · silver_catena_unificata (CATENA+ESTERNI, dedup)

**Status**: done   **Type**: feature   **Origin**: sprint 3.2
**Sprint**: 3.2 — Silver Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Unificazione delle due sorgenti bronze catena (ACT_3.1.2) secondo il pattern `WL2_CATENA =
CATENA UNION ESTERNI` con deduplica (ACT_3.2.1).

## Obiettivo
Notebook `silver_catena_unificata` con catena+esterni unificate e deduplicate.

## Esito
Consegnato. Fix chiave: **UNION per chiave logica** (non sulla tupla intera), coerente col pattern
WL2_CATENA. Alimenta `silver_t_stock` (ACT_3.2.4).
