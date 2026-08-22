# ACT_7.2.2 · Ottimizzazione Gold (OPTIMIZE + ZORDER + ANALYZE)

**Status**: done   **Type**: infra   **Origin**: sprint 7.2
**Sprint**: 7.2 — MicroStrategy & Ottimizzazione Query   **Fase / Wave**: FASE 7 — KPI Aggregati & Reporting   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Le tabelle Gold interrogate da MicroStrategy/KPI necessitavano ottimizzazione query (compattazione file e clustering) per prestazioni accettabili sul reporting.

## Obiettivo
Script di ottimizzazione Gold con OPTIMIZE + ZORDER + ANALYZE.

## Esito
Consegnato `sql/optimize/gold_optimize_tables.sql` (OPTIMIZE + ZORDER + ANALYZE sulle tabelle Gold). Attività chiusa offline; esecuzione periodica in cloud da schedulare.
