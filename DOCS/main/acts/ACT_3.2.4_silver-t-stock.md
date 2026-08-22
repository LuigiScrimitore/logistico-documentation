# ACT_3.2.4 · silver_t_stock (join catena ↔ struttura_mag)

**Status**: done   **Type**: feature   **Origin**: sprint 3.2
**Sprint**: 3.2 — Silver Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-29 (ordering fisiologico locale)

## Contesto
Silver di dettaglio stock che unisce catena unificata (ACT_3.2.2) e struttura magazzino clean
(ACT_3.2.3). Vedi sprint 3.2.

## Obiettivo
Notebook `silver_t_stock` con join catena ↔ struttura_mag.

## Esito
Consegnato. OP-29 (ordering fisiologico osservato in locale) confermato **OK sul DAG Databricks**.
Alimenta il Gold `gold_f_giacenze_daily` (ACT_3.3.2).
