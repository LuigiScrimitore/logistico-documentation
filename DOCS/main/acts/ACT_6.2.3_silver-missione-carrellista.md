# ACT_6.2.3 · Silver `silver_missione_carrellista` (durata, tipo)

**Status**: done   **Type**: feature   **Origin**: sprint 6.2
**Sprint**: 6.2   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Serviva il silver delle missioni carrellista con durata e tipo missione, a monte delle sessioni
e del fact F_TURNO (Sprint 6.2).

## Obiettivo
Silver `silver_missione_carrellista` con durata e tipo missione calcolati.

## Esito
`silver_missione_carrellista` consegnato (durata, tipo); alimenta
`silver_sessione_carrellista` (ACT_6.2.4) e `gold_f_movimentazione_carrellisti` (ACT_6.2.5).
