# ACT_0.3.7 · Logging & alerting standard

**Status**: done   **Type**: feature   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0014 (DQ&alerting interni)   **OP collegati**: —

## Contesto
Serviva uno standard di logging strutturato e alerting sui fallimenti per i notebook della pipeline, gestito internamente (ADR-0014).

## Obiettivo
Definire lo standard di logging (JSON) e l'alerting su failure.

## Esito
`logging_helper.py` con logging JSON strutturato ed email alert su failure via Databricks Workflows.
