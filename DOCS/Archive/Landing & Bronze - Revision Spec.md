# Landing & Bronze — Revision Spec (standard di implementazione)

**Data:** 2026-06-08 · **Autore:** Cloud Data Architect · **Scope:** layer Landing + Bronze
**Riferimenti:** `Analisi AS-IS Estrazione - CDT_ESTR.md`, `Open Points - Logistico 2.0.md`

Questa spec è lo standard unico a cui devono conformarsi **tutti** i notebook Bronze. Recepisce: modalità FULL/DELTA verificate sull'AS-IS (OP-08), convenzione path landing (OP-07), separazione del dato grezzo/unitario (OP-12/13/15/17), sorgente STAT per prep-spedizioni (OP-16), distinzione DETTAGLIO_CARR≠IMBFMOVIM (OP-14).

---

## 1. Principi

1. **Nessun JDBC.** Il Bronze legge esclusivamente file (CSV/Parquet) dalla landing zone ADLS Gen2.
2. **Dato grezzo e unitario.** Ogni notebook legge **una sola** tabella sorgente. Nessun JOIN, nessuna funzione di normalizzazione (es. `fn_get_radice`), nessuna unione fra tabelle. Tutte le trasformazioni vanno in Silver.
3. **Tipi StringType.** In Bronze i campi restano stringa (schema-on-read); i cast avvengono in Silver.
4. **Idempotenza.** Rieseguire lo stesso `run_date` non duplica né corrompe i dati.

## 2. Widget standard (uniformi su tutti i notebook)

```python
dbutils.widgets.dropdown("env", "dev", ["dev", "prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
dbutils.widgets.text("landing_base_path", "abfss://logistica@<storage>.dfs.core.windows.net", "Landing base path")
dbutils.widgets.text("file_format", "auto", "csv | parquet | auto")
# Solo per sorgenti Logistix multi-sito:
dbutils.widgets.text("siti", "lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx", "Siti Logistix")
```
- Catalogo: `get_catalog("bronze", env)` (da `utils`). Schema: `logistica`.
- `run_date` è il nome unico della data di run su **tutti** i layer (no più `load_date`).

## 3. Convenzione path landing (OP-07 — in attesa conferma struttura Foconi)

```
{landing_base_path}/{source}-landing/{table}/YYYY/MM/DD/*.{ext}          # cnd, stat
{landing_base_path}/logistix-landing/{sito}/{table}/YYYY/MM/DD/*.{ext}   # logistix multi-sito
```
- `source` ∈ {`logistix`, `cnd`, `stat`}; il container/prefisso è `<source>-landing` (non più `landing/<source>`).
- Inserire nell'header del notebook la nota: *"Path convention pending OP-07 (struttura Foconi da confermare con Reply)."*

## 4. Colonne di metadato Bronze (aggiunte da ogni notebook)

| Colonna | Valore |
|---------|--------|
| `_bronze_load_date` | `lit(run_date).cast(date)` — data di riferimento (dal path) |
| `_bronze_insert_ts` | `current_timestamp()` — preservata negli UPDATE (delta) |
| `_source_file` | `input_file_name()` |
| `_sito_cod` | solo Logistix multi-sito: `regexp_extract(input_file_name(), '/logistix-landing/([^/]+)/', 1)` |

## 5. Le tre modalità di scrittura

### MODE A — DELTA_MERGE (transazionali / movimenti)
Il file giornaliero contiene il **delta** (record nuovi + modificati). MERGE su **chiave naturale** (senza `_bronze_load_date` nella condizione, senza partizione per data).
```python
cond = " AND ".join(f"tgt.{k} = src.{k}" for k in MERGE_KEYS)
update_set = {c: f"src.{c}" for c in bronze_df.columns if c not in MERGE_KEYS and c != "_bronze_insert_ts"}
# prima esecuzione: saveAsTable (no partizione). Poi: MERGE whenMatchedUpdate(update_set)/whenNotMatchedInsertAll
```
- `_bronze_insert_ts` escluso dall'UPDATE (conserva il first-seen).
- **Nessuna** partizione `_bronze_load_date` (la stessa chiave non deve disperdersi su più partizioni).

### MODE B — FULL_OVERWRITE (anagrafiche)
Il file giornaliero contiene lo stato **completo**. Si sovrascrive la tabella (riflette lo stato corrente, come il truncate+insert AS-IS).
```python
(bronze_df.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable(FULL_TARGET))
```
- Nessuna partizione. `_bronze_load_date` = run_date (data dello snapshot anagrafico).

### MODE C — SNAPSHOT (giacenze)
Snapshot giornaliero storicizzato: `replaceWhere` sulla data, partizionato per `_bronze_load_date`.
```python
(bronze_df.write.format("delta").mode("overwrite")
   .option("replaceWhere", f"_bronze_load_date = '{run_date}'")
   .partitionBy("_bronze_load_date").saveAsTable(FULL_TARGET))
```

## 6. Lettura file (CSV/Parquet, auto-detect)
- `file_format=auto` → rileva da `dbutils.fs.ls` (`.parquet` prima, poi `.csv`).
- CSV: `header=true`, `inferSchema=false`, separatore da concordare (OP-08; default `;` per Logistix, verificare CND/STAT), encoding UTF-8.
- Gestione "file assente": log warning + `dbutils.notebook.exit("NO_DATA")` senza errore.
- **Schema esplicito**: mantenere la `SOURCE_COLS`/`StructType` già presente in ciascun notebook (colonne reali verificate — NON modificarle, NON inventarne).

