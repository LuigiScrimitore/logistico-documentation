# ACT_1.3.1 · Bronze siti (TABGEN nro_tab=7), operatori, corrieri via landing

**Status**: in-progress
**Type**: feature
**Origin**: sprint 1.3
**Sprint**: 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)
**Fase / Wave**: FASE 1 — Master Data & Dimensioni
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (landing ADLS attiva — FASE 0 / SFTP)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: FASE 0 (landing zone / SFTP)   **Blocca**: ACT_1.3.2, ACT_1.3.3, ACT_1.3.4 (silver logistiche)
**ADR collegate**: ADR-0002 (bronze.condiviso), ADR-0003 (UC Volume landing)   **OP collegati**: —

## Contesto e motivazione
Le anagrafiche logistiche (siti, operatori, corrieri) devono atterrare in Bronze dalla landing per
alimentare le silver DIM logistiche (ACT_1.3.2/1.3.3/1.3.4). I notebook sono scritti ma il first-run
richiede la landing ADLS attiva, dipendente da FASE 0 / SFTP. Precisazione su `TABGEN nro_tab=7`:
oggi `silver_dim_sito` deriva i codici sito da `struttura_mag` (distinct `MAG_SITO_COD`), non da
`TABGEN`; `TABGEN nro_tab=7` è la sorgente **futura** per valorizzare `SITO_DESC` (oggi null, cfr.
`02_pipeline_mapping.md` §dim_sito) → aspetto `nro_tab=7` **da verificare/implementare**.

## Obiettivo
Tabelle Bronze siti/operatori/corrieri popolate dalla landing con first-run cloud completato.
Fatto = i dataset Bronze scritti leggendo i file dalla landing (conteggi righe > 0), tali che le
Silver DIM logistiche a valle girino senza errori.

## Analisi tecnica
Notebook Bronze scritti, pattern canonico `notebooks/templates/template_bronze.py` (schema-on-read
StringType, `sep=";"`, `header=true`, `inferSchema=false`, `encoding=UTF-8`; metadati
`_bronze_load_date`/`_bronze_insert_ts`/`_source_file`; `exit("NO_DATA")` se file assente).

**Siti / topografia** (sorgente logistix multi-sito, MODE=FULL_OVERWRITE, union dei full di tutti i
siti; siti default: `lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx`):
- `notebooks/bronze/anagrafiche/bronze_tabgen.py` → `bronze_<env>.logistica.tabgen`. TABLE_NAME=
  `tabgen`, IS_MULTISITE=True. SOURCE_COLS: `MAG_SITO_COD, TGEN_NRO_TAB, TGEN_COD_SEDE,
  TGEN_CHIAVE1_TAB, TGEN_CHIAVE2_TAB, TGEN_DES_TABGEN, TGEN_CAMPO1_TAB, TGEN_CAMPO2_TAB,
  TGEN_DATA_MODIFICA, TGEN_NOME_UTENTE`. Path per sito:
  `{base}/logistix-landing/{sito}/tagben.../YYYY/MM/DD/`. `_sito_cod` estratto via regexp dal path.
  Il filtro `TGEN_NRO_TAB=7` (sito) è **applicato a valle** in Silver (derivazione `SITO_DESC`), non
  nel Bronze (che carica tutta la TABGEN) → da verificare.
- `notebooks/bronze/anagrafiche/bronze_struttura_mag.py` → `bronze_<env>.logistica.struttura_mag`
  (sorgente reale di `SITO_COD` per `silver_dim_sito` e delle celle per `silver_dim_topografia`).

**Operatori** (4 anagrafiche logistix, MODE=FULL_OVERWRITE, base della UNION OP-15 in
`silver_dim_operatore`):
- `bronze_carrellisti.py` (`carrellisti`: CRLLS_COD_CARRELLIST/CRLLS_DES_CARRELLIST/CRLLS_FLAG_CARR_ATT),
  `bronze_preparatori.py` (`preparatori`: PREP_COD_PREPARATOR/PREP_DES_PREPARATOR/PREP_FLAG_PREP_ATT),
  `bronze_ricevitori.py` (`ricevitori`: RICV_COD_RICEVITOR/RICV_COGNOME+RICV_NOME/RICV_FLAG_RICV_ATT),
  `bronze_spedizionieri.py` (`spedizionieri`: SPE_CODICE/SPE_COGNOME+SPE_NOME, FLG_ATTIVO assente).

**Corrieri** (sorgente CND, MODE=FULL_OVERWRITE):
- `notebooks/bronze/trasporti/bronze_vettori.py` → `bronze_<env>.logistica.t_vettori`. SOURCE_SYSTEM=
  `cnd`, path unico `{base}/cnd-landing/t_vettori/YYYY/MM/DD/`. SOURCE_COLS `VET_*` (18 col:
  VET_CODICE, VET_DESCRIZIONE, VET_INDIRIZZO, VET_CAP, VET_CITTA, VET_PROVINCIA, ...). Task
  `bronze_t_vettori` nel workflow `logistica_landing_ingestion.yml`. Nota: la Silver corriere
  (`silver_dim_corriere`) legge in realtà `bronze.logistica.vettori_track` (vettori@TRACK, stesse
  colonne VET_*, autoritativa dopo dismissione staging `WL1_VETTORI_TRASPO`) → `bronze_vettori_track.py`
  è la sorgente effettivamente consumata a valle; allineamento `t_vettori` vs `vettori_track` da
  verificare.

Il residuo è il first-run che dipende dalla landing ([[ADR-0003]], vedi ACT_0.1.3).

## Sviluppo (diario)
- 2026-07-03 · notebook scritto; parziale al 20%, first-run richiede ADLS.

## Verifica
- First-run cloud: i Bronze `tabgen`, `struttura_mag`, `carrellisti`/`preparatori`/`ricevitori`/
  `spedizionieri`, `t_vettori`/`vettori_track` si popolano dalla landing senza errori (log
  `FULL OVERWRITE ... (N righe)`); conteggi righe > 0.
- Union multi-sito coerente (`_sito_cod` valorizzato dai path logistix).
- A valle senza errori: `silver_dim_sito` (distinct `MAG_SITO_COD` da struttura_mag),
  `silver_dim_operatore` (UNION 4 anagrafiche + self-healing OP-28), `silver_dim_corriere`,
  `silver_dim_topografia` (CELLA_COD da concat STRM_*).

## Esito
— (in attesa di landing ADLS FASE 0)

## Follow-up
- `SITO_DESC` da `TABGEN nro_tab=7` — derivazione non ancora implementata in `silver_dim_sito`
  (oggi `SITO_DESC` null) → da valutare come ACT emergente.
- Allineamento sorgente corriere `t_vettori` (CND) vs `vettori_track` (TRACK) consumata dalla Silver.
- Al first-run completato → passare a record e chiudere.
