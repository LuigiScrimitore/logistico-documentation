# ACT_7.1.1 · Analisi aggregati Oracle CDT_DW (A_*)

**Status**: done   **Type**: analysis   **Origin**: sprint 7.1
**Sprint**: 7.1 — Aggregati Mensili DataMart   **Fase / Wave**: FASE 7 — KPI Aggregati & Reporting   **Closed**: 2026-07-03
**ADR collegate**: —   **OP collegati**: —

## Contesto
Prima di costruire i DataMart mensili Gold servivano da riferimento gli aggregati esistenti su Oracle CDT_DW (tabelle `A_*`), per replicarne semantica e granularità. Base per le attività 7.1.2–7.1.5.

## Obiettivo
Analizzare gli aggregati mensili Oracle `A_*` come modello sorgente per i DataMart Gold.

## Esito
Analisi completata: mappata la semantica delle tabelle `A_*` (inbound, stock, outbound, produttività) usata come specifica per `gold_dm_*`. Parte dello sprint 7.1 chiuso al 100% (offline).
