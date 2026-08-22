# ACT_7.2.3 · 10 SQL KPI views (chiavi naturali v2.0)

**Status**: done   **Type**: feature   **Origin**: sprint 7.2
**Sprint**: 7.2 — MicroStrategy & Ottimizzazione Query   **Fase / Wave**: FASE 7 — KPI Aggregati & Reporting   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **Doc collegati**: `13_registro_rename_gold_microstrategy.md`   **OP collegati**: —

## Contesto
Il layer di reporting (MicroStrategy) richiede viste KPI stabili sopra Gold, basate sulle chiavi naturali validate (v2.0, ADR-0008). Base per il connettore MicroStrategy (ACT_7.2.1) e la dashboard (ACT_7.2.5).

## Obiettivo
10 viste SQL KPI su Gold con chiavi naturali v2.0.

## Esito
Consegnate 10 viste KPI in `sql/kpi/kpi_*.sql` (chiavi naturali v2.0). Naming allineato al registro rename
`13_registro_rename_gold_microstrategy.md` per il consumo MicroStrategy.
