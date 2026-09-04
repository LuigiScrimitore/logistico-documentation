---
id: LL-021
titolo: Bronze su UC serverless — input_file_name() non è supportato (usa _metadata.file_path) e il path mancante letto lazy sfugge al try/except
sintomi:
  - "[UC_COMMAND_NOT_SUPPORTED.WITH_RECOMMENDATION] The command(s): input_file_name are not supported in Unity Catalog. Please use _metadata.file_path instead"
  - "[PATH_NOT_FOUND] Path does not exist: .../<tabella>/YYYY/MM/DD/*.csv nonostante il try/except AnalysisException sulla lettura"
tag: [databricks, unity-catalog, serverless, bronze, spark]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-09-01
origine: [smoke-test-carichi-dev]
---

## Sintomo
Due errori distinti nei notebook Bronze quando girano davvero su serverless + Unity Catalog:
1. `UC_COMMAND_NOT_SUPPORTED: input_file_name are not supported ... use _metadata.file_path instead` — al primo
   action (`.count()`), sui bronze che derivano `_source_file`/`_sito_cod` dal path del file.
2. `PATH_NOT_FOUND: .../*.csv` per una tabella **non presente** nella landing del giorno, **nonostante** il
   `try/except AnalysisException` attorno alla lettura: l'errore scatta più tardi (su `.select`/`.columns`), fuori dal try.

## Strada sbagliata
- Usare `F.input_file_name()` (funziona su cluster classici, **vietato** in UC).
- Affidarsi al `try/except AnalysisException` attorno a `spark.read.csv(...)`: la `.csv()` è **lazy**, il path non
  viene risolto lì; l'eccezione arriva al primo accesso allo schema/azione — quando il codice è già oltre il try.

## Regola
1. **Path del file**: cattura `_source_file` alla lettura con `F.col("_metadata.file_path")` e deriva da lì
   (`regexp_extract` per `_sito_cod`); preservala nella `.select` dei soli SOURCE_COLS.
2. **Skip robusto del path assente**: forza la risoluzione **dentro** il try e allarga a `except Exception`:
   ```python
   for p in landing_paths():
       try:
           df = read_one(p)
           df.columns            # forza la risoluzione: path assente -> eccezione -> skip
           frames.append(df)
       except Exception as _e:
           logger.warning(f"Path non trovato/illeggibile: {p} — skip ({type(_e).__name__})")
   ```
   Se `frames` resta vuoto → `dbutils.notebook.exit("NO_DATA")` (giorno senza quella sorgente = skip pulito, non fallimento).

## Perché
`input_file_name()` è deprecato/bloccato in UC per governance (path fisici non esposti); `_metadata.file_path` è la
pseudo-colonna supportata equivalente. La lettura Spark è lazy per design: senza un action che tocchi il path,
l'assenza non emerge — quindi va forzata dove la vuoi gestire. A valle, un Silver che legge una tabella Bronze mai
creata dà `TABLE_OR_VIEW_NOT_FOUND`: la robustezza NO_DATA va portata anche lì (residuo). Contesto wheel: [[LL-020]].

## Conferme e contraddizioni
- 2026-09-01 · luigi.scrimitore · smoke test `logistica_carichi` DEV: `bronze_carichi_dettagli/testate` (con dati
  lgcx) fallivano su `input_file_name` → fix `_metadata.file_path` = SUCCESS; `pesate`/`tracciace178` (non seedati)
  fallivano su PATH_NOT_FOUND → fix skip-forzato = SUCCESS (NO_DATA). Silver corrispondenti restano rossi con
  `TABLE_OR_VIEW_NOT_FOUND` finché la tabella bronze non esiste (residuo di robustezza NO_DATA lato Silver).
