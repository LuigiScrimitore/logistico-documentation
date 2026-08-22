# ACT_0.2.4 · Pipeline GitLab CI — gate PROD (manual approval)

**Status**: done   **Type**: infra   **Origin**: sprint 0.2
**Sprint**: 0.2 — GitLab CI/CD & Databricks Asset Bundles   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-10
**Gg (stima)**: 1
**ADR collegate**: ADR-0017 (go-live a fasi)   **OP collegati**: —

## Contesto
Il rilascio in produzione deve essere presidiato da un'approvazione manuale, coerente con la strategia di go-live a fasi (ADR-0017).

## Obiettivo
Definire il gate PROD nella pipeline GitLab CI con approvazione manuale.

## Esito
Gate manuale sul merge a `main` configurato nella pipeline CI/CD.
