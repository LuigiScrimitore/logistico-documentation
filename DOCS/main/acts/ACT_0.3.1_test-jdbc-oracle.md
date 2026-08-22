# ACT_0.3.1 · Test connettività JDBC Oracle → Databricks

**Status**: cancelled   **Type**: analysis   **Origin**: sprint 0.3
**Sprint**: 0.3 — Connettività Sorgenti & Template Notebook   **Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali   **Closed**: 2026-07-17
**Gg (stima)**: 1
**ADR collegate**: ADR-0005 (no segreti Oracle/export su landing)   **OP collegati**: —

## Contesto
Attività prevista per verificare la connettività JDBC diretta Oracle → Databricks.

## Obiettivo
(Non applicabile — vedi Esito.)

## Esito
❌ **Non applicabile.** Revisione architetturale: l'ingestion **non** è JDBC diretto ma **landing CSV in push (SFTP)**. La strategia landing elimina secret scope Oracle, VNet e `oracledb` sul cluster (coerente con D5 / ADR-0005). Sostituita da ACT_0.3.3 (decision matrix ingestion).
