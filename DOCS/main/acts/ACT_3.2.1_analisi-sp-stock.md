# ACT_3.2.1 · Analisi SP_STOCK_* (normalizzazione UM, dedup)

**Status**: done   **Type**: analysis   **Origin**: sprint 3.2
**Sprint**: 3.2 — Silver Giacenze   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Prima del silver giacenze serviva ricostruire la logica delle stored procedure Oracle SP_STOCK_*
(normalizzazione unità di misura e deduplica). Vedi sprint 3.2.

## Obiettivo
Definire regole di normalizzazione UM e strategia di dedup per il silver giacenze.

## Esito
Analisi consegnata: dedup **per chiave logica con precedenza** (non su tupla intera). Base per
ACT_3.2.2 e ACT_3.2.4.
