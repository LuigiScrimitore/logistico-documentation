# ACT_4.3.3 · silver_prep_prep_sped (join uniche⋈catena, dedup)

**Status**: done   **Type**: feature   **Origin**: sprint 4.3
**Sprint**: 4.3   **Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-33

## Contesto
Notebook di preparazione Silver che unisce liste uniche e catena unificata, con dedup. Il tiebreaker di
dedup usa `SEQ_PREL_PREP` (OP-33 da chiarire con BA). Vedi sprint
[`../sprint_agile/sprint_4.3.md`](../sprint_agile/sprint_4.3.md).

## Obiettivo
Notebook `silver_prep_prep_sped` con join uniche⋈catena e dedup.

## Esito
`silver_prep_prep_sped` consegnato (join + dedup, tiebreaker `SEQ_PREL_PREP`). Resta OP-33 da validare
con BA (vedi ACT_4.3.6 / punti aperti sprint). Schema target rinominato `logistica_curated`.
