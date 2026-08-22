# ACT_9016 · Guardrail pytest eseguibili in locale: classpath Delta + residui d'ambiente

**Status**: done (suite 111/111; tutti i follow-up chiusi)   **Type**: test-infra
**Origin**: follow-up [[ACT_9015]] (OP-CAR-6 → aggiunta di `pytest`)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (test/DQ)
**Gg (stima)**: 0,5   **Blocco**: 🟢 (solo-locale)
**Created**: 2026-08-22   **Closed**: 2026-08-22
**Dipende da**: [[ACT_9014]] (30 guardrail workflow), [[ACT_9015]] (OP-CAR-6)   **Blocca**: —
**ADR collegate**: —   **OP collegati**: nuovi OP-TST-1, OP-TST-2

## Contesto e motivazione
In [[ACT_9015]] (OP-CAR-6) è emerso che `pytest` **non era nell'immagine locale**: i 30 guardrail di
[[ACT_9014]] e i test DQ esistevano ma **in locale nessuno poteva eseguirli** — documentazione, non
protezione. Aggiunto `pytest>=8.0` ai requirements e ricostruita l'immagine, al primo run reale la suite
completa (`pytest tests/`) si è rivelata **non eseguibile per tre motivi distinti**, tutti pre-esistenti e
mai emersi proprio perché la suite non girava mai.

Questo ACT traccia il lavoro per rendere i guardrail *realmente eseguibili*. Principio guida (lo stesso di
[[ADR-0020]]): un guardrail che non gira è peggio di nessun guardrail, perché dà falsa sicurezza.

## Analisi tecnica

### Snapshot esito (2026-08-22, `pytest` sui 5 file top-level)
`3 failed, 96 passed, 12 errors in 38,51s`. I 96 verdi includono **tutti** i 30 guardrail di ACT_9014
(`test_workflows_alignment`, YAML/DAG puri) e i test calendario/30min. I rossi sono **solo** i test che
aprono una sessione Delta e i fixture DQ.

### Problema A — collection bloccata da `tests/local_bronze/` (RISOLTO aggirando)
`pytest tests/` restava **28 minuti in fase di collection** e poi abortiva con 2 errori di raccolta su
`tests/local_bronze/test_watermark.py` e `test_bronze_pruning.py`:
```
[REQUIRES_SINGLE_PART_NAMESPACE] spark_catalog requires a single-part namespace, but got `control_dev`.`etl`.
```
Quei file eseguono Spark SQL **a import-time** con FQN a 3 parti (`control_dev.etl.…`) validi solo su Unity
Catalog. `tests/local_bronze/` non è la suite di guardrail: è l'harness dell'ingestion bronze (script
`diag_*.py`, `run_notebook.py`, `spark_session.py`). **Decisione**: la suite guardrail si lancia sui 5 file
top-level, escludendo `tests/local_bronze/`. Comando di riferimento:
```
python -m pytest tests/test_workflows_alignment.py tests/test_dq_carichi.py \
  tests/test_logistica_utils.py tests/test_dim_calendario.py tests/test_regola_30min.py -q
```
Follow-up minore: valutare `--ignore=tests/local_bronze` in `pytest.ini`/`pyproject` così `pytest tests/`
non riesploda, oppure spostare `local_bronze/` fuori dal path di discovery.

### Problema B — classpath Delta assente nel fixture `spark` (RISOLTO)
Tutti i test Delta fallivano con:
```
java.lang.ClassNotFoundException: org.apache.spark.sql.delta.catalog.DeltaCatalog
```
Il fixture `spark` in `tests/conftest.py` dichiarava estensione e catalog Delta ma **non metteva i jar sul
classpath** (mancava `configure_spark_with_delta_pip` / `spark.jars.packages`). Il Dockerfile pre-scarica i
jar nella cache ivy (`/home/jovyan/.ivy2/.../delta-spark_2.12-3.2.0.jar`), ma il conftest non li agganciava.
**Fix**: builder passato a `configure_spark_with_delta_pip(builder).getOrCreate()` — risolve **offline** dalla
cache ivy pre-popolata. Dopo il fix la sessione si costruisce e i 96 verdi salgono da 30 (solo YAML) a 96.

