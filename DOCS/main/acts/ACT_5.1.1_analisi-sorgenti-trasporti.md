# ACT_5.1.1 · Analisi sorgenti trasporti

**Status**: done   **Type**: analysis   **Origin**: sprint 5.1
**Sprint**: 5.1 — Bronze Trasporti   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0013 (F_TRASPORTO grana MTV)   **OP collegati**: OP-26

## Contesto
Prima di costruire il Bronze Trasporti serviva mappare le sorgenti outbound (SPEDIZIONI@TRACK, T_TRASP_MTV, T_PDV, T_VETTORI) e decidere la via di alimentazione. Vedi sprint 5.1.

## Obiettivo
Mappare join e misure delle sorgenti trasporti e chiarire la provenienza di F_TRASPORTO.

## Esito
Analisi completata; risolto OP-26: F_TRASPORTO si alimenta da SPEDIZIONI@TRACK **via landing** (non JDBC). Grana MTV deliberata (ADR-0013).
