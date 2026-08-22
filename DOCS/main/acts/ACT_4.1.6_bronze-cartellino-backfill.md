# ACT_4.1.6 · bronze_cartellino + backfill

**Status**: in-progress
**Type**: feature
**Origin**: sprint 4.1
**Sprint**: 4.1 — Bronze Prep Spedizioni
**Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)
**Gg (stima)**: 1
**Blocco**: 🏗️ infra — backfill richiede ADLS (storico su cloud)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_4.1.1 (analisi sorgenti)   **Blocca**: Silver/Gold prep sped (completezza cartellino)
**ADR collegate**: ADR-0007 (standard 2-notebook)   **OP collegati**: OP-30

## Contesto e motivazione
Il cartellino (presenze/timbrature carrellisti) è l'ultima sorgente Bronze della Wave C picking.
Alimenta a valle `silver_sessione_carrellista` (task `silver_sessione_carrellista` in
[`logistica_prep_sped.yml`](../../../workflows/logistica_prep_sped.yml), `depends_on: bronze_cartellino`)
e quindi `gold_f_movimentazione_carrellisti`. Il notebook di ingestion è **realizzato**
([`notebooks/bronze/carrellisti/bronze_cartellino.py`](../../../notebooks/bronze/carrellisti/bronze_cartellino.py),
v3.0.0), ma il **backfill storico** richiede accesso ai file su ADLS, non disponibile offline. Senza
backfill il Bronze cartellino copre solo il giorno corrente (~180 righe/giorno, cfr.
[`../02_pipeline_mapping.md`](../02_pipeline_mapping.md) righe 344, 896). Sprint
[`../sprint_agile/sprint_4.1.md`](../sprint_agile/sprint_4.1.md) (4.1.6, 🔵 PARZ. 20%): "Bronze
completi; residuo backfill cartellino". Vedi anche [[ADR-0007]] (standard 2-notebook) e OP-30.

## Obiettivo
Notebook `bronze_cartellino` idempotente e **backfill storico completo** eseguito.
Fatto = tabella `<catalog>.logistica.cartellino` popolata con lo storico disponibile su ADLS,
MERGE idempotente (re-run senza duplicati), conteggio coerente con lo storico atteso.

## Analisi tecnica
- **Notebook**: `notebooks/bronze/carrellisti/bronze_cartellino.py` — `SOURCE_SYSTEM=logistix`,
  `TABLE_NAME=cartellino`, `MODE=DELTA_MERGE`, multisito (9 siti logistix, widget `siti` default
  `lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx`).
- **Schema sorgente esplicito** (`SOURCE_COLS`, verificato — non inventare): `MAG_SITO_COD`,
  `CARTE_COD_CARRELLIST`, `CARTE_DATA`, `CARTE_LOGIN`, `CARTE_LOGOUT`, `CARTE_ATTUALE`.
- **MERGE_KEYS** (chiave naturale): `MAG_SITO_COD`, `CARTE_COD_CARRELLIST`, `CARTE_DATA`.
- **Lettura CSV by-header** (OP-30, memoria bronze-csv-schema-by-name): `header=true`,
  `inferSchema=false`, `sep=";"`, `encoding=UTF-8`, glob `{path}*.csv`; poi
  `select([c for c in SOURCE_COLS if c in raw_df.columns])` — nessuno `.schema()` posizionale.
- **MERGE null-safe idempotente**: condizione `tgt.k <=> src.k` sulle MERGE_KEYS;
  `whenMatchedUpdate` gated su `tgt._row_hash <> src._row_hash` (pruning OP-30, propaga solo il
  delta reale); `whenNotMatchedInsertAll`. Prima esecuzione = CTAS `saveAsTable` con `mergeSchema`.
  Nessuna partizione per data, nessun `_bronze_load_date` nella condizione MERGE.
- **Path landing** (`landing_paths()`): un path per sito
  `{landing_base_path}/logistix-landing/{sito}/cartellino/{YYYY}/{MM}/{DD}/` — per il backfill
  iterare `run_date` sull'intero range storico disponibile su ADLS. File mancanti → `AnalysisException`
  → warning + skip; nessun frame → `dbutils.notebook.exit("NO_DATA")`.
- **`_sito_cod`** derivato via `regexp_extract(input_file_name(), r"/logistix-landing/([^/]+)/")`.
- **Blocco**: il backfill richiede i file storici su ADLS/landing → dipende dall'infra cloud
  (widget `landing_base_path` = `abfss://logistica@<storage>.dfs.core.windows.net`). OP-07 (path
  convention struttura Foconi) da confermare con Reply — da verificare se impatta il layout backfill.

## Sviluppo (diario)
- 2026-07-03 · notebook realizzato (~20%); backfill in attesa di ADLS.

## Verifica
- Eseguire il notebook per ogni `run_date` del range storico (loop offline analogo a
  `tests/local_bronze/run_notebook.py` / `run_b_newday.py`).
- Idempotenza: **re-run dello stesso range** → conteggio righe invariato, nessun duplicato sulla
  chiave `(MAG_SITO_COD, CARTE_COD_CARRELLIST, CARTE_DATA)` (verificabile con distinct-count come in
  `tests/local_bronze/rebuild_prep_sped.py`, blocco VERIFICA NO-DUP).
- Conteggio righe coerente con lo storico atteso (~180 righe/giorno × giorni).

## Esito
— (in attesa di accesso ADLS per il backfill)

## Follow-up
- Al primo accesso cloud: eseguire il backfill e chiudere l'attività; sbloccare
  `silver_sessione_carrellista` → `gold_f_movimentazione_carrellisti`.
- Chiarire OP-07 (path convention Foconi) con Reply prima del backfill se il layout differisce.
