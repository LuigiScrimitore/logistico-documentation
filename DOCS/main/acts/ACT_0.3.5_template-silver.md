# ACT_0.3.5 · Template Silver (cleansing 1:1, MERGE upsert)

**Status**: done   **Type**: feature   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0007 (standard 2-notebook curated/gold)   **OP collegati**: —

## Contesto
Serviva un template standard per lo strato Silver di cleansing 1:1 con upsert idempotente.

## Obiettivo
Definire il template Silver: cleansing 1:1 con MERGE upsert.

## Esito
Template Silver con helper `julian_to_date`, `normalize_sito` e **MERGE null-safe**.
