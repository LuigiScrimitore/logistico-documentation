# ACT_3.1.2 · bronze_catena + bronze_catena_esterni (SNAPSHOT)

**Status**: done   **Type**: feature   **Origin**: sprint 3.1
**Sprint**: 3.1 — Bronze Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Ingestion bronze delle due sorgenti snapshot di catena giacenze. Analisi in ACT_3.1.1
(`WL2_CATENA = CATENA UNION ESTERNI`).

## Obiettivo
Notebook `bronze_catena` e `bronze_catena_esterni` che materializzano lo snapshot giornaliero.

## Esito
Consegnati entrambi i bronze in modalità SNAPSHOT con **dynamic partition overwrite per giorno**.
Alimentano `silver_catena_unificata` (ACT_3.2.2).
