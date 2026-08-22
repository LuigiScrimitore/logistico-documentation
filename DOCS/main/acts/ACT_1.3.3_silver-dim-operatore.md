# ACT_1.3.3 · Silver DIM_OPERATORE (recovery legacy 3A/4A da storico_liste)

**Status**: done   **Type**: feature   **Origin**: sprint 1.3
**Sprint**: 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: OP-28

## Contesto
Gli operatori orfani sui fact venivano dal mancato recupero di codici legacy. La Silver operatore
recupera il pattern legacy 3A/4A da `storico_liste`, azzerando l'orphan rate (OP-28).

## Obiettivo
`DIM_OPERATORE` Silver con recovery legacy 3A/4A da `storico_liste`.

## Esito
Silver `DIM_OPERATORE` consegnata: recovery legacy 3A/4A da `storico_liste`, membro ND per non
mappati. Chiude OP-28 (orphan rate operatori azzerato).
