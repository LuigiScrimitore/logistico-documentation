# ACT_0.1.1 · Cataloghi Unity Catalog (solo DEV, referenziati)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 1   **Blocco**: 🏗️ infra (utenza Azure per `terraform apply`)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: —   **Blocca**: ACT_0.1.2 (schemi)
**ADR collegate**: ADR-0001 (config_dev D1), ADR-0004 (naming ambienti D4)   **OP collegati**: —

## Contesto e motivazione
L'overlay brownfield **non crea** i catalog (esistono già nel DWH aziendale): li **referenzia**. Serve
agganciare i catalog `bronze_dev`, `silver_dev`, `gold_dev`, `config_dev` (D1), `landing_dev` per poterci
creare sopra gli schemi logistici (ACT_0.1.2). Referenziare invece di creare evita conflitti sulla
piattaforma condivisa e rende `terraform plan` un fail-safe (fallisce se un catalog manca).

## Obiettivo
`terraform plan` risolve tutti i catalog DWH via `data "databricks_catalog"` senza crearli; fallisce in
modo esplicito se un catalog atteso non esiste. PROD/`_stage` non configurati ora (D4).

## Analisi tecnica
- File: `infra/terraform/brownfield/main.tf` — blocchi `data "databricks_catalog"` per i 5 catalog DEV.
- Nomi risolti dalla convenzione `<layer>_dev` (ADR-0004). Nessuna creazione catalog.

## Sviluppo (diario)
- 2026-07-03 · codice pronto; esecuzione bloccata su utenza Azure.

## Verifica
`terraform init && terraform plan` completa senza creare catalog e senza errori di risoluzione.

## Esito
— (in attesa accesso Azure)

## Follow-up
Configurare `_prod` alla fase di go-live PROD (nuova ACT).
