---
id: LL-027
titolo: Serverless ha ANSI ON — cast/parse su dati legacy sporchi vanno con try_cast/try_to_timestamp (e F.try_cast non esiste)
sintomi:
  - "CAST_INVALID_INPUT: The value '...' cannot be cast to BIGINT/TIMESTAMP because it is malformed"
  - "CANNOT_PARSE_TIMESTAMP: Text '...' could not be parsed"
  - "NUMERIC_VALUE_OUT_OF_RANGE: double cannot be represented as Decimal(p,s)"
  - "AttributeError: module 'pyspark.sql.functions' has no attribute 'try_cast'"
tag: [serverless, ansi, cast, try_cast, silver, dati-sporchi, stat]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-04
origine: [ACT_9027]
---

## Sintomo
Un notebook silver fallisce in serverless su un `cast`/`to_timestamp`/aritmetica con valori legacy
sporchi: `'S'`, `'2.0'`, `'1.4'`, `'0'`, ora `'603'`, timestamp `'2026-09-01 603'`. In locale (o con
ANSI OFF) davano NULL; in serverless (ANSI ON) **lanciano** e fanno fallire il job. Spesso in catena:
risolto un cast, ne emerge un altro a valle.

## Strada sbagliata
- Affidarsi a `col.cast("int"/"timestamp")` sui campi STAT (tutto StringType, spesso sporco): sotto ANSI
  crasha invece di dare NULL.
- `coalesce(col_stringa, F.lit(0))`: il literal intero forza la **coercizione stringa→intero**; un valore
  decimale/sporco (`'1.4'`) crasha. Vale anche per prezzi/quantita' letti come stringa.
- Provare a disattivare ANSI con `spark.conf.set("spark.sql.ansi.enabled","false")`: **vietato in serverless**.
- Usare `F.try_cast(...)`: **non esiste** in questa versione di PySpark (AttributeError).

## Regola
- Cast tolleranti: `F.expr("try_cast(<col> as <tipo>)")` (malformato → NULL). `F.try_cast` NON c'e';
  `F.try_to_timestamp(col, F.lit(fmt))` invece **esiste** e va bene per i timestamp.
- Nei `coalesce(stringa, default)` di campi numerici: castare prima con `try_cast` e usare un default
  del tipo giusto (`F.lit(0)`/`F.lit(0.0)`), es.
  `F.coalesce(F.expr("try_cast(sb.BOL_PRZ as double)"), F.lit(0.0))`.
- Durate/aritmetica con rischio overflow decimale: `try_cast(... as decimal(p,s))` (out-of-range → NULL).
- Date legacy: usare `julian_to_date` (gia' ANSI-safe, [[LL-022]]) invece di `cast`.

## Perche'
Il compute **serverless** gira con Spark ANSI abilitato e non lascia override delle spark.conf: un cast
invalido e' un errore hard, non un NULL. I dati STAT/Logistix sono StringType con sentinelle e sporcizia
storica: ogni conversione va resa esplicitamente tollerante. Vedi [[LL-028]] (altra conf serverless vietata),
[[LL-022]] (JDN), [[LL-026]] (full_refresh overwrite dopo remap).

## Conferme e contraddizioni
- 2026-09-04 · Francesco Foconi · DEV prep_sped: catena di crash risolta con try_cast/try_to_timestamp su
  `silver_prep_riepiloghi`, `silver_prep_prep_sped` (codici/prezzi BOL), `silver_prep_turno_prep_sito`,
  `silver_sessione_carrellista` + `julian_to_date` ANSI-safe → prep_sped 20/20, datamart 12/12, 7/7 verde.
