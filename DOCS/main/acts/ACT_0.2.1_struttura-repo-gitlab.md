# ACT_0.2.1 · Struttura repository GitLab

**Status**: done   **Type**: infra   **Origin**: sprint 0.2
**Sprint**: 0.2 — GitLab CI/CD & Databricks Asset Bundles   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-10
**Gg (stima)**: 1
**ADR collegate**: ADR-0016 (GitLab multi-repo)   **OP collegati**: —

## Contesto
Il progetto Logistico 2.0 richiede un layout di repository standard su GitLab prima di poter versionare notebook, workflow e libreria. Il deploy cloud effettivo dipende dai prerequisiti dello Sprint 0.1 (subgroup GitLab, workspace).

## Obiettivo
Definire il layout dei repository con `.gitignore` e branch protection.

## Esito
Struttura repo definita con cartelle `notebooks/`, `workflows/`, `tests/`, `lib/`, `infra/terraform/`, più `.gitignore` e branch protection. Nota di adattamento cloud (ADR-0016): la struttura va riportata sui **3 repo** del subgroup `logistico` — `logistico-infrastructure` (terraform), `logistico-workflows` (notebooks+DAB), `logistico-lib` (wheel).
