# ACT_0.3.4 · Template Bronze (CSV landing → Delta MERGE)

**Status**: done   **Type**: feature   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0010 (incrementale watermark/pattern#2/pruning)   **OP collegati**: —

## Contesto
Serviva un notebook template standard per l'ingestion Bronze dai CSV in landing verso Delta, riusabile su tutte le tabelle bronze.

## Obiettivo
Definire il template Bronze: CSV landing → Delta con MERGE.

## Esito
Template Bronze con **schema-on-read per header** (mai `.schema()` posizionale sui CSV) e pruning su `row_hash`. Coerente con ADR-0010 (incrementale).
