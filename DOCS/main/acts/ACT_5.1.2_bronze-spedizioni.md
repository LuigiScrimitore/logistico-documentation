# ACT_5.1.2 · bronze_spedizioni (via landing, DELTA_MERGE)

**Status**: done   **Type**: feature   **Origin**: sprint 5.1
**Sprint**: 5.1 — Bronze Trasporti   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0010 (incrementale)   **OP collegati**: OP-26

## Contesto
SPEDIZIONI@TRACK è la sorgente di F_TRASPORTO e arriva via landing (OP-26), non JDBC. Serviva il notebook Bronze relativo. Vedi sprint 5.1.

## Obiettivo
Ingestion Bronze di `spedizioni` da landing con strategia DELTA_MERGE.

## Esito
`bronze_spedizioni` consegnato (lettura da landing, DELTA_MERGE incrementale).
