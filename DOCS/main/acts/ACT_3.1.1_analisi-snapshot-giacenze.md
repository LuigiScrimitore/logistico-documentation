# ACT_3.1.1 · Analisi snapshot giacenze (CATENA/ESTERNI, T_STOCK, STRUTTURA_MAG)

**Status**: done   **Type**: analysis   **Origin**: sprint 3.1
**Sprint**: 3.1 — Bronze Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Prima di scrivere i bronze giacenze serviva capire natura e grain delle sorgenti snapshot
(CATENA, CATENA_ESTERNI, T_STOCK, STRUTTURA_MAG) e la logica di unione. Vedi sprint 3.1.

## Obiettivo
Definire modello e strategia di caricamento delle sorgenti giacenze.

## Esito
Analisi consegnata: `WL2_CATENA = CATENA UNION ESTERNI`; snapshot da caricare con dynamic
partition overwrite per giorno. Base per 3.1.2–3.1.4.
