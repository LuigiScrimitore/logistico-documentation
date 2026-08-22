# ACT_6.2.4 · Silver `silver_sessione_carrellista` (ORE_PRODUTTIVE)

**Status**: done   **Type**: feature   **Origin**: sprint 6.2
**Sprint**: 6.2   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: —

## Contesto
Le sessioni carrellista aggregano le missioni (ACT_6.2.3) in ore produttive, al netto delle
pause, per il fact F_TURNO e i KPI (Sprint 6.2).

## Obiettivo
Silver `silver_sessione_carrellista` con `ORE_PRODUTTIVE`.

## Esito
`silver_sessione_carrellista` consegnato; `ORE_PRODUTTIVE` = `MAX(SUM(durata)-30, 0)/60`
(sottrazione pausa 30 min, clamp a 0, conversione in ore). Alimenta `gold_f_movimentazione_carrellisti` (ACT_6.2.5).
