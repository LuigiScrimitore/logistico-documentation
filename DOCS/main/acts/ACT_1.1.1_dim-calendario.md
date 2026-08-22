# ACT_1.1.1 · DIM_CALENDARIO (2018–2030, festività IT)

**Status**: done   **Type**: feature   **Origin**: sprint 1.1
**Sprint**: 1.1 — Dimensione Calendario & Strutture Merceologiche   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
La dimensione temporale è prerequisito per ogni fact Gold. Serve un calendario giornaliero 2018–2030
con attributi ISO e festività italiane, calcolate in PySpark (Pasqua via algoritmo di Gauss).

## Obiettivo
`DIM_CALENDARIO` giornaliera 2018–2030 con ISO week, trimestre e festività IT, generata in PySpark.

## Esito
Notebook DIM_CALENDARIO consegnato (PySpark, Pasqua con Gauss). Attributi: ISO week, trimestre,
festività italiane. Verificata con 15 test pytest verdi (vedi ACT_1.1.4).
