# ACT_0.2.3 · Pipeline GitLab CI — stage DEV

**Status**: done   **Type**: infra   **Origin**: sprint 0.2
**Sprint**: 0.2 — GitLab CI/CD & Databricks Asset Bundles   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-10
**Gg (stima)**: 1
**ADR collegate**: ADR-0016 (GitLab multi-repo)   **OP collegati**: —

## Contesto
Necessaria una pipeline CI per validare e deployare automaticamente su ambiente DEV i bundle Databricks.

## Obiettivo
Configurare `.gitlab-ci.yml` con lo stage DEV (validate + deploy-dev).

## Esito
`.gitlab-ci.yml` con stage `validate`, `test`, `deploy-dev`. Nota di adattamento cloud (ADR-0016): la pipeline va adattata ai **3 repo** del subgroup `logistico` (multi-repo, non mono-repo); secret CI/CD limitati all'auth (`ARM_*` + `DATABRICKS_TOKEN`), meccanismo in definizione con Technology.
