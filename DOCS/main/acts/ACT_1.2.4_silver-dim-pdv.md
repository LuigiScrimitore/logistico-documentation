# ACT_1.2.4 · Silver DIM_PDV

**Status**: done   **Type**: feature   **Origin**: sprint 1.2
**Sprint**: 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Silver punti vendita normalizza le anagrafiche Bronze (ACT_1.2.1) a DIM, base per la Gold DIM_PDV
(ACT_1.2.6).

## Obiettivo
`DIM_PDV` Silver (dedup, SCD1) su `silver.logistica`.

## Esito
Silver `DIM_PDV` consegnata (stesso pattern dedup/SCD1 di ACT_1.2.2).
