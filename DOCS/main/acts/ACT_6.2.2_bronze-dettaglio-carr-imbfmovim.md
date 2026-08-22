# ACT_6.2.2 · Bronze `bronze_dettaglio_carr` + `bronze_imbfmovim`

**Status**: done   **Type**: feature   **Origin**: sprint 6.2
**Sprint**: 6.2   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-15

## Contesto
Il layer silver carrellisti necessita dei bronze delle sorgenti analizzate in ACT_6.2.1
(Sprint 6.2).

## Obiettivo
Bronze `bronze_dettaglio_carr` e `bronze_imbfmovim` disponibili per il silver carrellisti.

## Esito
Bronze `bronze_dettaglio_carr` e `bronze_imbfmovim` consegnati; OP-15 risolto (unione degli
operatori in `dim_operatore`). Sbloccano `silver_missione_carrellista` (ACT_6.2.3).
