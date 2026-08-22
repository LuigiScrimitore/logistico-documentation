# ACT_0.3.3 · Decision matrix ingestion per tabella

**Status**: done   **Type**: analysis   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0005 (no segreti Oracle/export su landing), ADR-0010 (incrementale watermark)   **OP collegati**: —

## Contesto
Dopo la revisione architetturale (ingestion via landing CSV push, non JDBC — vedi ACT_0.3.1), serviva formalizzare per ogni tabella la strategia di ingestion.

## Obiettivo
Produrre la decision matrix di ingestion per tabella.

## Esito
`DOCS/decision_matrix_ingestion.md` v2.0.
