# ACT_1.1.2 · DIM_MESE/TRIMESTRE/ANNO (attributi calendario)

**Status**: done   **Type**: feature   **Origin**: sprint 1.1
**Sprint**: 1.1 — Dimensione Calendario & Strutture Merceologiche   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Le aggregazioni per mese/trimestre/anno servono al reporting sopra i fact. Anziché dimensioni
separate, gli attributi sono stati inclusi direttamente in `DIM_CALENDARIO` (vedi ACT_1.1.1).

## Obiettivo
Attributi mese/trimestre/anno disponibili sulla dimensione calendario.

## Esito
Attributi mese/trimestre/anno inclusi in `dim_calendario`. Nessun artefatto separato.
