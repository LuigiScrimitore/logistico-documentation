# ACT_0.2.5 · Libreria logistica_utils

**Status**: done   **Type**: feature   **Origin**: sprint 0.2
**Sprint**: 0.2 — GitLab CI/CD & Databricks Asset Bundles   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-10
**Gg (stima)**: 1
**ADR collegate**: ADR-0005 (no segreti su landing), ADR-0014 (DQ&alerting interni)   **OP collegati**: —

## Contesto
Serviva una libreria condivisa per centralizzare utility comuni (secret, logging, gestione Delta, data quality, storage) usate dai notebook della pipeline, packagizzata come wheel deployabile via DAB.

## Obiettivo
Realizzare la libreria `logistica_utils` con i moduli di base e relativa copertura di test.

## Esito
Libreria `logistica_utils` con 6 moduli — `secret_helper`, `logging`, `delta`, `dq`, `utils`, `storage` — e 64 test. Distribuita come wheel. Da riportare sul repo `logistico-lib` (ADR-0016).