### Problema C1 — fixture DQ: `float` in colonna `DecimalType` → OP-TST-1 (RISOLTO 2026-08-22)
Le 12 righe *error* (setup di `test_dq_carichi` e `TestDQHelper`) falliscono **prima** di testare la logica:
```
PySparkTypeError: [CANNOT_ACCEPT_OBJECT_IN_TYPE] DecimalType(18,4) can not accept object 102.0 in type float.
```
I fixture costruiscono i DataFrame campione passando `float` Python a colonne `DecimalType`. `delta-spark==3.2.0`
tira `pyspark 3.5.9` (più recente del 3.5.0 dell'immagine base), che ha il type-check stretto e rifiuta la
coercizione `float → Decimal` che le versioni vecchie accettavano. **Non è un problema della logica DQ.**
Opzioni per OP-TST-1: (a) usare `decimal.Decimal(...)` nei fixture; (b) pin `pyspark==3.5.0` allineato
all'immagine base; (c) cast esplicito in fase di build del DataFrame. La (a) è la più mirata; la (b) rimuove
anche lo skew di versione tra pip e SPARK_HOME.

**Fix applicato (a)**: in `tests/conftest.py`, `sample_carichi_df` usa `Decimal(...)` invece di `float(...)`
per le tre colonne `DecimalType` (`PESO_NETTO`/`PESO_LORDO`/`QTA_RICEVUTA`). Era l'unico fixture con
`DecimalType` popolato da float, ed è quello condiviso da tutti i 12 test in *error*. Esito su
`test_dq_carichi` + `test_logistica_utils`: da `12 errors` a **0**, `50 passed` (restano solo le 3 di
`TestDeltaHelper` → OP-TST-2). Scelta la (a) sulla (b) perché isolata ai test: non ho voluto pinnare pyspark
finché non serve, per non nascondere lo skew di versione (che resta annotato qui).

### Problema C2 — `merge_into` costruisce FQN con punto iniziale in locale → OP-TST-2 (RISOLTO 2026-08-22)
Le 3 righe *failed* (`TestDeltaHelper`) vengono da [delta_helper.py:130](../../lib/logistica_utils/delta_helper.py):
```
ParseException: Syntax error at or near '.'  ==SQL== .test_delta_db.test_upsert
```
`merge_into` compone un FQN a 3 parti `{catalog}.{schema}.{table}`; in locale il catalog è vuoto → nome con
punto iniziale che lo `spark_catalog` (a 2 parti) rifiuta. Su Databricks (UC, 3 livelli) è corretto: è il solo
ambiente locale a essere l'anomalia. Opzioni per OP-TST-2: (a) in `merge_into` omettere il segmento catalog
quando vuoto/None (fix di produzione, basso rischio, migliora anche la portabilità); (b) far girare i test in
modalità UC-like localmente; (c) marcare i 3 test `skip` in locale con motivo esplicito. La (a) è preferibile:
il bug è reale anche se oggi si manifesta solo in locale.

**Fix applicato (a)**: introdotto in `lib/logistica_utils/delta_helper.py` un helper `_build_fqn(catalog, schema,
table)` che con `catalog` vuoto/None restituisce `schema.table` (2 parti) invece di `.schema.table`. Usato sia da
`DeltaHelper._fqn` (che serve `merge_into`, `get_max_watermark`, `table_exists`, replaceWhere, append) sia dalla
funzione module-level `get_watermark`, che aveva lo **stesso** bug latente — un'unica sorgente di verità. Con
`catalog` valorizzato il comportamento a 3 livelli di Unity Catalog è invariato.

## Esito e stato
- ✅ **Problema B**: risolto in `tests/conftest.py` (classpath Delta via `configure_spark_with_delta_pip`).
- ✅ **OP-TST-1** (float→Decimal nei fixture): risolto (2026-08-22) con `Decimal(...)` in `conftest.py`.
- ✅ **OP-TST-2** (FQN locale in `merge_into`): risolto (2026-08-22) con `_build_fqn` in `delta_helper.py`.
- ✅ **Problema A**: risolto (2026-08-22) con `--ignore=tests/local_bronze` in `addopts` di `pytest.ini`.
  Ora anche il comando naturale `pytest` (via `testpaths = tests`) colleziona i soli 5 file guardrail senza
  impiccarsi in collection.

**Suite completa: 111/111 verde** (2026-08-22), sia coi 5 file nominati sia con `pytest` bare.

Nessuno dei rossi è una regressione di OP-CAR-6: `utils.py` cambia solo `attach_carico_peso_volume`, che non è
toccato da nessuno dei test falliti. OP-CAR-6 resta validato end-to-end contro il Gold reale (vedi [[ACT_9015]]).

## Lezioni collegate
- [[LL-005]] — il tema del guardrail che non protegge finché non gira davvero.
