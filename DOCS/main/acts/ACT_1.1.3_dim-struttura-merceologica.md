# ACT_1.1.3 · DIM_STRUTTURA_MERCEOLOGICA (5 livelli da CDT_DW)

**Status**: in-progress
**Type**: feature
**Origin**: sprint 1.1
**Sprint**: 1.1 — Dimensione Calendario & Strutture Merceologiche
**Fase / Wave**: FASE 1 — Master Data & Dimensioni
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (first-run cloud pendente, dipende da FASE 0)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: FASE 0 (landing/first-run cloud)   **Blocca**: ACT_1.2.5 (Gold DIM_ARTICOLO — JOIN merceologica)
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
La struttura merceologica è la gerarchia di classificazione articolo usata in JOIN dalla Gold
DIM_ARTICOLO (ACT_1.2.5). L'attività nasce con scope "5 livelli da `CDT_DW`" (titolo sprint 1.1.3),
ma l'implementazione attuale copre il **solo livello di area merceologica logistica**
(`LU_AREA_MERCL_LOGIS`): il livello superiore (macro-aggregato `LU_MACRO_AGG_MERCL`) è **rinviato a
OP-03/OP-04** (vedi commento header del notebook). I 5 livelli "master" (aggancio anagrafica Retail
su Gold DIM_ARTICOLO) sono lookup condivise estratte da `CDT_DW` e lette in sola lettura da
`bronze_<env>.condiviso` (D2), non ricostruite dal logistico (OP-02). Il notebook è pronto e testato
offline; manca solo il first-run in cloud, dipendente dalla disponibilità dell'ambiente FASE 0.

## Obiettivo
`LU_AREA_MERCL_LOGIS` (area merceologica logistica) popolata da `bronze.logistica.aree_merceologiche`
ed eseguita con successo in cloud. Fatto = first-run cloud completato senza errori, chiave
`COD_AREA_MERC` univoca, conteggio righe coerente (atteso ~19 righe secondo `02_pipeline_mapping.md`).
Nota: la copertura "5 livelli" piena resta legata a OP-03/04 (macro-aggregato) e OP-02 (master Retail)
→ **da verificare** se l'obiettivo dello sprint va riscoperto o l'ACT va ridefinita sul solo livello area.

## Analisi tecnica
**Notebook**: `notebooks/gold/dimensioni/gold_dim_struttura_merceologica.py` (v3.0.0). Produce
`gold_<env>.logistica.LU_AREA_MERCL_LOGIS` (NOTEBOOK_NAME interno `gold_lu_area_mercl_logis`).
- **Sorgente**: `bronze_<env>.logistica.aree_merceologiche` (notebook Bronze
  `notebooks/bronze/anagrafiche/bronze_aree_merceologiche.py`, MODE=FULL_OVERWRITE, multi-sito
  logistix). Colonne reali Bronze: `MAG_SITO_COD`, `ARM_COD_AREA_MERCEOLOGICA`,
  `ARM_DES_AREA_MERCEOLOGICA`, `ARM_TIPO_PREPARAZIONE`. (OP-10: eventuale filtro `ARM_TIPO_AREA=1`
  applicato a monte in estrazione, non nel Bronze — da confermare con Foconi/Reply.)
- **Mapping Gold**: `ARM_COD_AREA_MERCEOLOGICA → COD_AREA_MERC` (chiave), `ARM_DES_AREA_MERCEOLOGICA
  → DES_AREA_MERC`, `ARM_TIPO_PREPARAZIONE → TIPO_PREPARAZIONE`; aggiunta `DWH_UPDATED_AT`.
- **Dedup multi-sito**: la stessa area è replicata su più siti → `Window.partitionBy(
  "ARM_COD_AREA_MERCEOLOGICA").orderBy(_bronze_insert_ts desc)`, tiene `row_number()==1`; filtro
  `COD_AREA_MERC IS NOT NULL`.
- **Scrittura**: Delta `mode("overwrite")` + `overwriteSchema=true` (pattern anagrafica FULL, stato
  corrente), preceduta da `CREATE SCHEMA IF NOT EXISTS`.
- **Note**: la Silver merceologica è confluita in dim_articolo deprecato (OP-02); il notebook legge
  direttamente il Bronze. `LU_MACRO_AGG_MERCL` (livello superiore) rinviato (OP-03/04).
- **Orchestrazione**: task `gold_lu_area_mercl_logis` nel workflow [[ACT_1.3.7_workflow-dim-refresh]]
  (`workflows/logistica_dim_refresh.yml`), senza `depends_on` (non ha una Silver a monte).
Il residuo è esclusivamente esecutivo: la prima esecuzione su Databricks cloud, non disponibile fino
al completamento di FASE 0 (Fondamenta Infrastrutturali) e alla landing ADLS attiva (per il Bronze
`aree_merceologiche`, dipendenza indiretta via [[ACT_1.2.1_bronze-anagrafiche]] path logistix).

## Sviluppo (diario)
- 2026-07-03 · notebook pronto e validato offline; parziale al 90%, in attesa del first-run cloud.

## Verifica
- First-run cloud di `gold_dim_struttura_merceologica` senza errori (via task `gold_lu_area_mercl_logis`).
- `SELECT COUNT(*)` e `COUNT(DISTINCT COD_AREA_MERC)` coincidono (chiave univoca) su
  `gold_<env>.logistica.LU_AREA_MERCL_LOGIS`; righe > 0 (atteso ~19 da `02_pipeline_mapping.md`).
- Nessun `COD_AREA_MERC` null; `DES_AREA_MERC`/`TIPO_PREPARAZIONE` valorizzati coerenti con Bronze.
- JOIN a valle in Gold DIM_ARTICOLO (ACT_1.2.5) senza esplosione di cardinalità.

## Esito
— (in attesa di ambiente cloud FASE 0)

## Follow-up
- OP-03/OP-04 · livello superiore `LU_MACRO_AGG_MERCL` (macro-aggregato merceologico) — non implementato.
- OP-02 · aggancio anagrafiche master Retail (5 livelli pieni) su Gold DIM_ARTICOLO.
- Al first-run cloud completato → passare a record e chiudere (valutando se rinominare l'ACT sul solo
  livello area merceologica logistica realmente coperto).
