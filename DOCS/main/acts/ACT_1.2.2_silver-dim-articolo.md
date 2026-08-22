# ACT_1.2.2 · Silver DIM_ARTICOLO (dedup, SCD1)

**Status**: done   **Type**: feature   **Origin**: sprint 1.2
**Sprint**: 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
La Silver articolo normalizza e deduplica le anagrafiche Bronze (ACT_1.2.1) in una DIM SCD1, base per
la Gold DIM_ARTICOLO (ACT_1.2.5).

## Obiettivo
`DIM_ARTICOLO` Silver con dedup e SCD1 su `silver.logistica`.

## Esito
Silver `DIM_ARTICOLO` consegnata: dedup + SCD1 via `MERGE INTO` su `silver.logistica`.
