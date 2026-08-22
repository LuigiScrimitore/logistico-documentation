# ACT_3.3.3 · gold_dm_giacenze_monthly

**Status**: done   **Type**: feature   **Origin**: sprint 3.3
**Sprint**: 3.3 — Gold F_GIACENZE   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Datamart mensile aggregato delle giacenze a partire dal fatto giornaliero (ACT_3.3.2). Vedi sprint 3.3.

## Obiettivo
Datamart `gold_dm_giacenze_monthly` (schema `gold.logistica_dm`).

## Esito
Consegnato in `gold.logistica_dm`. Aggrega `gold_f_giacenze_daily` su base mensile.
