# ACT_5.2.1 · Analisi T_ORDINI, T_TRASP_* (join, misure)

**Status**: done   **Type**: analysis   **Origin**: sprint 5.2
**Sprint**: 5.2 — Silver Trasporti   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0013 (F_TRASPORTO grana MTV)   **OP collegati**: —

## Contesto
Prima del Silver serviva definire join e misure tra T_ORDINI e le tabelle T_TRASP_*. Vedi sprint 5.2.

## Obiettivo
Mappare join e misure delle sorgenti per i notebook Silver trasporti.

## Esito
Analisi completata; base per `silver_prep_trasporto`/`silver_prep_ordini`. Schema silver target = `logistica_curated`.
