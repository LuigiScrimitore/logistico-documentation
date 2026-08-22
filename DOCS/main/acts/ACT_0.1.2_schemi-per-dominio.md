# ACT_0.1.2 · Schemi Unity Catalog per dominio logistico

**Status**: in-progress
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 1   **Blocco**: 🏗️ infra (utenza Azure per `terraform apply`)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: ACT_0.1.1 (catalog referenziati)   **Blocca**: tutti i notebook (bronze/silver/gold)
**ADR collegate**: ADR-0001 (config_dev D1), ADR-0002 (bronze.condiviso D2)   **OP collegati**: —

## Contesto e motivazione
L'area logistica è isolata a livello di **schema** (non di catalog, ADR-0004). Vanno creati gli schemi
che ospitano tabelle e viste dei tre layer + condiviso + controllo. Senza schemi, nessuna tabella può
essere scritta.

## Obiettivo
Creati gli schemi: `bronze.logistica`, `bronze.condiviso` (D2), `silver.logistica`,
`silver.logistica_curated`, `gold.logistica`, `gold.logistica_dm`, `config.logistica_etl` (D1).

## Analisi tecnica
- File: `infra/terraform/brownfield/main.tf` (risorse `databricks_schema`).
- **Rename 2026-07-03**: ex `silver.prep_logistica` → **`silver.logistica_curated`** (allineato al naming
  usato dai notebook curated, ADR-0007).
- Dipende dai catalog di ACT_0.1.1.

## Sviluppo (diario)
- 2026-07-03 · rename `prep_logistica`→`logistica_curated` recepito; codice pronto.

## Verifica
`terraform apply` crea i 7 schemi; un `SHOW SCHEMAS` nei rispettivi catalog li elenca; un notebook di
prova crea/dropa una tabella dummy in `bronze.logistica`.

## Esito
— (in attesa accesso Azure)

## Follow-up
Grants sugli schemi → ACT_0.1.7.
