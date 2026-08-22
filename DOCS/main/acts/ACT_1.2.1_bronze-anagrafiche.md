# ACT_1.2.1 · Bronze anagrafiche (ART_RADICI, FORNITORI, T_PDV) via landing

**Status**: in-progress
**Type**: feature
**Origin**: sprint 1.2
**Sprint**: 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita
**Fase / Wave**: FASE 1 — Master Data & Dimensioni
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (landing ADLS attiva — FASE 0 / SFTP)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: FASE 0 (landing zone / SFTP)   **Blocca**: ACT_1.2.2, ACT_1.2.3, ACT_1.2.4 (silver anagrafiche)
**ADR collegate**: ADR-0002 (bronze.condiviso), ADR-0003 (UC Volume landing)   **OP collegati**: —

## Contesto e motivazione
Le anagrafiche articolo/PDV devono atterrare in Bronze dalla landing per alimentare le silver DIM
(ACT_1.2.2/1.2.3/1.2.4). Nota importante rispetto allo scope originario `ART_RADICI, FORNITORI, T_PDV`:
- **Articolo** → sorgente reale `cdt-estr-raw-landing/artdgene` (RAW `ARTDGENE`), NON più lo staging
  `wl1_artdgene` (ridisegno "SCELTA B"); le derivate ART_RADICE/VAR restano in Silver.
- **PDV** → sorgente reale `cdt-estr-raw-landing/apvpunto_vendita` (RAW `APVPUNTO_VENDITA`), NON più
  `wl1_apvpunto_vendita`. Il vecchio `bronze_t_pdv` (CND `t_pdv`) è stato **RIMOSSO (RS-01, 2026-06-20)**:
  il PDV arriva da `CDT_DW` come lookup condivisa (`LU_PDV` in `bronze_<env>.condiviso`).
- **Fornitore** → **da verificare**: non esiste un notebook Bronze `FORNITORI`/`fornitore` nel repo;
  `LU_FORNITORE` è lookup condivisa estratta da `CDT_DW` (OP-02), non ricostruita dal logistico. Lo
  scope "FORNITORI" dell'ACT è quindi verosimilmente superato da RS-01/OP-02.

Il residuo è il first-run che richiede la landing ADLS attiva, dipendente da FASE 0 / SFTP.

## Obiettivo
Tabelle Bronze anagrafiche articolo/PDV popolate dalla landing con first-run cloud completato.
Fatto = i dataset Bronze scritti leggendo i file dalla landing (conteggi righe > 0). Lo scope
`FORNITORI` va riconciliato con RS-01/OP-02 → **da verificare**.

## Analisi tecnica
Notebook Bronze già scritti, pattern canonico `notebooks/templates/template_bronze.py`. Ingestion
by-name (header CSV, `inferSchema=false`, `sep=";"`, `encoding=UTF-8`, schema-on-read StringType —
no `.schema()` posizionale). Metadati Bronze aggiunti: `_bronze_load_date`, `_bronze_insert_ts`,
`_source_file`. Tolerant-to-missing-file: `dbutils.notebook.exit("NO_DATA")`.
- **Articolo** — `notebooks/bronze/prep_spedizioni/bronze_artdgene.py` (v1.0.0). SOURCE_SYSTEM=
  `cdt_estr_raw`, TABLE_NAME=`artdgene`, MODE=FULL_OVERWRITE, `SOURCE_COLS=[]` (estrae tutto).
  Path: `{landing_base_path}/cdt-estr-raw-landing/artdgene/YYYY/MM/DD/`. Target
  `bronze_<env>.logistica.artdgene`.
- **PDV** — `notebooks/bronze/prep_spedizioni/bronze_apvpunto_vendita.py` (v1.0.0). SOURCE_SYSTEM=
  `cdt_estr_raw`, TABLE_NAME=`apvpunto_vendita`, MODE=FULL_OVERWRITE, `SOURCE_COLS=[]`. Path:
  `{landing_base_path}/cdt-estr-raw-landing/apvpunto_vendita/YYYY/MM/DD/`. Target
  `bronze_<env>.logistica.apvpunto_vendita`. Alimenta `silver_dim_pdv.py` (clean 1:1) e `silver_t_pdv.py`.
- Le `LU_*` master (`LU_FORNITORE`, `LU_PDV`, `LU_ART_RADICE`) stanno in `bronze_<env>.condiviso`
  (D2 / [[ADR-0002]]), estratte da `CDT_DW`; landing su UC Volume ([[ADR-0003]], vedi ACT_0.1.3).
- **Orchestrazione**: `artdgene`/`apvpunto_vendita` sono sorgenti `cdt_estr_raw` (non nei task CND del
  workflow `logistica_landing_ingestion.yml`, che copre CND/STAT) → **da verificare** in quale
  workflow/task sono schedulati (candidato: ingestion CDT_ESTR_RAW).
Il residuo è il first-run, che dipende dalla landing (ADR-0003, vedi ACT_0.1.3).

## Sviluppo (diario)
- 2026-07-03 · notebook scritto; parziale al 20%, first-run richiede ADLS.
- 2026-06-20 · RS-01: rimosso `bronze_t_pdv` (CND `t_pdv`); PDV da CDT_DW. Ridisegno SCELTA B su
  articolo/PDV (sorgente RAW `cdt-estr-raw-landing`, non staging `wl1_*`).

## Verifica
- First-run cloud: i Bronze `artdgene` e `apvpunto_vendita` si popolano dalla landing senza errori di
  accesso; conteggi righe > 0 (log `FULL OVERWRITE ... (N righe)`).
- Schema by-name preservato (nessun disallineamento posizionale); metadati `_bronze_*` presenti.
- A valle: `silver_dim_articolo` / `silver_dim_pdv` girano senza colonne mancanti.

## Esito
— (in attesa di landing ADLS FASE 0)

## Follow-up
- RS-01 / OP-02 · riconciliare lo scope `FORNITORI`/`T_PDV` dell'ACT con l'architettura attuale
  (master da CDT_DW in `bronze.condiviso`) → eventuale rinomina/ridimensionamento dell'ACT su
  articolo+PDV effettivamente coperti.
- Al first-run completato → passare a record e chiudere.
