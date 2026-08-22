# ACT_3.3.2 · gold_f_giacenze_daily (replaceWhere per data_foto)

**Status**: done   **Type**: feature   **Origin**: sprint 3.3
**Sprint**: 3.3 — Gold F_GIACENZE   **Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Fatto Gold giornaliero delle giacenze, alimentato dal silver t_stock (ACT_3.2.4) secondo grain/misure
di ACT_3.3.1. Vedi sprint 3.3.

## Obiettivo
Notebook `gold_f_giacenze_daily` con scrittura idempotente per giorno.

## Esito
Consegnato con **replaceWhere per `data_foto`** (idempotenza per giorno). Popolato con ~55k righe nel
big re-run. Alimenta datamart mensile (ACT_3.3.3) e KPI (ACT_3.3.4/3.3.5).
