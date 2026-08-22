# ACT_3.1.3 · bronze_t_stock (CND/STAT, MERGE)

**Status**: done   **Type**: feature   **Origin**: sprint 3.1
**Sprint**: 3.1 — Bronze Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0010 (incrementale)   **OP collegati**: —

## Contesto
Bronze della sorgente T_STOCK (attributi CND/STAT) per l'area giacenze. Vedi sprint 3.1.

## Obiettivo
Notebook `bronze_t_stock` con caricamento incrementale.

## Esito
Consegnato `bronze_t_stock` in modalità **MERGE** (CND/STAT). Alimenta `silver_t_stock` (ACT_3.2.4).
