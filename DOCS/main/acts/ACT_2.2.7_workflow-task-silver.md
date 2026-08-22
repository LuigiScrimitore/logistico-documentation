# ACT_2.2.7 · Aggiornamento workflow con task Silver

**Status**: in-progress
**Type**: infra
**Origin**: sprint 2.2
**Sprint**: 2.2
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD — deploy workflow su Databricks pendente
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.1.7, ACT_2.2.2, ACT_2.2.3, ACT_2.2.4, ACT_2.2.5   **Blocca**: —
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
Il workflow `logistica_carichi` ([[ACT_2.1.7]]) va esteso con i task Silver, per orchestrare Bronze→Silver. I notebook Silver Carichi sono completi e testati in locale (sprint 2.2 al 100%, suite DQ 15 test; OP-12 risolto — art_radice/variante derivati in Silver per troncamento). Definizione già presente in `workflows/logistica_carichi.yml`; deploy cloud pendente.

## Obiettivo
Workflow aggiornato con i task Silver, deployato ed eseguibile. Fatto = catena Bronze→Silver verde su Databricks. La versione completa Bronze→Silver→Gold è in [[ACT_2.3.5]].

## Analisi tecnica
- **Task Silver in `workflows/logistica_carichi.yml`** (anchor `&silver_params` = `env`, `run_date`; ogni Silver filtra `_bronze_load_date = run_date`):
  - `silver_carico_testata` → `silver_carichi_testate` — `depends_on: bronze_sto_tes_carichi` — `retries 2`, `7200s` — clean/dedup/MERGE, `julian_to_date`, `normalize_sito` → `silver_dev.logistica.carico_testata`
  - `silver_carico_dettaglio` → `silver_carichi_dettagli` — `depends_on: bronze_sto_righe_carico` — normalizzazione articolo radice/variante (OP-12) → `silver_dev.logistica.carico_dettaglio`
  - `silver_pesata` → `silver_pesate` — `depends_on: bronze_pesate` — DQ flag peso negativo → `silver_dev.logistica.pesata`
  - `silver_traccia_ce178` → `silver_traccia_ce178` — `depends_on: bronze_tracciace178` — dedup, parsing lotto/scadenza
  - `silver_tracciabilita_lotto` → `silver/tracciabilita/silver_tracciabilita_lotto` — `depends_on: silver_traccia_ce178` — aggregato CE178 per SITO+CARICO+DATA+COD_MSI, MERGE
- **Nota grain/curated**: `silver_prep_carico` (JOIN `carico_testata ⋈ carico_dettaglio ⋈ pesata`, calcolo `SCARTO_QTA`, OVERWRITE dinamico per ANNO_MESE) produce `silver_dev.logistica_curated.carico`, sorgente unica del Gold. Nel YML corrente questo step non è un task Silver esplicito ma è **incorporato a monte di `gold_f_carico`** (i cui `depends_on` sono i 3 Silver testata/dettaglio/pesata) — **da verificare** se serve un task dedicato `silver_prep_carico` nella chain. La pesata è in **INNER JOIN** (OP-CAR-5 confermato fedele al legacy `V_CARICO_ORDINARIO`).
- **Compute**: `carichi_cluster` come i task Bronze; [[ADR-0009]] (serverless) da allineare al deploy.
- Deploy via DAB (`databricks bundle deploy -t dev`), non eseguibile offline.

## Sviluppo (diario)
- 2026-07-03 · task Silver aggiunti al workflow; avanzamento ~90%; deploy cloud pendente.

## Verifica
- `databricks bundle run logistica_carichi` → catena Bronze→Silver verde; ogni `silver_*` verde dopo il rispettivo `bronze_*`.
- Tabelle `silver_dev.logistica.carico_testata / carico_dettaglio / pesata` popolate per il `run_date`; suite DQ Silver (sprint 2.2.6) senza violazioni.

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
Nessuna al momento.
