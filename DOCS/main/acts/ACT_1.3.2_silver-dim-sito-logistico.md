# ACT_1.3.2 · Silver DIM_SITO_LOGISTICO (normalize_sito + alias da TABGEN)

**Status**: done   **Type**: feature   **Origin**: sprint 1.3
**Sprint**: 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
La Silver sito normalizza i siti da Bronze `TABGEN` (ACT_1.3.1) in una DIM, base per la Gold
DIM_SITO (ACT_1.3.6). Il mapping sito è critico per le quadrature fact.

## Obiettivo
`DIM_SITO_LOGISTICO` Silver con normalizzazione e alias da `TABGEN`.

## Esito
Silver `DIM_SITO_LOGISTICO` consegnata con utility `normalize_sito()` e gestione alias da `TABGEN`.
