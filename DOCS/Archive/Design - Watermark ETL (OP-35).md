# Design — Watermark / Controllo Incrementale ETL (OP-35)

**Stato:** proposta di design (da rivedere prima dell'implementazione)
**Data:** 2026-06-14
**Owner:** Cloud Data Architect — Team Logistico 2.0
**Riferimenti:** OP-35 (granularità per sorgente), OP-30 (incrementalità implementata), OP-36 (runner test sessione singola)

---

## 1. Obiettivo e contesto

Oggi la catena incrementale è guidata **dall'esterno** dal `run_date` (widget/job param), senza memoria persistente dell'ultima data processata:
- **Bronze**: legge il landing della partizione `run_date` (`<source>-landing/{tabella}/YYYY/MM/DD/`), per-sito su logistix, singolo su stat/track/cdt_estr_raw.
- **Clean** (silver): filtra `_bronze_load_date == run_date` + MERGE upsert.
- **Prep #2**: ricalcola le chiavi con `_silver_load_date == run_date`.

**Problema:** se si accumulano più giornate di solo-landing (come il caso 06-12/06-13), il catch-up richiede **un run per giorno** in sequenza. Inoltre, se un singolo caricamento sorgente fallisce (es. `spedizioni@TRACK` ORA-01555), non c'è modo di riprocessare **solo quello** senza rifare l'intera giornata.

**Soluzione:** una **tabella di controllo** (`control_<env>.etl.watermark`) che memorizza, con granularità **(stage, sistema, tabella, sito)**, l'ultima data processata con successo. Abilita:
1. **Catch-up multi-giorno in un solo run** (range invece di singolo `run_date`).
2. **Isolamento fallimenti** + **retry selettivo** (riprocessa solo la chiave fallita).
3. **Auditabilità** (chi/quando/quante righe/esito).

---

## 2. Decisioni recepite

- **Granularità: `(stage, sistema, tabella, sito)`** — NON globale. (OP-35, confermato 2026-06-12.)
- **Store: catalog dedicato `control_<env>`** — separato dai dati di business; schema `etl`; tabella `watermark`. (Scelta 2026-06-14.)
- **Approccio: tabella di controllo esplicita (OP-35 opzione B)** — auditabile, granulare, gestisce retry selettivi.

---

## 3. Modello dati

### 3.1 Naming (Unity Catalog vs locale)

| Ambiente | FQN |
|---|---|
| Databricks dev | `control_dev.etl.watermark` |
| Databricks prod | `control_prod.etl.watermark` |
| Locale (runner test, 2 livelli collassati) | db `control_dev_etl`, tabella `watermark` → `control_dev_etl.watermark` |

`get_catalog` va esteso con il layer `control` (dev e prod **separati e speculari** su tutti i livelli, Gold incluso):
```python
_CATALOG_MAP = {
  "dev":  {"bronze":"bronze_dev","silver":"silver_dev","gold":"gold_dev","control":"control_dev"},
  "prod": {"bronze":"bronze_prod","silver":"silver_prod","gold":"gold_prod","control":"control_prod"},
}
```
Nel runner locale: aggiungere `control_dev_etl`, `control_dev_parametri` (e le varianti `_prod`) a `DB_NAMES` di `spark_session.py`.

> **Control layer trasversale (per ambiente).** Il catalog `control_<env>` ospita due schemi con governance diversa:
> - **`etl`** — stato operativo scritto dalle pipeline: `watermark` (questo design), e in futuro log run / esiti DQ.
> - **`parametri`** — tabelle **parametriche e manuali di integrazione** mantenute a mano (mapping, override, correzioni codici, soglie DQ, calendari custom). Lette dalle pipeline silver/gold dove serve integrare/correggere i sorgenti. Criterio: configurazione/correttiva piccola → `parametri`; vero dato di business → trattarla come sorgente landing→bronze.

### 3.2 Schema tabella `watermark`

| Colonna | Tipo | Descrizione |
|---|---|---|
| `stage` | STRING | confine di processing: `landing_to_bronze` \| `bronze_to_clean` \| `clean_to_prep` |
| `sistema` | STRING | sorgente: `logistix` \| `stat` \| `track` \| `cdt_estr_raw` \| `cdtdw` |
| `tabella` | STRING | nome tabella (landing/bronze), es. `storico_liste`, `sto_righe_carico` |
| `sito` | STRING | sito logistix (`lgvx`, `lonx`, …) **oppure** `_ALL_` per sorgenti non multi-sito (stat/track/cdt_estr_raw/cdtdw) |
| `last_processed_date` | DATE | ultima data **processata con successo** per la chiave (semantica per-stage, vedi §3.3) |
| `last_run_ts` | TIMESTAMP | timestamp dell'ultimo aggiornamento watermark |
| `rows_processed` | BIGINT | righe processate nell'ultimo step (diagnostico) |
| `esito` | STRING | `OK` \| `FAIL` |
| `message` | STRING | nota/errore sintetico (per FAIL o warning) |
| `_updated_at` | TIMESTAMP | audit tecnico (current_timestamp allo scrittura) |

**Chiave logica (MERGE):** `(stage, sistema, tabella, sito)` — una sola riga per chiave, aggiornata in upsert. (Niente storicizzazione delle versioni: per l'audit storico ci si appoggia alla Delta history / `DESCRIBE HISTORY`.)

**Tabella Delta**, non partizionata (volumi piccoli: ~ n_tabelle × n_siti × n_stage = ordine 10²–10³ righe).

### 3.3 Semantica di `last_processed_date` per stage

- **`landing_to_bronze`**: data della **partizione landing** (`YYYY/MM/DD`) ultima ingerita con successo a bronze per quella `(sistema, tabella, sito)`. Il bronze MERGE-prune (`_row_hash`) resta invariato; il watermark dice solo *fin dove siamo arrivati a leggere il landing*.
- **`bronze_to_clean`**: massimo `_bronze_load_date` processato con successo dal clean per quella tabella. (Sito: per stat il clean non ha colonna sito → `_ALL_`; per le tabelle logistix-derivate si può tenere `_ALL_` a livello clean, vedi §6 nota.)
- **`clean_to_prep`**: massimo `_silver_load_date` processato dai prep pattern #2. (Opzionale in questa fase — i prep oggi usano `run_date`; vedi §5.3.)

---

## 4. Helper (in `lib/logistica_utils/utils.py`)

```python
def get_control_table(env: str) -> str:
    """FQN tabella watermark: control_<env>.etl.watermark."""
    return f"{get_catalog('control', env)}.etl.watermark"

def ensure_watermark_table(spark, env: str) -> str:
    """Crea schema control + tabella watermark se assenti. Idempotente. Ritorna FQN."""
    # CREATE SCHEMA IF NOT EXISTS control_<env>.etl  (in locale: db control_<env>_etl)
    # CREATE TABLE IF NOT EXISTS <fqn> (...colonne §3.2...) USING delta
    ...

def read_watermark(spark, env, stage, sistema, tabella, sito="_ALL_"):
    """Ritorna last_processed_date (date) per la chiave, o None se assente/FAIL."""
    ...

def update_watermark(spark, env, stage, sistema, tabella, sito,
                     last_processed_date, rows_processed, esito="OK", message=None):
    """MERGE upsert della riga (stage,sistema,tabella,sito). Aggiorna solo su esito OK
       per la data; su FAIL scrive esito='FAIL'+message SENZA avanzare last_processed_date."""
    ...

def pending_landing_dates(spark, env, sistema, tabella, sito, available_dates):
    """Dato l'elenco delle partizioni landing presenti, ritorna quelle > last_processed_date
       (per lo stage landing_to_bronze). Usato dall'orchestratore per il catch-up."""
    ...
```

**Regola di transazionalità (critica):**
> Il watermark si aggiorna **solo dopo** che lo step ha scritto con successo il target (bronze MERGE / clean MERGE). In caso di errore si scrive `esito='FAIL'` + `message` **senza** avanzare `last_processed_date`. Così un retry riparte esattamente dalla data fallita. L'update del watermark e la scrittura del target **non** sono in una transazione distribuita unica: l'ordine è *scrivi target → poi avanza watermark*; se il processo muore in mezzo, al retry si rilegge/riscrive la stessa data (idempotente grazie al MERGE upsert + `_row_hash`).

---

## 5. Integrazione nei layer

### 5.1 Landing → Bronze (`stage = landing_to_bronze`)

Per ogni `(sistema, tabella, sito)`:
1. L'orchestratore (o il notebook) calcola le **partizioni landing disponibili** e quelle **pending** = `> last_processed_date` (via `pending_landing_dates`).
2. Per ciascuna data pending (in ordine), il bronze legge `…/YYYY/MM/DD/`, fa MERGE-prune, poi `update_watermark(..., last_processed_date=data, esito='OK')`.
3. Se una data fallisce: `update_watermark(..., esito='FAIL', message=...)`, **stop** su quella chiave; le altre `(tabella, sito)` proseguono indipendenti.

> Nota multi-sito: logistix itera i siti → una riga watermark per sito. stat/track/cdt_estr_raw → `sito='_ALL_'`.

### 5.2 Bronze → Clean (`stage = bronze_to_clean`)

Sostituisce il filtro `_bronze_load_date == run_date` con un **range**:
```python
process_from = read_watermark(spark, env, 'bronze_to_clean', sistema, tabella) or DATE_MIN
# incrementale: tutte le righe non ancora processate
raw = raw.filter(F.col("_bronze_load_date") > F.lit(process_from))
# … MERGE upsert come oggi …
new_wm = raw.agg(F.max("_bronze_load_date")).collect()[0][0]
update_watermark(spark, env, 'bronze_to_clean', sistema, tabella, '_ALL_', new_wm, rows_clean, 'OK')
```
- `full_refresh=true` → ignora il watermark (rilegge tutto, come oggi) e **resetta** il watermark al max.
- Catch-up: se il bronze contiene 06-12 e 06-13 non ancora processati, **un solo run** li prende entrambi (range), invece di due run.

### 5.3 Clean → Prep #2 (`stage = clean_to_prep`) — opzionale fase 2

I prep pattern #2 oggi usano `_silver_load_date == run_date`. Con watermark diventerebbe `_silver_load_date > process_from`. **Rinviabile**: i prep sono idempotenti e il volume del range catch-up è gestibile; da valutare insieme all'orchestrazione.

---

## 6. Flusso catch-up multi-giorno (esempio 4 giorni di solo-landing)

```
Giorni landing accumulati: 06-11, 06-12, 06-13, 06-14 (solo landing, no bronze)

1) LANDING→BRONZE (per ogni sistema/tabella/sito):
   pending = [06-11..06-14] (tutte > watermark)
   per ogni data: read landing/YYYY/MM/DD → MERGE-prune bronze → avanza watermark
   (se 06-13 spedizioni@track fallisce: watermark spedizioni/track resta a 06-12,
    le altre tabelle avanzano a 06-14; retry mirato solo su spedizioni/track)

2) BRONZE→CLEAN (un solo run):
   process_from = max watermark clean (es. 06-10) → filtra _bronze_load_date > 06-10
   → prende 06-11..06-14 in un colpo → MERGE upsert → avanza watermark a 06-14

3) PREP/GOLD: un solo run sul delta accumulato (pattern #2 su _silver_load_date del range).
```

> Nota su `sito` a livello clean: le tabelle STAT (storico_liste/bolle) non hanno il sito come dimensione di partizione del watermark clean → `_ALL_`. Le tabelle logistix-derivate (carichi/movimenti) **potrebbero** voler watermark per-sito anche a livello clean; per semplicità di fase 1 si tiene `_ALL_` a livello clean (il per-sito serve soprattutto a landing→bronze per l'isolamento fallimenti). Da rivalutare se emergono fallimenti per-sito a valle.

---

## 7. Impatti e cose da curare

- **`get_catalog`**: aggiungere layer `control` (§3.1). Backward-compatible (nuova chiave nel map).
- **Runner locale** (`spark_session.py`): aggiungere `control_dev_etl`/`control_prod_etl` a `DB_NAMES`; `ensure_databases` li crea.
- **Terraform** (a regime Databricks): nuovo catalog `control_<env>` + schema `etl` + grant. (Non necessario in locale.)
- **Rewrite FQN runner**: il runner collassa `catalog.schema.table` → `catalog_schema.table`. `control_dev.etl.watermark` → `control_dev_etl.watermark`: verificare che `_install_fqn_rewriters` gestisca anche questo catalog (probabile sì, è generico).
- **Date di default**: `process_from` iniziale quando il watermark è assente → usare una `DATE_MIN` esplicita (es. `1900-01-01`) coerente coi rebase LEGACY già configurati, **oppure** trattare `None` come full-refresh-implicito alla prima esecuzione.
- **Concorrenza**: in locale sessione singola, nessun problema. A regime Databricks, se più job aggiornano la stessa riga watermark, il MERGE Delta è ACID per-tabella; valutare conflitti di commit (retry).
- **Relazione con `process_from` interim (OP-30)**: il parametro esplicito `process_from` resta come override manuale; il watermark ne diventa il default auto-derivato.

---

## 8. Piano di implementazione — stato

1. ✅ `get_catalog` + `DB_NAMES` (layer control). *(commit catalog refactor)*
2. ✅ Helper in `utils.py`: `get_control_table`, `ensure_watermark_table`, `read_watermark`, `update_watermark`, `pending_landing_dates`.
3. ✅ Test `tests/local_bronze/test_watermark.py` — ALL_OK (create → read None → OK avanza → FAIL non avanza → upsert idempotente → catch-up range → isolamento sito).
4. ✅ Pilota `bronze_to_clean` su `silver_storico_liste_clean`: range `_bronze_load_date > process_from` + update watermark; override widget `process_from`. Test `test_watermark_pilot.py` — ALL_OK (da wm 06-11 un solo run fa catch-up 06-12+06-13 → 06-13; 2° run NO_DATA idempotente).
5. ⏳ Roll-out agli altri clean (`storico_bolle_clean`, carichi/spedizioni/ordini) + (opz.) `landing_to_bronze` nell'orchestratore (`pending_landing_dates`). — *L*
6. ⏳ (Fase 2) `clean_to_prep` se necessario; deploy Terraform control catalog + integrazione orchestrazione Databricks. — *L*

**Fatto (2026-06-14):** fondamenta (1–3) + pilota (4) validati su caso reale (STAT `storico_liste`). Il pattern è pronto per il roll-out (5).
