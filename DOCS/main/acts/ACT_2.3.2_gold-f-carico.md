# ACT_2.3.2 · gold_f_carico (join silver, lookup dim, fallback)

**Status**: done   **Type**: feature   **Origin**: sprint 2.3
**Sprint**: 2.3   **Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0006 (grain etichetta+peso anagrafica), ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Costruzione del fact Gold F_CARICO a grain etichetta, con join sui Silver Carichi, lookup dimensioni e fallback per orphan. Rif. analisi ACT_2.3.1.

## Obiettivo
Notebook `gold_f_carico` con 0% orphan in locale, chiavi naturali validate.

## Esito
Consegnato `gold_f_carico`: 0.0% orphan in locale; CORRIERE_COD rimosso. PES_CARICO da anagrafica articolo (non da pesata). Testato in locale.
