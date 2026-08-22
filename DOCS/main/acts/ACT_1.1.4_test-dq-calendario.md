# ACT_1.1.4 · Test DQ Calendario

**Status**: done   **Type**: dq   **Origin**: sprint 1.1
**Sprint**: 1.1 — Dimensione Calendario & Strutture Merceologiche   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
`DIM_CALENDARIO` (ACT_1.1.1) è dimensione fondante e va protetta da regressioni su range date,
ISO week, trimestri e festività italiane.

## Obiettivo
Suite di test DQ sulla dimensione calendario, verde.

## Esito
15 test pytest verdi su range 2018–2030, ISO week, trimestre e festività IT.
