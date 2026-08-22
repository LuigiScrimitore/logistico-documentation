# ACT_0.2.2 · Databricks Asset Bundles (databricks.yml dev)

**Status**: done   **Type**: infra   **Origin**: sprint 0.2
**Sprint**: 0.2 — GitLab CI/CD & Databricks Asset Bundles   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-10
**Gg (stima)**: 1
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto
Serviva un meccanismo dichiarativo per il deploy dei job Databricks per ambiente, definito offline prima dell'accesso cloud.

## Obiettivo
Configurare i Databricks Asset Bundles (`databricks.yml`) per l'ambiente dev.

## Esito
`databricks.yml` con job reference e variabili catalog/schema per ambiente. Nota di adattamento cloud: compute **serverless** (decisione 2026-07-03, vedi ADR-0009 e ACT_0.1.5).
