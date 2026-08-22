# ACT_6.1.3 · Silver `silver_tracciabilita_lotto` (flag_scaduto, gg a scadenza)

**Status**: done   **Type**: feature   **Origin**: sprint 6.1
**Sprint**: 6.1   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Serviva il layer silver della tracciabilità lotto CE178 con gli indicatori di scadenza a
supporto di gold e conformità (Sprint 6.1).

## Obiettivo
Silver `silver_tracciabilita_lotto` con `flag_scaduto` e giorni a scadenza calcolati.

## Esito
`silver_tracciabilita_lotto` consegnato con `flag_scaduto` e gg a scadenza; alimenta
`gold_f_tracciabilita_lotti` (ACT_6.1.4) e la vista conformità (ACT_6.1.5).
