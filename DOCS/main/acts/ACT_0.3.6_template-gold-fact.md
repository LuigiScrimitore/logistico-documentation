# ACT_0.3.6 · Template Gold Fact (lookup, surrogate_key_fallback)

**Status**: done   **Type**: feature   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0007 (standard 2-notebook curated/gold), ADR-0008 (chiavi naturali validate in Gold), ADR-0011 (LAD via _COD_NAT)   **OP collegati**: —

## Contesto
Serviva un template standard per i fact Gold, con gestione dei lookup dimensionali e fallback sulle chiavi.

## Obiettivo
Definire il template Gold Fact con lookup e `surrogate_key_fallback`.

## Esito
Template Gold Fact basato su **chiavi naturali validate** (ADR-0008) con controllo dell'**orphan-rate** e fallback su surrogate key.