## 7. Classificazione per tabella (modalità + sorgente + path)

| Notebook | Tabella | Sistema | Path landing | MODE |
|----------|---------|---------|--------------|------|
| carichi/bronze_carichi_testate | sto_tes_carichi | logistix | logistix-landing/{sito}/sto_tes_carichi | **DELTA_MERGE** |
| carichi/bronze_carichi_dettagli | sto_righe_carico | logistix | logistix-landing/{sito}/sto_righe_carico | **DELTA_MERGE** |
| carichi/bronze_pesate | pesate | logistix | logistix-landing/{sito}/pesate | **DELTA_MERGE** |
| carichi/bronze_traccia_ce178 | tracciace178 | logistix | logistix-landing/{sito}/tracciace178 | **DELTA_MERGE** |
| carrellisti/bronze_missioni_carr | dettaglio_carr | logistix | logistix-landing/{sito}/dettaglio_carr | **DELTA_MERGE** |
| carrellisti/bronze_cartellino | cartellino | logistix | logistix-landing/{sito}/cartellino | **DELTA_MERGE** |
| giacenze/bronze_movimenti_magazzino | imbfmovim | logistix | logistix-landing/{sito}/imbfmovim | **DELTA_MERGE** (movimenti, OP-14: distinta da dettaglio_carr) |
| prep_spedizioni/bronze_prep_riepiloghi | storico_riepiloghi | **stat** | stat-landing/storico_riepiloghi | **DELTA_MERGE** (OP-16) |
| prep_spedizioni/bronze_prep_bolle_testate | testate_bolle | **stat** | stat-landing/testate_bolle | **DELTA_MERGE** (OP-16) |
| prep_spedizioni/bronze_prep_bolle_righe | storico_bolle | **stat** | stat-landing/storico_bolle | **DELTA_MERGE** (OP-16) |
| prep_spedizioni/bronze_timbrature | t_prep_sped | cnd | cnd-landing/t_prep_sped | **DELTA_MERGE** (OP-17: tab. derivata, flag) |
| stat/bronze_buoni_eco | buoni_eco | stat | stat-landing/buoni_eco | **DELTA_MERGE** (fuori core) |
| anagrafiche/bronze_carrellisti | carrellisti | logistix | logistix-landing/{sito}/carrellisti | **FULL_OVERWRITE** |
| anagrafiche/bronze_preparatori | preparatori | logistix | logistix-landing/{sito}/preparatori | **FULL_OVERWRITE** |
| anagrafiche/bronze_ricevitori | ricevitori | logistix | logistix-landing/{sito}/ricevitori | **FULL_OVERWRITE** |
| anagrafiche/bronze_spedizionieri | spedizionieri | logistix | logistix-landing/{sito}/spedizionieri | **FULL_OVERWRITE** |
| anagrafiche/bronze_struttura_mag | struttura_mag | logistix | logistix-landing/{sito}/struttura_mag | **FULL_OVERWRITE** |
| anagrafiche/bronze_corsie | corsie | logistix | logistix-landing/{sito}/corsie | **FULL_OVERWRITE** |
| anagrafiche/bronze_tabgen | tabgen | logistix | logistix-landing/{sito}/tabgen | **FULL_OVERWRITE** |
| anagrafiche/bronze_aree_merceologiche | aree_merceologiche | logistix | logistix-landing/{sito}/aree_merceologiche | **FULL_OVERWRITE** (OP-10: filtro ARM_TIPO_AREA=1 lato sorgente, da confermare) |
| anagrafiche/bronze_classe_posto_pallet | classe_posto_pallet | logistix | logistix-landing/{sito}/classe_posto_pallet | **FULL_OVERWRITE** |
| anagrafiche/bronze_pdv | t_pdv | cnd | cnd-landing/t_pdv | **FULL_OVERWRITE** |
| trasporti/bronze_vettori | t_vettori | cnd | cnd-landing/t_vettori | **FULL_OVERWRITE** |
| stat/bronze_tipo_attivita | tipo_attivita_eco | stat | stat-landing/tipo_attivita_eco | **FULL_OVERWRITE** (lookup) |
| giacenze/bronze_giacenze_snapshot | t_stock | cnd | cnd-landing/t_stock | **SNAPSHOT** |
| trasporti/bronze_trasporti | t_trasp_mtv | cnd | cnd-landing/t_trasp_mtv | **DELTA_MERGE** (area trasporti non core; flag) |

### Notebook NON conformi (JDBC) — DESCOPE/OP
`trasporti/bronze_contratti_corrieri`, `bronze_ordini_righe`, `bronze_ordini_testate`, `bronze_swap` → ancora JDBC Oracle. **Non convertiti in questa revisione** (area trasporti fuori scope core, richiede analisi sorgente dedicata). Registrati in Open Points (OP-26). Da migrare a landing o descopare.

## 8. Note di implementazione per gli sviluppatori
- Mantenere invariati gli elenchi colonna (`SOURCE_COLS`/StructType) già presenti: sono verificati sul reale, non vanno modificati.
- Uniformare header (Area/Layer/Versione 3.0.0/Data 2026-06-08/Descrizione con MODE).
- Rimuovere `load_date` → `run_date`; rimuovere `catalog`/`catalog_bronze` → `get_catalog("bronze", env)`.
- Logging con `get_logger`; gestione "no data" con `dbutils.notebook.exit`.
- Per le anagrafiche multi-sito (FULL_OVERWRITE): l'overwrite riflette l'unione dei full di tutti i siti del giorno (union dei file letti, poi overwrite unico).
