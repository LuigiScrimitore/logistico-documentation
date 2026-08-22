# ACT_6.1.4 · Gold `gold_f_tracciabilita_lotti` (QTA_RESIDUA, MERGE)

**Status**: done   **Type**: feature   **Origin**: sprint 6.1
**Sprint**: 6.1   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0008 (chiavi naturali Gold), ADR-0010 (incrementale)   **OP collegati**: —

## Contesto
Il fact di tracciabilità lotti CE178 chiude la catena silver→gold di Wave E, con quantità
residua per lotto e scrittura incrementale MERGE (Sprint 6.1).

## Obiettivo
Gold `gold_f_tracciabilita_lotti` con `QTA_RESIDUA` e upsert via MERGE.

## Esito
`gold_f_tracciabilita_lotti` consegnato con `QTA_RESIDUA` e MERGE incrementale; base della vista
conformità CE178 (ACT_6.1.5).
