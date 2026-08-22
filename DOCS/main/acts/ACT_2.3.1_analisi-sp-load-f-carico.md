# ACT_2.3.1 · Analisi SP_LOAD_F_CARICO (grain, misure, join)

**Status**: done   **Type**: analysis   **Origin**: sprint 2.3
**Sprint**: 2.3   **Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0006 (grain F_CARICO=etichetta+peso anagrafica)   **OP collegati**: —

## Contesto
Prima del Gold F_CARICO serviva analizzare la stored procedure Oracle SP_LOAD_F_CARICO per determinare grain, misure e join. L'analisi ha portato a rivedere il grain a **etichetta** (catena WL_CARICO) con PES_CARICO da anagrafica articolo.

## Obiettivo
Documentare grain, misure e join di SP_LOAD_F_CARICO come base per `gold_f_carico`.

## Esito
Analisi completata; grain definito a livello etichetta e sorgenti misure identificate (ADR-0006). Abilita ACT_2.3.2.
