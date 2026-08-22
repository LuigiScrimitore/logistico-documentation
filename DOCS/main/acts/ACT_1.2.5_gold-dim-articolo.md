# ACT_1.2.5 · Gold DIM_ARTICOLO (JOIN merceologica 5 livelli, SCD1)

**Status**: done   **Type**: feature   **Origin**: sprint 1.2
**Sprint**: 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: OP-02

## Contesto
La Gold articolo arricchisce la Silver DIM_ARTICOLO (ACT_1.2.2) con la struttura merceologica a 5
livelli (ACT_1.1.3) e chiavi naturali validate (ADR-0008).

## Obiettivo
`DIM_ARTICOLO` Gold con JOIN merceologica 5 livelli e SCD1.

## Esito
Gold `DIM_ARTICOLO` consegnata: JOIN struttura merceologica 5 livelli, SCD1, chiavi naturali (ADR-0008).
Lookup anagrafiche master Retail opzionale/commentata (OP-02 — aggancio ancora aperto).
