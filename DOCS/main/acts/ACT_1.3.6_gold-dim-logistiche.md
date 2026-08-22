# ACT_1.3.6 · Gold DIM_SITO/OPERATORE/CORRIERE/TOPOGRAFIA

**Status**: done   **Type**: feature   **Origin**: sprint 1.3
**Sprint**: 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)   **Fase / Wave**: FASE 1 — Master Data & Dimensioni   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Le Gold logistiche promuovono le Silver DIM (ACT_1.3.2–1.3.5) con chiavi naturali validate (ADR-0008)
e gestione dei valori mancanti.

## Obiettivo
`DIM_SITO`, `DIM_OPERATORE`, `DIM_CORRIERE`, `DIM_TOPOGRAFIA` Gold consegnate.

## Esito
Le quattro Gold DIM logistiche consegnate, con `surrogate_key_fallback` null="ND" per i non mappati
(chiavi naturali ADR-0008).
