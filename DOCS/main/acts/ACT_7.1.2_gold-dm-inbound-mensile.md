# ACT_7.1.2 · DataMart `gold_dm_inbound_mensile`

**Status**: done   **Type**: feature   **Origin**: sprint 7.1
**Sprint**: 7.1 — Aggregati Mensili DataMart   **Fase / Wave**: FASE 7 — KPI Aggregati & Reporting   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Primo dei quattro DataMart mensili della FASE 7: aggregazione inbound (peso/QTA, lead time). Deriva dall'analisi degli aggregati Oracle `A_*` (vedi ACT_7.1.1).

## Obiettivo
DataMart mensile inbound in `gold.logistica_dm` con peso/QTA e P90 lead_time.

## Esito
`gold_dm_inbound_mensile` consegnato in `gold.logistica_dm` (metriche peso/QTA, P90 lead_time). Parte dello sprint 7.1 chiuso al 100% (offline).
