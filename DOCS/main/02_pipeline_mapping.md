# Pipeline Mapping & Runbook — Logistico 2.0

> 🧭 **Navigazione**: attività → [`acts/`](acts/) · decisioni → [`adr/`](adr/) · indice unico →
> [`15_backlog_master.md`](15_backlog_master.md). Stato di avanzamento → `sprint_agile/`.

> **SSOT:** questo file in `docs/main/` è la versione canonica e integrata.  
> Assorbe: `pipeline_mapping.md`, `Pipeline Operativa - Logistico 2.0.md`, `decision_matrix_ingestion.md`,  
> `Landing & Bronze - Revision Spec.md`, `Silver - Revision Spec.md`, `Gold - Revision Spec.md`,  
> `Workflow - Revision Spec.md`, `runbook.md`.  
> I file originali sono stati spostati in `docs/Archive/`.

**Ultimo aggiornamento:** 2026-07-02 | Pipeline validata end-to-end 2026-06-17 | Certifica wave Carichi/Prep-Sped 2026-07-02

---

## Indice

1. [Sistemi sorgente](#1-sistemi-sorgente)
2. [Architettura a layer](#2-architettura-a-layer)
3. [Pattern di ingestion — Landing](#3-pattern-di-ingestion--landing)
4. [Standard notebook Bronze](#4-standard-notebook-bronze)
5. [Inventario Bronze](#5-inventario-bronze)
6. [Standard notebook Silver](#6-standard-notebook-silver)
7. [Inventario Silver](#7-inventario-silver)
8. [Standard notebook Gold & DataMart](#8-standard-notebook-gold--datamart)
9. [Inventario Gold](#9-inventario-gold)
10. [Workflow e Scheduling](#10-workflow-e-scheduling)
11. [Flussi end-to-end per area](#11-flussi-end-to-end-per-area)
12. [Inventario tabelle per schema](#12-inventario-tabelle-per-schema)
13. [Tabelle dismesse](#13-tabelle-dismesse)
14. [Regole di layer](#14-regole-di-layer)
15. [Runbook Operativo](#15-runbook-operativo)
16. [Note operative](#16-note-operative)

---

## 1. Sistemi sorgente

| Sistema | Tipo connessione | Landing subdir | Siti / Schema |
|---------|-----------------|----------------|---------------|
| **LOGISTIX** | Oracle db-link multi-sito (`LOG_<SITO>`) | `logistix-landing/{sito}/` | 22 siti: laix, lbvx, lcax, leax, lfax, lfmx, lfqx, lfsx, lfvx, lgax, lgcx, lgnx, lgqx, lgrx, lgsx, lgvx, lgzx, lonx, losx, lslx, lsmx, lsvx |
| **STAT** | Oracle db-link unico (`STAT`) | `stat-landing/` | Schema STAT (prep spedizioni) |
| **CDT_ESTR_RAW** | Oracle diretto, schema `CDT_ESTR` | `cdt-estr-raw-landing/` | Anagrafiche locali CDT |
| **TRACK** | Oracle db-link `@TRACK` | `track-landing/` | Trasporti / vettori |

Tutte le estrazioni sono **READ-ONLY** — nessun update di flag CDC sul sorgente Oracle.

---

## 2. Architettura a layer

| Layer | Catalogo.schema | Ruolo |
|-------|-----------------|-------|
| **Bronze** | `bronze_<env>.logistica` | Copia 1:1 raw dei file landing + metadati `_bronze_*`, `_sito_estrazione`/`_sito_cod` |
| **Silver clean** | `silver_<env>.logistica` | Cleansing 1:1 (julian→date, `normalize_sito`, trim/cast, dedup) + elaborazioni intermedie (uniche, catena, s_trasp_mtv) |
| **Silver prep** | `silver_<env>.logistica_curated` | Fase 1 modellazione (join) + Fase 2 calcolo (logiche, chiavi-giorno). **Il Gold legge SOLO da qui** |
| **Gold fact** | `gold_<env>.logistica` | Fase 3: aggancio dimensioni (`surrogate_key_fallback`+`check_orphan_rate`), scrittura `F_*` e dimensioni `LU_*` |
| **Gold datamart** | `gold_<env>.logistica_dm` | Aggregati mensili `A_*` dai fact |
| **Retail master** | `bronze_<env>.condiviso` (D2) | Lookup condivise `LU_FORNITORE`, `LU_PDV`, `LU_ART_RADICE` (estratte da CDT_DW, NON ricostruite dal logistico) |

> `<env>` = `dev`/`prod`. In locale gli FQN a 3 livelli sono collassati a 2 (`silver_dev_logistica`) dal rewriter del runner.
> **Brownfield Databricks (D2 ✅ deciso 2026-07-02):** gli schemi logistici vivono nei catalog DWH esistenti; le anagrafiche condivise stanno in **`bronze_<env>.condiviso`** (schema proprio, isolamento totale). Nelle tabelle sotto, il vecchio label `cdtdw.condiviso` va letto come `bronze_<env>.condiviso` (widget default già aggiornati — DBR-02). Vedi `10_piano_migrazione_databricks.md`.

### Grafo macro di esecuzione

```
[0] LANDING (ingestion Oracle→CSV)  extract_oracle_to_landing.py  (22 siti logistix + stat + cdt_estr_raw + track)
        │
        ▼
[1] BRONZE 1:1  (tutte le aree; UPSERT transazionali / FULL anagrafiche / SNAPSHOT giacenze)
        │
        ├─────────────┬───────────────┬──────────────┬───────────────┐
        ▼             ▼               ▼              ▼               ▼
[2] DIMENSIONI   [3] CARICHI     [4] GIACENZE    [5] SPEDIZIONI   [6] TRASPORTI
   (LU_*)         (F_CARICO)     (F_GIACENZE)    (F_PREP_SPED,    (F_TRASPORTO,
        │                                          F_TURNO_*)      F_ORDINI)
        └─────────────┴───────────────┴──────────────┴───────────────┘
                                   │  (i fact agganciano le LU_*)
                                   ▼
[7] GOLD_DM aggregati A_*  (inbound, outbound, produttività, turno, stock, giacenze)
```

**Regola di precedenza:** le **dimensioni `LU_*` (fase 2) vanno costruite prima dei fact** (fase 3–6); gli **aggregati `A_*` (fase 7) per ultimi** (leggono i fact).

### Certifica & quadratura vs CDT_DW (aggiornamento 2026-07-02)

La ri-certifica di `F_CARICO` e `F_PREP_SPED` usa `scripts/quadratura/quadratura_fact.py` (confronto
parametrico sito×periodo vs CDT_DW legacy). Esiti e note aperte (dettaglio in `09_runbook_recert_carichi_prepsped.md`
e `05_open_points.md` sez. F):

- **F_CARICO** — grain **etichetta** (allineato a CDT_SA.sql); `PES_CARICO` da anagrafica
  `LU_ART_UNITA_LOGISTICA` (non dalla pesata). Gap residuo **OP-CAR-5**: il grain di
  `silver_prep_carico` è guidato dalla **pesata (INNER JOIN)** → un carico appare in Gold solo quando
  la pesata è arrivata e matcha; CDT_DW popola T_CARICO dalla catena WL (prima). Dove pesata e carico
  coesistono il match è perfetto. Decisione di design pendente (LEFT join pesata vs grain da catena WL).
- **F_PREP_SPED** — v4.0 (grain con `SEQ_PREL_PREP`, articolo radice+variante). **OP-PSP-2 risolto**:
  `DATA_PREL_INIZ` ricostruita da `LSPRL_DATA_PRELIEVO`+`LSPRL_ORA_PRELIEVO`. **OP-PSP-1 chiuso**: le
  righe senza bolla (scartate TIPO_SCAR 09/10) sono coverage aggiuntiva — CDT_DW le esclude a monte.
- **Quadratura affidabile solo su file live**: leggendo Delta con pyarrow (senza Spark) bisogna filtrare
  i parquet tombstoned via `_delta_log` (helper `live_delta_files()`), altrimenti i full_refresh gonfiano
  i conteggi. Su Databricks il problema non esiste (Spark legge il log). Vedi memoria del progetto.

---

## 3. Pattern di ingestion — Landing

### Cambio architetturale v2.0

| Aspetto | v1.x (deprecata) | v2.0 (attuale) |
|---------|-------------------|----------------|
| Modalità lettura | Pull JDBC da Oracle | Push CSV su landing zone ADLS Gen2 |
| Connettività Oracle su Databricks | Richiesta (JDBC, firewall, credenziali) | Non richiesta |
| Watermark | Colonna Oracle (es. `DATA_ESTRAZIONE_DWH`) | Path della landing zone (`YYYY/MM/DD`) |
| Partizionamento | `numPartitions` JDBC | Non applicabile (CSV già splittato per giorno) |
| Scrittura Bronze | Append-only con dedup watermark | MERGE INTO (upsert) su chiavi business |
| Formato dati | Record Oracle via driver JDBC | File CSV UTF-8, separatore `;` |

```
Sistema sorgente          Landing Zone ADLS Gen2             Bronze Delta Lake
(Logistix / STAT / CDT)       (blob container)              (Unity Catalog)

     Delta giornaliero         landing/
     in formato CSV      ────► {sistema}-landing/        ────► MERGE INTO
                                {[sito]/}                      {catalog}.logistica.{table}
                                {tabella}/
                                YYYY/MM/DD/
                                *.csv
```

### Path base e struttura directory

```
abfss://logistica@<storage_account>.dfs.core.windows.net/
  logistix-landing/
    lgax/
      sto_tes_carichi/YYYY/MM/DD/*.csv
      sto_righe_carico/YYYY/MM/DD/*.csv
      pesate/YYYY/MM/DD/*.csv
      tracciace178/YYYY/MM/DD/*.csv
      dettaglio_carr/YYYY/MM/DD/*.csv
      imbfmovim/YYYY/MM/DD/*.csv
      cartellino/YYYY/MM/DD/*.csv
      carrellisti/YYYY/MM/DD/*.csv
      preparatori/YYYY/MM/DD/*.csv
      ricevitori/YYYY/MM/DD/*.csv
      spedizionieri/YYYY/MM/DD/*.csv
      struttura_mag/YYYY/MM/DD/*.csv
      corsie/YYYY/MM/DD/*.csv
      tabgen/YYYY/MM/DD/*.csv
      aree_merceologiche/YYYY/MM/DD/*.csv
      classe_posto_pallet/YYYY/MM/DD/*.csv
      storico_riepiloghi/YYYY/MM/DD/*.csv   ← SOLO lgax (STAT)
      testate_bolle/YYYY/MM/DD/*.csv        ← SOLO lgax (STAT)
      storico_bolle/YYYY/MM/DD/*.csv        ← SOLO lgax (STAT)
    lgcx/ lcax/ lccx/ lexx/ locx/ lonx/ lscx/ lslx/ ...  (stesse cartelle, tranne le tre STAT)
  stat-landing/
    storico_riepiloghi/YYYY/MM/DD/*.csv
    testate_bolle/YYYY/MM/DD/*.csv
    storico_bolle/YYYY/MM/DD/*.csv
    storico_liste/YYYY/MM/DD/*.csv
    buoni_eco/YYYY/MM/DD/*.csv
    tipo_attivita_eco/YYYY/MM/DD/*.csv
  cdt-estr-raw-landing/
    AUTOMEZZI/YYYY/MM/DD/*.csv
    APVPUNTO_VENDITA/YYYY/MM/DD/*.csv
    ESTRAI_SPEDIZIONI/YYYY/MM/DD/*.csv
  track-landing/
    vettori/YYYY/MM/DD/*.csv
    SPEDIZIONI/YYYY/MM/DD/*.csv
```

### SLA landing zone

| Sistema | Orario push completato | Orario avvio Bronze | Finestra tolleranza |
|---------|------------------------|---------------------|---------------------|
| Logistix (tutti i siti) | 04:00 | 05:00 | 30 min (alert se landing vuota alle 05:30) |
| STAT | 03:00 | 05:00 | 30 min |
| CDT_ESTR_RAW | 03:30 | 05:00 | 30 min |
| TRACK | 03:30 | 05:00 | 30 min |

**Gestione file mancanti:** il notebook Bronze esegue un controllo preventivo `dbutils.fs.ls()`. Se la cartella è assente o non contiene CSV → `dbutils.notebook.exit("NO_DATA_IN_LANDING")` (non è un errore, ma viene loggato e monitorato separatamente dai failure reali).

### Modalità di estrazione

| Modalità | Descrizione | Filtro |
|----------|-------------|--------|
| `delta` | Finestra su colonna data (Julian Day o DATE) | `date_column >= run_date - N` |
| `full` | Snapshot completo della tabella | Nessun filtro (anagrafiche stabili) |
| `snapshot` | Full per run_date, partizionato per data | Una partizione per giorno |

### Decision Matrix — Logistix

| Tabella | Path landing | Siti | Merge keys Bronze | Modalità |
|---------|--------------|------|-------------------|----------|
| `sto_tes_carichi` | `logistix-landing/{sito}/sto_tes_carichi` | Tutti | `MAG_SITO_COD, STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO` | DELTA |
| `sto_righe_carico` | `logistix-landing/{sito}/sto_righe_carico` | Tutti | `MAG_SITO_COD, SRCAR_NRO_CARICO, SRCAR_COD_MSI, SRCAR_COD_MAGAZZINO` | DELTA |
| `pesate` | `logistix-landing/{sito}/pesate` | Tutti | `MAG_SITO_COD, PSP_NUMETIC, PSP_DATABOLLA` | DELTA |
| `tracciace178` | `logistix-landing/{sito}/tracciace178` | Tutti | `MAG_SITO_COD, CE178_NRO_ETICHETTA, CE178_NRO_CARICO` | DELTA — retention CE178 obbligatoria 5 anni, NO delete |
| `dettaglio_carr` | `logistix-landing/{sito}/dettaglio_carr` | Tutti | `MAG_SITO_COD, DTCRL_COD_CARRELLIST, DTCRL_DATA_RICH_ABB, DTCRL_ORA_RICH_ABB, DTCRL_COD_MSI` | DELTA |
| `imbfmovim` | `logistix-landing/{sito}/imbfmovim` | Tutti | `MAG_SITO_COD, IMFNUMBOL, IMFANNOBOL, IMFPRGRIF, IMFCODIMB` | DELTA (distinta da dettaglio_carr — OP-14) |
| `cartellino` | `logistix-landing/{sito}/cartellino` | Tutti | `MAG_SITO_COD, CARTE_COD_CARRELLIST, CARTE_DATA` | DELTA |
| `carrellisti` | `logistix-landing/{sito}/carrellisti` | Tutti | `MAG_SITO_COD, CRLLS_COD_CARRELLIST` | FULL |
| `preparatori` | `logistix-landing/{sito}/preparatori` | Tutti | `MAG_SITO_COD, PREP_COD_PREPARATOR` | FULL |
| `ricevitori` | `logistix-landing/{sito}/ricevitori` | Tutti | `MAG_SITO_COD, RICV_COD_RICEVITOR` | FULL |
| `spedizionieri` | `logistix-landing/{sito}/spedizionieri` | Tutti | `MAG_SITO_COD, SPE_CODICE` | FULL |
| `struttura_mag` | `logistix-landing/{sito}/struttura_mag` | Tutti | `MAG_SITO_COD, STRM_COD_MAGAZZINO, STRM_CORSIA, STRM_COLONNA, STRM_PIANO` | FULL |
| `corsie` | `logistix-landing/{sito}/corsie` | Tutti | `MAG_SITO_COD, CORSI_COD_MAGAZZINO, CORSI_CORSIA` | FULL |
| `tabgen` | `logistix-landing/{sito}/tabgen` | Tutti | `MAG_SITO_COD, TGEN_NRO_TAB, TGEN_COD_SEDE, TGEN_CHIAVE1_TAB` | FULL |
| `aree_merceologiche` | `logistix-landing/{sito}/aree_merceologiche` | Tutti | `MAG_SITO_COD, ARM_COD_AREA_MERCEOLOGICA` | FULL (filtro ARM_TIPO_AREA=1) |
| `classe_posto_pallet` | `logistix-landing/{sito}/classe_posto_pallet` | Tutti | `MAG_SITO_COD, CLPAL_COD_CLAS_POSPA` | FULL |
| `catena` | `logistix-landing/{sito}/catena` | Tutti | — | SNAPSHOT |
| `catena_esterni` | `logistix-landing/{sito}/catena_esterni` | Tutti | — | SNAPSHOT |
| `storico_riepiloghi` | `stat-landing/storico_riepiloghi` | — (STAT) | `RPLPR_SITO, RPLPR_NRO_RIEPILOGO, RPLPR_DATA_PREPARAZ` | DELTA (OP-16) |
| `testate_bolle` | `stat-landing/testate_bolle` | — (STAT) | `TEBO_SITO, TEBO_NRO_BOLLA, TEBO_DATA_BOLLA` | DELTA (OP-16) |
| `storico_bolle` | `stat-landing/storico_bolle` | — (STAT) | `BOL_SITO, BOL_NRO_BOLLA, BOL_DATA_BOLLA, BOL_NRO_RIGA` | DELTA (OP-16) |
| `storico_liste` | `stat-landing/storico_liste` | — (STAT) | `LSPRL_SITO, LSPRL_NRO_GABBIA, LSPRL_NRO_ORDINE_NEG, LSPRL_COD_NEGOZIO, LSPRL_COD_MSI, LSPRL_DATA_ORDIN_NEG, LSPRL_SEQUE_PRELIEVO, LSPRL_FLAG_SCARTATO` | DELTA |
| `t_stock` | `cnd-landing/t_stock` | — (CND) | `STKNMAG, STKCINT` | SNAPSHOT |
| `t_prep_sped` | `cnd-landing/t_prep_sped` | — (CND) | `MAG_SITO_COD, NUM_RIEP, SOCIO_COD, ART_COD` | DELTA (OP-17) |
| `t_pdv` | `cnd-landing/t_pdv` | — (CND) | `PUVCODICE` | FULL |
| `t_vettori` | `cnd-landing/t_vettori` | — (CND) | `VET_CODICE` | FULL |
| `t_trasp_mtv` | `cnd-landing/t_trasp_mtv` | — (CND) | `SP_ID, MAG_SITO_COD, DATABOLLA, NUMBOLLA` | DELTA |
| `vettori` (TRACK) | `track-landing/vettori` | — (TRACK) | — | FULL |
| `SPEDIZIONI` (TRACK) | `track-landing/SPEDIZIONI` | — (TRACK) | `SP_ID` | DELTA |
| `AUTOMEZZI` | `cdt-estr-raw-landing/AUTOMEZZI` | — (CDT) | — | FULL |
| `APVPUNTO_VENDITA` | `cdt-estr-raw-landing/APVPUNTO_VENDITA` | — (CDT) | — | FULL |
| `buoni_eco` | `stat-landing/buoni_eco` | — (STAT) | `BUONO_COD` | DELTA |
| `tipo_attivita_eco` | `stat-landing/tipo_attivita_eco` | — (STAT) | — | FULL |

---

## 4. Standard notebook Bronze

### Principi

1. **Nessun JDBC.** Il Bronze legge esclusivamente file (CSV/Parquet) dalla landing zone ADLS Gen2.
2. **Dato grezzo e unitario.** Un notebook = una tabella sorgente. Nessun JOIN, nessuna normalizzazione, nessuna unione tra tabelle. Tutto va in Silver.
3. **Tipi StringType.** In Bronze tutti i campi restano stringa (schema-on-read); i cast avvengono in Silver.
4. **Idempotenza.** Rieseguire lo stesso `run_date` non duplica né corrompe i dati.

### Widget standard

```python
dbutils.widgets.dropdown("env", "dev", ["dev", "prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
dbutils.widgets.text("landing_base_path", "abfss://logistica@<storage>.dfs.core.windows.net", "Landing base path")
dbutils.widgets.text("file_format", "auto", "csv | parquet | auto")
# Solo per sorgenti Logistix multi-sito:
dbutils.widgets.text("siti", "lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx", "Siti Logistix")
```

- Catalogo: `get_catalog("bronze", env)`. Schema: `logistica`.
- `run_date` è il nome unico della data di run su tutti i layer (non usare `load_date`).

### Colonne di metadato aggiunte

| Colonna | Valore |
|---------|--------|
| `_bronze_load_date` | `lit(run_date).cast(date)` — data di riferimento (dal path) |
| `_bronze_insert_ts` | `current_timestamp()` — preservata negli UPDATE (delta) |
| `_source_file` | `input_file_name()` |
| `_sito_cod` | solo Logistix multi-sito: `regexp_extract(input_file_name(), '/logistix-landing/([^/]+)/', 1)` |

### Tre modalità di scrittura

**MODE A — DELTA_MERGE** (transazionali / movimenti)

```python
cond = " AND ".join(f"tgt.{k} <=> src.{k}" for k in MERGE_KEYS)   # null-safe <=>
update_set = {c: f"src.{c}" for c in bronze_df.columns
              if c not in MERGE_KEYS and c != "_bronze_insert_ts"}
# _bronze_insert_ts escluso dall'UPDATE (conserva il first-seen)
# Nessuna partizione per _bronze_load_date (la stessa chiave non deve disperdersi)
```

**MODE B — FULL_OVERWRITE** (anagrafiche)

```python
(bronze_df.write.format("delta").mode("overwrite")
    .option("overwriteSchema", "true").saveAsTable(FULL_TARGET))
# Nessuna partizione. _bronze_load_date = run_date (data dello snapshot)
```

**MODE C — SNAPSHOT** (giacenze)

```python
(bronze_df.write.format("delta").mode("overwrite")
    .option("replaceWhere", f"_bronze_load_date = '{run_date}'")
    .partitionBy("_bronze_load_date").saveAsTable(FULL_TARGET))
```

### Lettura file

- `file_format=auto` → rileva da `dbutils.fs.ls` (`.parquet` prima, poi `.csv`).
- CSV: `header=true`, `inferSchema=false`, separatore `;` (Logistix), verificare CND/STAT, encoding UTF-8.
- **Schema esplicito**: mantenere la `SOURCE_COLS`/`StructType` già presente — colonne reali verificate; NON modificarle, NON inventarne.
- Gestione "file assente": log warning + `dbutils.notebook.exit("NO_DATA")` senza errore.

---

## 5. Inventario Bronze

**Regola**: 1:1 rispetto alla sorgente landing. Nessuna derivazione, nessun join.  
Aggiunge metadati `_bronze_load_date`, `_sito_estrazione`. MERGE null-safe `<=>` su chiave composita.  
Namespace: `bronze_dev.logistica.*`

### Carichi

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_carichi_testate.py` | logistix / sto_tes_carichi | `sto_tes_carichi` | DELTA_MERGE | ~1.400 righe/giorno |
| `bronze_carichi_dettagli.py` | logistix / sto_righe_carico | `sto_righe_carico` | DELTA_MERGE | ~30.000 righe/giorno |
| `bronze_pesate.py` | logistix / pesate | `pesate` | DELTA_MERGE | ~16.000 righe/giorno |
| `bronze_traccia_ce178.py` | logistix / tracciace178 | `tracciace178` | DELTA_MERGE | ~12.000 righe/giorno |

### Giacenze

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_catena.py` | logistix / catena | `catena` | SNAPSHOT | ~158.000 righe/giorno |
| `bronze_catena_esterni.py` | logistix / catena_esterni | `catena_esterni` | SNAPSHOT | ~5.300 righe/giorno |
| `bronze_movimenti_magazzino.py` | logistix / imbfmovim | `imbfmovim` | DELTA_MERGE | variabile |
| `bronze_giacenze_snapshot.py` | cnd / t_stock | `t_stock` | SNAPSHOT | ~150.000 righe (CND) |

### Prep spedizioni

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_prep_bolle_righe.py` | stat / storico_bolle | `storico_bolle` | DELTA_MERGE | ~430.000–880.000 righe/giorno |
| `bronze_prep_bolle_testate.py` | stat / testate_bolle | `testate_bolle` | DELTA_MERGE | ~2.000–9.000 righe/giorno |
| `bronze_prep_riepiloghi.py` | stat / storico_riepiloghi | `storico_riepiloghi` | DELTA_MERGE | ~9.700 righe/giorno |
| `bronze_storico_liste.py` | stat / storico_liste | `storico_liste` | DELTA_MERGE | ~198.000–270.000 righe/giorno |
| `bronze_timbrature.py` | cnd / t_prep_sped | `t_prep_sped` | DELTA_MERGE | variabile (CND) |

### Trasporti

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_spedizioni.py` | track / SPEDIZIONI | `spedizioni` | DELTA_MERGE | variabile |
| `bronze_vettori_track.py` | track / vettori | `vettori_track` | FULL_OVERWRITE | 96 righe |
| `bronze_automezzi.py` | cdt_estr_raw / AUTOMEZZI | `automezzi` | FULL_OVERWRITE | ~1.900 righe |
| `bronze_trasporti.py` | cnd / t_trasp_mtv | `t_trasp_mtv` | DELTA_MERGE | variabile (CND) |

### Carrellisti

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_cartellino.py` | logistix / cartellino | `cartellino` | DELTA_MERGE | ~180 righe/giorno |
| `bronze_missioni_carr.py` | logistix / dettaglio_carr | `dettaglio_carr` | DELTA_MERGE | ~10.000 righe/giorno |

### Anagrafiche

| Notebook | Sorgente Landing | Tabella Bronze | Modalità |
|----------|-----------------|----------------|----------|
| `bronze_struttura_mag.py` | logistix / struttura_mag | `struttura_mag` | FULL_OVERWRITE |
| `bronze_tabgen.py` | logistix / tabgen | `tabgen` | FULL_OVERWRITE |
| `bronze_carrellisti.py` | logistix / carrellisti | `carrellisti` | FULL_OVERWRITE |
| `bronze_preparatori.py` | logistix / preparatori | `preparatori` | FULL_OVERWRITE |
| `bronze_ricevitori.py` | logistix / ricevitori | `ricevitori` | FULL_OVERWRITE |
| `bronze_spedizionieri.py` | logistix / spedizionieri | `spedizionieri` | FULL_OVERWRITE |
| `bronze_corsie.py` | logistix / corsie | `corsie` | FULL_OVERWRITE |
| `bronze_aree_merceologiche.py` | logistix / aree_merceologiche | `aree_merceologiche` | FULL_OVERWRITE |
| `bronze_classe_posto_pallet.py` | logistix / classe_posto_pallet | `classe_posto_pallet` | FULL_OVERWRITE |
| `bronze_apvpunto_vendita.py` | cdt_estr_raw / APVPUNTO_VENDITA | `apvpunto_vendita` | FULL_OVERWRITE |
| `bronze_pdv.py` | cnd / t_pdv | `t_pdv` | FULL_OVERWRITE |
| `bronze_tipo_attivita.py` | stat / tipo_attivita_eco | `tipo_attivita_eco` | FULL_OVERWRITE |
| `bronze_buoni_eco.py` | stat / buoni_eco | `buoni_eco` | DELTA_MERGE |

---

## 6. Standard notebook Silver

### Principio critico — solo colonne reali (OP-27)

Il Silver è stato costruito storicamente su colonne inventate, non presenti nel Bronze reale. La regola è assoluta: ogni notebook Silver deve usare **esclusivamente** colonne presenti nel Bronze corrispondente. Prima di scrivere o modificare, leggere il notebook Bronze sorgente e prendere le colonne reali da `SOURCE_COLS`/`StructType`. Non inventare attributi (cognome/nome/contratto/ragione sociale) se non esistono.

Esempi di errori corretti:
- `silver_dim_corriere`: usare `VET_DESCRIZIONE` (non `VET_RAGIONE_SOC`)
- `silver_dim_pdv`: usare `PUVNOME` (non `PUVDESC`)
- `silver_dim_operatore` (carrellisti): `CRLLS_DES_CARRELLIST` (non cognome/nome/data_assunzione)

### Principi Silver

1. **Cleansing, non modellazione lookup.** Silver = entità di business pulite, tipizzate, deduplicate, rinominate da prefisso Oracle a nome business. I lookup `LU_*` e gli aggregati `A_*` sono artefatti del Gold.
2. **Cast espliciti** da StringType ai tipi business. Deduplica con `Window` su chiave naturale ordinando per `_bronze_insert_ts DESC`. Colonna `_silver_ts = current_timestamp()`.
3. **MERGE INTO** Silver su chiave naturale (CTAS alla prima esecuzione) per entità incrementali; **overwrite** per anagrafiche full; **replaceWhere** per snapshot (giacenze).
4. Le trasformazioni rimosse dal Bronze vanno qui: OP-12 normalizzazione articolo radice/variante; OP-15 unione operatori; OP-17 consolidamento prep_sped.

### Widget standard

```python
dbutils.widgets.dropdown("env", "dev", ["dev", "prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
```

Cataloghi: `get_catalog("bronze", env)` / `get_catalog("silver", env)`. Schema `logistica`. Usare `_bronze_insert_ts` (NON `_ingestion_timestamp`).

### Pattern di scrittura Silver

- Incrementali (transazionali): MERGE su chiave naturale (CTAS prima volta). Filtrare Bronze per `_bronze_load_date = run_date` se il Bronze è delta giornaliero.
- Anagrafiche/dimensioni logistiche: overwrite completo (riflettono lo stato corrente del Bronze full).
- Giacenze daily: `replaceWhere` su DATA_FOTO/`_bronze_load_date`.

### Dimensioni logistiche — mappatura colonne reali

**silver_dim_sito** (da `struttura_mag`)
- `SITO_COD` = distinct `MAG_SITO_COD`. `SITO_DESC`: non esiste un nome sito nel sorgente → lasciare null o derivare da `tabgen` (TGEN_NRO_TAB=7).

**silver_dim_operatore** — UNION 4 anagrafiche (OP-15), colonne reali:
- carrellisti: `CRLLS_COD_CARRELLIST`→OPERATORE_COD, `CRLLS_DES_CARRELLIST`→DESCRIZIONE, `CRLLS_FLAG_CARR_ATT`→FLG_ATTIVO, TIPO='CARRELLISTA'
- preparatori: `PREP_COD_PREPARATOR`→OPERATORE_COD, `PREP_DES_PREPARATOR`→DESCRIZIONE, `PREP_FLAG_PREP_ATT`→FLG_ATTIVO, TIPO='PREPARATORE'
- ricevitori: `RICV_COD_RICEVITOR`→OPERATORE_COD, `RICV_COGNOME`+`RICV_NOME`→DESCRIZIONE (concat), `RICV_FLAG_RICV_ATT`→FLG_ATTIVO, TIPO='RICEVITORE'
- spedizionieri: `SPE_CODICE`→OPERATORE_COD, `SPE_COGNOME`+`SPE_NOME`→DESCRIZIONE (concat), FLG_ATTIVO=null, TIPO='SPEDIZIONIERE'
- Schema target unico: OPERATORE_COD, SITO_COD, TIPO_OPERATORE, DESCRIZIONE, FLG_ATTIVO, _silver_ts. Dedup su (OPERATORE_COD, SITO_COD, TIPO_OPERATORE).

**silver_dim_corriere** (da `vettori_track`): `VET_CODICE`→CORRIERE_COD, `VET_DESCRIZIONE`→RAGIONE_SOCIALE, `VET_INDIRIZZO`→INDIRIZZO, `VET_CITTA`→CITTA, `VET_PROVINCIA`→PROVINCIA, `VET_CAP`→CAP, `VET_STATO`→FLG_ATTIVO.

**silver_dim_topografia** (da `struttura_mag`): `CELLA_COD` = concat_ws('_', MAG_SITO_COD, STRM_COD_MAGAZZINO, STRM_CORSIA, STRM_COLONNA, STRM_PIANO). Usare solo colonne STRM_ realmente presenti.

### Dimensioni master DEPRECATE (OP-02)

`silver_dim_articolo`, `silver_dim_fornitore`, `silver_dim_pdv` → marcate **DEPRECATE** (header + escluse dai workflow). Le dimensioni master sono prodotte dal flusso Retail Master Data e lette in Gold come `LU_*` da `bronze_dev.condiviso`.

### Allineamento sorgenti Bronze post-revisione

- Prep-spedizioni: leggere da `bronze.logistica.storico_riepiloghi`, `testate_bolle`, `storico_bolle` (sistema STAT) — OP-16.
- Carrellisti: `dettaglio_carr` e `imbfmovim` sono **due tabelle distinte** (OP-14).
- Giacenze: `bronze.logistica.t_stock` è uno **snapshot** → filtrare `_bronze_load_date = run_date`.

---

## 7. Inventario Silver

**Regola**: cleansing, normalizzazione sito, deduplicazione, derivazioni business (no join a dimensioni Gold).  
Namespace: `silver_dev.logistica.*` (operative) e `silver_dev.logistica_curated.*` (pronte per Gold).

### Dimensioni operative

| Notebook | Sorgente Bronze/Silver | Tabella Silver | Trasformazione |
|----------|----------------------|----------------|----------------|
| `silver_dim_sito.py` | `struttura_mag` | `silver_dev.logistica.dim_sito` | Dedup per MAG_SITO_COD, 22 righe |
| `silver_dim_topografia.py` | `struttura_mag` | `silver_dev.logistica.dim_topografia` | Dedup per SITO+COD_MAGAZZINO |
| `silver_dim_operatore.py` | `carrellisti`, `preparatori`, `ricevitori`, `spedizionieri` | `silver_dev.logistica.dim_operatore` | UNION 4 anagrafiche + self-healing NON_DEFINITO + membro ND |
| `silver_dim_corriere.py` | `vettori_track` | `silver_dev.logistica.dim_corriere` | Clean, dedup su VET_CODICE |
| `silver_dim_pdv.py` | `apvpunto_vendita` | `silver_dev.logistica.dim_pdv` | Clean 1:1 |

### Carichi

| Notebook | Sorgente Bronze | Tabella Silver | Trasformazione |
|----------|----------------|----------------|----------------|
| `silver_carichi_testate.py` | `sto_tes_carichi` | `silver_dev.logistica.carico_testata` | Clean, dedup, MERGE incrementale per run_date |
| `silver_carichi_dettagli.py` | `sto_righe_carico` | `silver_dev.logistica.carico_dettaglio` | Clean, dedup |
| `silver_pesate.py` | `pesate` | `silver_dev.logistica.pesata` | Clean, dedup |
| `silver_prep_carico.py` | `carico_testata` ⋈ `carico_dettaglio` ⋈ `pesata` | `silver_dev.logistica_curated.carico` | JOIN 3 tabelle, calcolo SCARTO_QTA, OVERWRITE dinamico per ANNO_MESE |
| `silver_traccia_ce178.py` | `tracciace178` | `silver_dev.logistica.tracciabilita_lotto` | Clean, dedup |

### Giacenze

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_catena_clean.py` | `bronze.catena` | `silver_dev.logistica.catena_clean` | Sito canonico, cast date, deriva ART_RADICE/ART_VAR, SNAPSHOT append |
| `silver_catena_esterni_clean.py` | `bronze.catena_esterni` | `silver_dev.logistica.catena_esterni_clean` | Come catena_clean, SNAPSHOT append |
| `silver_catena_unificata.py` | `catena_clean` ∪ `catena_esterni_clean` | `silver_dev.logistica.catena_unificata` | UNION + dedup ST15 (ambiguità), SNAPSHOT overwrite |
| `silver_t_stock.py` | `catena_unificata` ⋈ `struttura_mag` | `silver_dev.logistica.t_stock` | JOIN sito canonico, aggregazione picking vs scorte (ST13/14), SNAPSHOT |
| `silver_prep_giacenze.py` | `t_stock` | `silver_dev.logistica_curated.giacenze` | Dedup per chiave, SNAPSHOT overwrite per DATA_FOTO |
| `silver_giacenze_aggregata.py` | `logistica_curated.giacenze` | `silver_dev.logistica.giacenza_aggregata` | GROUP BY MAG_COD + DATA_FOTO, SNAPSHOT overwrite |

### Prep spedizioni

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_prep_riepiloghi.py` | `storico_riepiloghi` | `silver_dev.logistica.prep_riepilogo` | Clean, dedup, MERGE |
| `silver_storico_bolle_clean.py` | `storico_bolle` | `silver_dev.logistica.storico_bolle_clean` | Clean, dedup per chiave, MERGE upsert |
| `silver_storico_bolle_uniche.py` | `storico_bolle_clean` | `silver_dev.logistica.storico_bolle_uniche` | DISTINCT per bolla, MERGE upsert — DQ S7 (costanza attributi) |
| `silver_storico_liste_clean.py` | `storico_liste` | `silver_dev.logistica.storico_liste_clean` | Clean, dedup, MERGE upsert, watermark (OP-35 pilota) |
| `silver_storico_liste_uniche.py` | `storico_liste_clean` | `silver_dev.logistica.storico_liste_uniche` | DISTINCT per lista, MERGE upsert — DQ S7 |
| `silver_prep_bolle.py` | `storico_bolle_clean` ⋈ `testate_bolle` | `silver_dev.logistica.prep_bolla` | JOIN testata + righe bolle |
| `silver_timbrature_sessioni.py` | `t_prep_sped` | `silver_dev.logistica.timbratura_sessione` | Clean, calcolo DURATA_MIN (sessioni timbratura) |
| `silver_prep_sped_integrata.py` | `timbratura_sessione` ⋈ `prep_riepilogo` | `silver_dev.logistica.prep_sped_integrata` | JOIN + GROUP BY + aggregazioni (OP-17) |
| `silver_prep_turno_prep_sito.py` | `prep_riepilogo` ⋈ `prep_bolla` | `silver_dev.logistica_curated.turno_prep_sito` | GROUP BY turno/sito |
| `silver_prep_prep_sped.py` | `storico_liste_uniche` ⋈ `storico_bolle_uniche` | `silver_dev.logistica_curated.prep_sped` | JOIN, MERGE incrementale pattern #2 |

### Trasporti

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_vettori_clean.py` | `vettori_track` | `silver_dev.logistica.vettori_track_clean` | Clean, dedup, FULL OVERWRITE |
| `silver_automezzi_clean.py` | `automezzi` | `silver_dev.logistica.automezzi_clean` | Clean 1:1, FULL OVERWRITE |
| `silver_spedizioni_clean.py` | `spedizioni` | `silver_dev.logistica.spedizioni_clean` | Clean, dedup su SP_ID, MERGE |
| `silver_ordini.py` | `sto_tes_carichi` | `silver_dev.logistica.ordine` | Filtro `FLAG_TRASFERITO != 'S'` (ordini pendenti), dedup |
| `silver_trasp_mtv_build.py` | `automezzi_clean` ⋈ `spedizioni_clean` | `silver_dev.logistica.s_trasp_mtv` | Rebuild catena trasporti (sostituzione WL2) |
| `silver_prep_trasporto.py` | `spedizioni_clean` ⋈ `s_trasp_mtv` | `silver_dev.logistica_curated.trasporto` | JOIN + calcoli, UNION CONS/TRANSITO, MERGE |
| `silver_prep_ordini.py` | `silver_dev.logistica.ordine` | `silver_dev.logistica_curated.ordini` | Normalizzazione per Gold, FULL OVERWRITE |
| `silver_costo_trasporto.py` | `spedizioni_clean` ⋈ `vettori_track_clean` | `silver_dev.logistica.costo_trasporto` | Calcolo costo per movimento |

### Tracciabilità e carrellisti

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_tracciabilita_lotto.py` | `tracciace178` | `silver_dev.logistica.tracciabilita_lotto` | Aggregazione per SITO+CARICO+DATA+COD_MSI, MERGE |
| `silver_missione_carrellista.py` | `dettaglio_carr` | `silver_dev.logistica.missione_carrellista` | Clean, dedup |
| `silver_sessione_carrellista.py` | `missione_carrellista` | `silver_dev.logistica.sessione_carrellista` | Aggregazione per OPERATORE+SESSIONE |

### Tabelle t_* (interfaccia legacy CDT)

| Notebook | Sorgente | Tabella Silver |
|----------|----------|----------------|
| `silver_t_pdv.py` | `apvpunto_vendita` | `silver_dev.logistica.t_pdv` |
| `silver_t_vettori.py` | `vettori_track_clean` | `silver_dev.logistica.t_vettori` |
| `silver_t_stock.py` | `catena_unificata` ⋈ `struttura_mag` | `silver_dev.logistica.t_stock` |
| `silver_t_prep_sped.py` | `bronze.t_prep_sped` | `silver_dev.logistica.t_prep_sped` |
| `silver_t_trasp_mtv.py` | `s_trasp_mtv` | `silver_dev.logistica.t_trasp_mtv` |

---

## 8. Standard notebook Gold & DataMart

### Regole di naming (OP-06)

- **Lookup/dimensioni → `LU_*`** (NON `dim_*`)
- **Aggregati → `A_*`** (NON `dm_*`)
- **Fact → `F_*`** (invariato)
- Schemi: `gold_prod.logistica` per `LU_*` logistiche e `F_*`; `gold_prod.logistica_dm` per `A_*`.
- Le lookup master Retail si leggono da `gold_prod.condiviso` (placeholder widget `retail_master_schema`).

### Principio colonne reali (OP-27)

Il Gold va costruito **esclusivamente sulle colonne reali del Silver corretto**. Leggere i notebook Silver sorgente per i nomi esatti. Chiavi naturali string (no surrogate ID numerici). Dove un lookup master non è disponibile (OP-02), portare la chiave naturale e lasciare la join master opzionale/commentata.

### Widget standard Gold

```python
dbutils.widgets.dropdown("env", "dev", ["dev", "prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
dbutils.widgets.text("retail_master_schema", "gold_prod.condiviso", "Retail master schema (OP-02)")
```

Pattern: `replaceWhere` su partizione (ANNO_MESE o data) per idempotenza. `DWH_UPDATED_AT = current_timestamp()`.

### Lookup logistiche da costruire (`LU_*`)

| Target | Da Silver | Chiave |
|--------|-----------|--------|
| `LU_SITO` | `dim_sito` | SITO_COD |
| `LU_OPERATORE` | `dim_operatore` | OPERATORE_COD + SITO_COD + TIPO_OPERATORE |
| `LU_CORRIERE` | `dim_corriere` | CORRIERE_COD |
| `LU_TOPOGRAFIA` | `dim_topografia` | CELLA_COD |
| `LU_AREA_MERCL_LOGIS` | `bronze.aree_merceologiche` | COD_AREA_MERC |

### Fact — specifiche

**F_CARICO** — grain: riga dettaglio carico; silver: `logistica_curated.carico`; misure: QTA_ORDINATA, NRO_PZ_CARICATI, QTA_UF_RILEVATA, SCARTO_QTA, PESO_LORDO, PESO_MEDIO, NRO_COLLI; partizione ANNO_MESE.

**F_GIACENZE_DAILY** — grain: DATA_FOTO+ART_COD_INTERNO+MAG_COD; replaceWhere su DATA_FOTO.

**F_PREP_SPED** — grain: riepilogo per operatore/giorno; misure reali: TOT_CARTONI, TOT_CARTONI_PREP, NUM_PREPARATI, GABBIE_PREPARATE; PRODUTTIVITA su CARTONI (non colli); **regola 30 min attrezzaggio**: Window per (PREPARATORE_COD, DATA_PREPARAZ, SITO_COD) ordinata per ORA_INIZIO_PREP — prima sessione del giorno ORE_PRODUTTIVE = max(0, ORE_LAVORATE - 0.5); partizione DATA_PREPARAZ.

**F_MOVIMENTAZIONE_CARRELLISTI** — grain: carrellista/giorno/sito; sessione + missioni aggregate; partizione DATA_PRESENZA.

**F_ORDINI** — grain: ordine/carico; da `silver_dev.logistica.ordine`; stato "non chiuso" = proxy FLAG_TRASFERITO!='S'.

**F_TRASPORTO** — grain: trasporto/bolla; area non core (flag); partizione DATA_BOLLA.

**F_TRACCIABILITA_LOTTI** — grain: lotto/articolo; colonne: NUM_ETICHETTE, NUM_ANNULLATE, NUM_TRASFERITE_STAT, TASSO_ANNULLAMENTO; partizione ANNO_MESE.

### Aggregati DataMart (`A_*`, schema `gold_prod.logistica_dm`)

Sorgente = SEMPRE fact Gold (no Silver, no trasformazioni: solo GROUP BY + filtri + funzioni aggregate). replaceWhere su ANNO_MESE.

| Target | Era | Sorgente fact | Grain |
|--------|-----|---------------|-------|
| `A_INBOUND_MENSILE` | gold_a_inbound_mensile | F_CARICO | FORNITORE_COD+SITO_COD+ANNO_MESE |
| `A_GIACENZE_MONTHLY` | gold_dm_giacenze_monthly | F_GIACENZE_DAILY | ART_RADICE+MAG_COD+ANNO_MESE |
| `A_STOCK_MENSILE` | gold_a_stock_mensile | A_GIACENZE_MONTHLY | ART_RADICE+MAG_COD+ANNO_MESE |
| `A_OUTBOUND_MENSILE` | gold_a_outbound_mensile | F_ORDINI (+F_TRASPORTO) | SITO_COD+CORRIERE_COD+ANNO_MESE |
| `A_PRODUTTIVITA_MENSILE` | gold_a_produttivita_mensile | F_TURNO_PREP_SITO | SITO_COD+ANNO_MESE |
| `A_TURNO_PREP_SITO` | gold_dm_turno_prep_sito | F_TURNO_PREP_SITO | SITO_COD+DATA_PREPARAZ |

### KPI SQL (`sql/kpi/*.sql`)

Le 10 view usano `LU_*` (non `dim_*`), `A_*` (non `dm_*`), misure reali (cartoni/quintali, QTA_PEZZI, scarto su dettaglio). Dove un KPI si basava su un dato inesistente (es. colli/ora, ORE_PRODUTTIVE carrellisti, costo trasporto reale), riformulare sul dato reale o aggiungere commento `-- PLACEHOLDER/OP`. View in `gold_prod.logistica.kpi_*`.

---

## 9. Inventario Gold

**Regola**: join a dimensioni lookup (LU_*), calcolo FK surrogate (`surrogate_key_fallback`), scrittura fact/aggregati.  
Namespace: `gold_dev.logistica.*` (fact + lookup) e `gold_dev.logistica_dm.*` (aggregati datamart).

### Lookup condivise (da CDT_DW)

| Notebook | Sorgente | Gold Target | Righe tipiche |
|----------|----------|-------------|---------------|
| `gold_lu_from_cdtdw.py` | `bronze_dev.condiviso.*` | `gold_dev.logistica.LU_ART_RADICE` | 693.879 |
| | | `gold_dev.logistica.LU_FORNITORE` | 11.478 |
| | | `gold_dev.logistica.LU_PDV` | 4.185 |
| | | `gold_dev.logistica.LU_GIORNO` | 8.035 |
| | | `gold_dev.logistica.LU_MESE` | 264 |

### Lookup logistica

| Notebook | Sorgente Silver | Gold Target | Righe tipiche |
|----------|----------------|-------------|---------------|
| `gold_dim_sito.py` | `silver_dev.logistica.dim_sito` | `gold_dev.logistica.LU_SITO` | 22 |
| `gold_dim_operatore.py` | `silver_dev.logistica.dim_operatore` | `gold_dev.logistica.LU_OPERATORE` | ~16.082 (incl. membro ND) |
| `gold_dim_corriere.py` | `silver_dev.logistica.dim_corriere` | `gold_dev.logistica.LU_CORRIERE` | 96 |
| `gold_dim_topografia.py` | `silver_dev.logistica.dim_topografia` | `gold_dev.logistica.LU_TOPOGRAFIA` | ~379.711 |
| `gold_dim_struttura_merceologica.py` | `silver_dev.logistica.aree_merceologiche` | `gold_dev.logistica.LU_AREA_MERCL_LOGIS` | 19 |

### Fact tables

| Notebook | Sorgente Silver | Gold Target | Grain | Partizione | Orphan rate |
|----------|----------------|-------------|-------|------------|-------------|
| `gold_f_carico.py` | `logistica_curated.carico` | `F_CARICO` | 1 riga = dettaglio carico | ANNO_MESE | 0.0% |
| `gold_f_prep_sped.py` | `logistica_curated.prep_sped` | `F_PREP_SPED` | SITO + RIEPILOGO_NRO + OPERATORE | — | 0.0% |
| `gold_f_turno_prep_sito.py` | `logistica_curated.turno_prep_sito` | `F_TURNO_PREP_SITO` | SITO + DATA + TURNO | — | 0.0% |
| `gold_f_trasporto.py` | `logistica_curated.trasporto` | `F_TRASPORTO` | 1 riga = movimento | GIORNO_BOLLA_SPED_ID | 0.0% |
| `gold_f_ordini.py` | `logistica_curated.ordini` | `F_ORDINI` | 1 riga = ordine | — | 0.0% |
| `gold_f_giacenze_daily.py` | `logistica_curated.giacenze` | `F_GIACENZE_DAILY` | DATA_FOTO + ART + MAG | DATA_FOTO | 0.0% |
| `gold_f_tracciabilita_lotti.py` | `silver_dev.logistica.tracciabilita_lotto` | `F_TRACCIABILITA_LOTTI` | CARICO + LOTTO + DATA | ANNO_MESE | — |
| `gold_f_movimentazione_carrellisti.py` | `silver_dev.logistica.missione_carrellista` | `F_MOVIMENTAZIONE_CARRELLISTI` | 1 riga = missione | DATA_PRESENZA | — |
| `gold_late_arriving_handler.py` | `F_CARICO` (finestra 90gg) | — | Handler late-arriving | — | — |
| `gold_lad_resolver.py` *(maintenance)* | Qualsiasi fact con FK=-1 | — | Re-risoluzione generica FK=-1 via `<dim>_COD_NAT` — widget: fact_table/env/dry_run | — | — |

### Aggregati datamart

| Notebook | Sorgente Gold | DM Target | Grain |
|----------|--------------|-----------|-------|
| `gold_a_inbound_mensile.py` | `F_CARICO` | `A_INBOUND_MENSILE` | FORNITORE + SITO + ANNO_MESE |
| `gold_a_outbound_mensile.py` | `F_ORDINI` ⋈ `F_TRASPORTO` (full outer) | `A_OUTBOUND_MENSILE` | SITO_COD+CORRIERE_COD+ANNO_MESE |
| `gold_a_stock_mensile.py` | `A_GIACENZE_MONTHLY` (DM→DM passthrough) | `A_STOCK_MENSILE` | ART_RADICE+MAG_COD+ANNO_MESE |
| `gold_a_produttivita_mensile.py` | `F_TURNO_PREP_SITO` | `A_PRODUTTIVITA_MENSILE` | SITO_COD+ANNO_MESE |
| `gold_dm_giacenze_monthly.py` | `F_GIACENZE_DAILY` | `A_GIACENZE_MONTHLY` | MAG + ANNO_MESE |
| `gold_dm_turno_prep_sito.py` | `F_TURNO_PREP_SITO` | `A_TURNO_PREP_SITO` | SITO + DATA + TURNO |

---

## 10. Workflow e Scheduling

### Panoramica scheduling giornaliero

```
00:30  wf_landing_ingestion  ─── CND + STAT (Bronze)
01:00  wf_dim_refresh        ─── Dimensioni Silver+Gold (LU_*)
02:00  wf_carichi            ─── Bronze + Silver + Gold F_CARICO
03:30  wf_giacenze           ─── Silver + Gold F_GIACENZE
04:30  wf_prep_sped          ─── Bronze carr. + Silver + Gold F_PREP_SPED
05:00  wf_trasporti          ─── Silver + Gold F_ORDINI + F_TRASPORTO
05:30  wf_wave_e             ─── CE178 (stub, compreso in carichi)
06:00  wf_datamart           ─── Aggregati A_*
06:00  wf_checks_daily       ─── Quadratura KPI + DQ gold
07:00  wf_giacenze_monthly   ─── [1° del mese] aggregazione mensile stock
07:00  wf_dq_report_weekly   ─── [lunedì] report DQ settimanale
```

| Workflow | Schedule | Durata stimata | SLA completamento |
|----------|----------|----------------|-------------------|
| `wf_bronze_all_daily` | 03:00 | 25 min | 03:30 |
| `wf_silver_all_daily` | 03:30 | 35 min | 04:15 |
| `wf_gold_all_daily` | 04:15 | 30 min | 04:50 |
| `wf_checks_daily` | 04:50 | 20 min | 05:15 |
| `wf_giacenze_monthly` | 1° del mese 07:00 | 45 min | 07:50 |
| `wf_compliance_ce178_alert` | 06:00 | 5 min | 06:10 |
| `wf_dq_report_weekly` | Lunedì 07:00 | 20 min | 07:25 |

### Parametri standard DAB (Revision Spec v3.0.0)

Tutti i workflow devono usare:
- `env` (dev/prod) — propagato a tutti i task
- `run_date` (YYYY-MM-DD, default `{{job.start_time.iso_date}}`) — sostituisce il vecchio `load_date`
- `landing_base_path` (solo Bronze) — pattern `<source>-landing` (OP-07)
- `file_format` (solo Bronze) — `auto`/`csv`/`parquet`
- `siti` (solo Bronze Logistix multi-sito) — comma-separated
- `retail_master_schema` (solo Gold) — placeholder OP-02
- `max_concurrent_runs: 1` su tutti i workflow (idempotenza)

Eliminare: `load_date`, `catalog_bronze`/`catalog_silver`/`catalog_gold` (i cataloghi derivano da `get_catalog(layer, env)` dentro i notebook).

### Mappatura workflow → notebook (generata dai YML — ACT_9014)

> ⚙️ **Sezione generata**: rispecchia i `workflows/*.yml` reali. Il DAG è **derivato dal grafo
> read/write dei notebook** (ADR-0019), non scritto a mano; il guardrail
> `tests/test_workflows_alignment.py` impedisce che doc, YML e notebook ridivergano.
>
> **DQ gate (ACT_9010)**: i workflow che producono Gold terminano con il task `dq_gate`
> (`notebooks/dq/dq_gate.py`): applica `ACCEPTANCE_REGISTRY`, persiste gli esiti in
> `config_<env>.logistica_etl.dq_results` e blocca il run sui check BLOCKING (ADR-0014).
>
> **Dipendenze cross-workflow** (es. dimensioni ← bronze anagrafiche) non sono esprimibili con
> `depends_on` tra job distinti: sono garantite dagli **schedule sfalsati**.


**`logistica_landing_ingestion`** (00:30) — Bronze anagrafiche condivise + STAT — servono al `dim_refresh` (01:00)

| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_aree_merceologiche` | `notebooks/bronze/anagrafiche/bronze_aree_merceologiche` | — |
| `bronze_carrellisti` | `notebooks/bronze/anagrafiche/bronze_carrellisti` | — |
| `bronze_classe_posto_pallet` | `notebooks/bronze/anagrafiche/bronze_classe_posto_pallet` | — |
| `bronze_corsie` | `notebooks/bronze/anagrafiche/bronze_corsie` | — |
| `bronze_preparatori` | `notebooks/bronze/anagrafiche/bronze_preparatori` | — |
| `bronze_ricevitori` | `notebooks/bronze/anagrafiche/bronze_ricevitori` | — |
| `bronze_spedizionieri` | `notebooks/bronze/anagrafiche/bronze_spedizionieri` | — |
| `bronze_struttura_mag` | `notebooks/bronze/anagrafiche/bronze_struttura_mag` | — |
| `bronze_tabgen` | `notebooks/bronze/anagrafiche/bronze_tabgen` | — |
| `bronze_apvpunto_vendita` | `notebooks/bronze/prep_spedizioni/bronze_apvpunto_vendita` | — |
| `bronze_artdgene` | `notebooks/bronze/prep_spedizioni/bronze_artdgene` | — |
| `bronze_buoni_eco` | `notebooks/bronze/stat/bronze_buoni_eco` | — |
| `bronze_tipo_attivita` | `notebooks/bronze/stat/bronze_tipo_attivita` | — |

**`logistica_dim_refresh`** (01:00) — Anagrafiche `LU_*` da CDT_DW + dimensioni Silver → Gold

| task_key | notebook | depends_on |
|----------|----------|------------|
| `silver_dim_articolo` | `notebooks/silver/dimensioni/silver_dim_articolo` | — |
| `silver_dim_corriere` | `notebooks/silver/dimensioni/silver_dim_corriere` | — |
| `silver_dim_fornitore` | `notebooks/silver/dimensioni/silver_dim_fornitore` | — |
| `silver_dim_operatore` | `notebooks/silver/dimensioni/silver_dim_operatore` | — |
| `silver_dim_pdv` | `notebooks/silver/dimensioni/silver_dim_pdv` | — |
| `silver_dim_sito` | `notebooks/silver/dimensioni/silver_dim_sito` | — |
| `silver_dim_topografia` | `notebooks/silver/dimensioni/silver_dim_topografia` | — |
| `gold_lu_from_cdtdw` | `notebooks/gold/condiviso/gold_lu_from_cdtdw` | — |
| `gold_dim_articolo` | `notebooks/gold/dimensioni/gold_dim_articolo` | — |
| `gold_dim_calendario` | `notebooks/gold/dimensioni/gold_dim_calendario` | — |
| `gold_dim_corriere` | `notebooks/gold/dimensioni/gold_dim_corriere` | `silver_dim_corriere` |
| `gold_dim_fornitore` | `notebooks/gold/dimensioni/gold_dim_fornitore` | — |
| `gold_dim_operatore` | `notebooks/gold/dimensioni/gold_dim_operatore` | `silver_dim_operatore` |
| `gold_dim_pdv` | `notebooks/gold/dimensioni/gold_dim_pdv` | — |
| `gold_dim_sito` | `notebooks/gold/dimensioni/gold_dim_sito` | `silver_dim_sito` |
| `gold_dim_struttura_merceologica` | `notebooks/gold/dimensioni/gold_dim_struttura_merceologica` | — |
| `gold_dim_topografia` | `notebooks/gold/dimensioni/gold_dim_topografia` | `silver_dim_topografia` |

**`logistica_carichi`** (02:00) — Wave A Carichi + tracciabilità CE178

| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_carichi_dettagli` | `notebooks/bronze/carichi/bronze_carichi_dettagli` | — |
| `bronze_carichi_testate` | `notebooks/bronze/carichi/bronze_carichi_testate` | — |
| `bronze_pesate` | `notebooks/bronze/carichi/bronze_pesate` | — |
| `bronze_traccia_ce178` | `notebooks/bronze/carichi/bronze_traccia_ce178` | — |
| `silver_carichi_dettagli` | `notebooks/silver/carichi/silver_carichi_dettagli` | `bronze_carichi_dettagli` |
| `silver_carichi_testate` | `notebooks/silver/carichi/silver_carichi_testate` | `bronze_carichi_testate` |
| `silver_pesate` | `notebooks/silver/carichi/silver_pesate` | `bronze_pesate` |
| `silver_prep_carico` | `notebooks/silver/carichi/silver_prep_carico` | `silver_carichi_dettagli`, `silver_carichi_testate`, `silver_pesate` |
| `silver_traccia_ce178` | `notebooks/silver/carichi/silver_traccia_ce178` | `bronze_traccia_ce178` |
| `silver_tracciabilita_lotto` | `notebooks/silver/tracciabilita/silver_tracciabilita_lotto` | `bronze_traccia_ce178` |
| `gold_f_carico` | `notebooks/gold/carichi/gold_f_carico` | `silver_prep_carico` |
| `gold_late_arriving_handler` | `notebooks/gold/carichi/gold_late_arriving_handler` | `silver_prep_carico` |
| `gold_f_tracciabilita_lotti` | `notebooks/gold/tracciabilita/gold_f_tracciabilita_lotti` | `silver_tracciabilita_lotto` |
| `dq_gate` | `notebooks/dq/dq_gate` | `gold_f_carico`, `gold_late_arriving_handler`, `gold_f_tracciabilita_lotti` |

**`logistica_giacenze`** (03:30) — Wave B Giacenze (ordine catena → t_stock → prep, OP-29)

| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_catena` | `notebooks/bronze/giacenze/bronze_catena` | — |
| `bronze_catena_esterni` | `notebooks/bronze/giacenze/bronze_catena_esterni` | — |
| `bronze_giacenze_snapshot` | `notebooks/bronze/giacenze/bronze_giacenze_snapshot` | — |
| `bronze_movimenti_magazzino` | `notebooks/bronze/giacenze/bronze_movimenti_magazzino` | — |
| `silver_t_stock` | `notebooks/silver/cdt_estr/silver_t_stock` | `silver_catena_unificata` |
| `silver_catena_clean` | `notebooks/silver/giacenze/silver_catena_clean` | `bronze_catena` |
| `silver_catena_esterni_clean` | `notebooks/silver/giacenze/silver_catena_esterni_clean` | `bronze_catena_esterni` |
| `silver_catena_unificata` | `notebooks/silver/giacenze/silver_catena_unificata` | `silver_catena_clean`, `silver_catena_esterni_clean` |
| `silver_giacenze_aggregata` | `notebooks/silver/giacenze/silver_giacenze_aggregata` | `silver_prep_giacenze` |
| `silver_prep_giacenze` | `notebooks/silver/giacenze/silver_prep_giacenze` | `bronze_giacenze_snapshot`, `silver_t_stock` |
| `gold_f_giacenze_daily` | `notebooks/gold/giacenze/gold_f_giacenze_daily` | `silver_prep_giacenze` |
| `dq_gate` | `notebooks/dq/dq_gate` | `gold_f_giacenze_daily` |

**`logistica_prep_sped`** (04:30) — Wave C Prep Spedizioni + carrellisti (Wave E)

| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_cartellino` | `notebooks/bronze/carrellisti/bronze_cartellino` | — |
| `bronze_missioni_carr` | `notebooks/bronze/carrellisti/bronze_missioni_carr` | — |
| `bronze_prep_bolle_righe` | `notebooks/bronze/prep_spedizioni/bronze_prep_bolle_righe` | — |
| `bronze_prep_bolle_testate` | `notebooks/bronze/prep_spedizioni/bronze_prep_bolle_testate` | — |
| `bronze_prep_riepiloghi` | `notebooks/bronze/prep_spedizioni/bronze_prep_riepiloghi` | — |
| `bronze_storico_liste` | `notebooks/bronze/prep_spedizioni/bronze_storico_liste` | — |
| `bronze_timbrature` | `notebooks/bronze/prep_spedizioni/bronze_timbrature` | — |
| `silver_prep_prep_sped` | `notebooks/silver/prep_spedizioni/silver_prep_prep_sped` | — |
| `silver_prep_riepiloghi` | `notebooks/silver/prep_spedizioni/silver_prep_riepiloghi` | `bronze_prep_riepiloghi` |
| `silver_prep_turno_prep_sito` | `notebooks/silver/prep_spedizioni/silver_prep_turno_prep_sito` | `silver_prep_riepiloghi` |
| `silver_storico_bolle_clean` | `notebooks/silver/prep_spedizioni/silver_storico_bolle_clean` | `bronze_prep_bolle_righe` |
| `silver_storico_bolle_uniche` | `notebooks/silver/prep_spedizioni/silver_storico_bolle_uniche` | `silver_storico_bolle_clean` |
| `silver_storico_liste_clean` | `notebooks/silver/prep_spedizioni/silver_storico_liste_clean` | `bronze_storico_liste` |
| `silver_storico_liste_uniche` | `notebooks/silver/prep_spedizioni/silver_storico_liste_uniche` | `silver_storico_liste_clean` |
| `silver_missione_carrellista` | `notebooks/silver/tracciabilita/silver_missione_carrellista` | `bronze_missioni_carr` |
| `silver_sessione_carrellista` | `notebooks/silver/tracciabilita/silver_sessione_carrellista` | `bronze_cartellino` |
| `gold_f_movimentazione_carrellisti` | `notebooks/gold/carrellisti/gold_f_movimentazione_carrellisti` | `silver_missione_carrellista`, `silver_sessione_carrellista` |
| `gold_f_prep_sped` | `notebooks/gold/prep_spedizioni/gold_f_prep_sped` | `silver_prep_prep_sped` |
| `gold_f_turno_prep_sito` | `notebooks/gold/prep_spedizioni/gold_f_turno_prep_sito` | `silver_prep_turno_prep_sito` |
| `dq_gate` | `notebooks/dq/dq_gate` | `gold_f_movimentazione_carrellisti`, `gold_f_prep_sped`, `gold_f_turno_prep_sito` |

**`logistica_trasporti`** (05:00) — Wave D Trasporti/Ordini

| task_key | notebook | depends_on |
|----------|----------|------------|
| `bronze_automezzi` | `notebooks/bronze/trasporti/bronze_automezzi` | — |
| `bronze_spedizioni` | `notebooks/bronze/trasporti/bronze_spedizioni` | — |
| `bronze_trasporti` | `notebooks/bronze/trasporti/bronze_trasporti` | — |
| `bronze_vettori` | `notebooks/bronze/trasporti/bronze_vettori` | — |
| `bronze_vettori_track` | `notebooks/bronze/trasporti/bronze_vettori_track` | — |
| `silver_t_vettori` | `notebooks/silver/cdt_estr/silver_t_vettori` | — |
| `silver_automezzi_clean` | `notebooks/silver/trasporti/silver_automezzi_clean` | `bronze_automezzi` |
| `silver_ordini` | `notebooks/silver/trasporti/silver_ordini` | — |
| `silver_prep_ordini` | `notebooks/silver/trasporti/silver_prep_ordini` | `silver_ordini` |
| `silver_prep_trasporto` | `notebooks/silver/trasporti/silver_prep_trasporto` | `silver_spedizioni_clean` |
| `silver_spedizioni_clean` | `notebooks/silver/trasporti/silver_spedizioni_clean` | `bronze_spedizioni` |
| `silver_vettori_clean` | `notebooks/silver/trasporti/silver_vettori_clean` | — |
| `gold_f_ordini` | `notebooks/gold/trasporti/gold_f_ordini` | `silver_prep_ordini` |
| `gold_f_trasporto` | `notebooks/gold/trasporti/gold_f_trasporto` | `silver_prep_trasporto` |
| `dq_gate` | `notebooks/dq/dq_gate` | `gold_f_ordini`, `gold_f_trasporto` |

**`logistica_aggregati`** (06:00) — LAD resolver (OP-32 L-03) → DataMart `A_*`

| task_key | notebook | depends_on |
|----------|----------|------------|
| `lad_f_carico` | `notebooks/gold/maintenance/gold_lad_resolver` | — |
| `lad_f_prep_sped` | `notebooks/gold/maintenance/gold_lad_resolver` | — |
| `lad_f_turno_prep_sito` | `notebooks/gold/maintenance/gold_lad_resolver` | — |
| `lad_f_trasporto` | `notebooks/gold/maintenance/gold_lad_resolver` | — |
| `lad_f_ordini` | `notebooks/gold/maintenance/gold_lad_resolver` | — |
| `gold_a_inbound_mensile` | `notebooks/gold/aggregati/gold_a_inbound_mensile` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `gold_a_outbound_mensile` | `notebooks/gold/aggregati/gold_a_outbound_mensile` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `gold_a_produttivita_mensile` | `notebooks/gold/aggregati/gold_a_produttivita_mensile` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `gold_a_stock_mensile` | `notebooks/gold/aggregati/gold_a_stock_mensile` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `gold_dm_giacenze_monthly` | `notebooks/gold/aggregati/gold_dm_giacenze_monthly` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `gold_dm_turno_prep_sito` | `notebooks/gold/aggregati/gold_dm_turno_prep_sito` | `lad_f_carico`, `lad_f_prep_sped`, `lad_f_turno_prep_sito`, `lad_f_trasporto`, `lad_f_ordini` |
| `dq_gate` | `notebooks/dq/dq_gate` | `gold_a_inbound_mensile`, `gold_a_outbound_mensile`, `gold_a_produttivita_mensile`, `gold_a_stock_mensile`, `gold_dm_giacenze_monthly`, `gold_dm_turno_prep_sito` |

**Totale: 7 workflow, 103 task.** Notebook non orchestrati (deliberato, allow-list in
`tests/test_workflows_alignment.py`): `bronze_swap`, `bronze_vettori_locale`, `silver_trasporti`,
`silver_t_trasp_mtv`, `silver_prep_bolle`, `gold_f_giacenze_monthly`.

---

## 11. Flussi end-to-end per area

### Grafo dipendenze dettagliato

**3.1 Dimensioni (LU_*)**
```
bronze: struttura_mag, tabgen, corsie, aree_merceologiche, carrellisti, preparatori,
        vettori(track), apvpunto_vendita
   ▼ silver_dim_sito / _operatore / _corriere / _topografia
   ▼ gold_dim_sito / _operatore / _corriere / _topografia / _struttura_merceologica
          → LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA, LU_AREA_MERCL_LOGIS
(parallelo) Retail master: bronze_dev.condiviso.LU_FORNITORE / LU_PDV / LU_ART_RADICE
```

**3.2 Carichi → F_CARICO**
```
bronze_carichi_testate (sto_tes_carichi)  ─┐
bronze_carichi_dettagli (sto_righe_carico) ├──▶ silver_carichi_*
bronze_pesate (pesate)                    ─┘
                                              ▼ silver_prep_carico → logistica_curated.carico
                                              ▼ gold_f_carico → F_CARICO (+gold_late_arriving)
```

**3.3 Giacenze/Stock → F_GIACENZE_DAILY**
```
bronze_catena (SNAPSHOT) ─┬─▶ silver_catena_clean
bronze_catena_esterni    ─┘   silver_catena_esterni_clean
                                   ▼ silver_catena_unificata (UNION + dedup ST15)
    bronze_struttura_mag ──────▶       ▼ silver_t_stock (join struttura_mag)
                                            ▼ silver_prep_giacenze → logistica_curated.giacenze
                                                ▼ gold_f_giacenze_daily → F_GIACENZE_DAILY
```

**3.4 Spedizioni → F_PREP_SPED + F_TURNO_PREP_SITO**
```
bronze_storico_liste      ─┬─▶ silver_storico_liste_clean
bronze_prep_bolle_righe   ─┤   silver_storico_bolle_clean
bronze_prep_riepiloghi    ─┘       ▼ silver_storico_liste_uniche / _bolle_uniche (GROUP BY 8 chiavi)
                                       ▼ silver_prep_prep_sped → logistica_curated.prep_sped
                                           ▼ gold_f_prep_sped → F_PREP_SPED
              silver_prep_riepiloghi ──▶ silver_prep_turno_prep_sito → logistica_curated.turno_prep_sito
                                           ▼ gold_f_turno_prep_sito → F_TURNO_PREP_SITO
```

**3.5 Trasporti → F_TRASPORTO + F_ORDINI**
```
bronze_spedizioni (SPEDIZIONI@TRACK) ─▶ silver_spedizioni_clean
bronze_automezzi                     ─▶ silver_automezzi_clean
                                             ▼ silver_trasp_mtv_build → s_trasp_mtv (rebuild WL2)
                                                 ▼ silver_prep_trasporto → logistica_curated.trasporto
                                                     ▼ gold_f_trasporto → F_TRASPORTO
bronze_carichi_testate (sto_tes_carichi) ─▶ silver_ordini → silver_prep_ordini → gold_f_ordini → F_ORDINI
```

**3.6 Fatti minori**
```
bronze carrellisti/cartellino/dettaglio_carr → silver sessione/missione_carrellista
        → gold_f_movimentazione_carrellisti → F_MOVIMENTAZIONE_CARRELLISTI
bronze tracciace178 → silver tracciabilita_lotto → gold_f_tracciabilita_lotti → F_TRACCIABILITA_LOTTI
```

### Flussi con volumi

**Carichi (Inbound)**
```
Oracle LOGISTIX (22 siti) → Landing logistix-landing/{sito}/
      ▼ Bronze: sto_tes_carichi / sto_righe_carico / pesate  (~1.400/30.000/16.000 righe/g)
      ▼ Silver clean: carico_testata / carico_dettaglio / pesata
      ▼ Silver prep: logistica_curated.carico  (~44.700 righe/mese)
      ▼ Gold: F_CARICO  [grain: dettaglio carico, part. ANNO_MESE]
      ▼ DM: A_INBOUND_MENSILE  (~1.854 righe)
```

**Giacenze (Stock)**
```
Oracle LOGISTIX (22 siti) → Landing snapshot giornaliero
      ▼ Bronze: catena / catena_esterni  (~163.000 righe/g)
      ▼ Silver: catena_clean → catena_unificata → t_stock → logistica_curated.giacenze  (~54.700 righe)
      ▼ Gold: F_GIACENZE_DAILY  [grain: DATA_FOTO + ART + MAG]
      ▼ DM: A_GIACENZE_MONTHLY / A_STOCK_MENSILE  (~54.961 righe)
```

**Prep spedizioni (Fulfillment)**
```
Oracle STAT → Landing stat-landing/
      ▼ Bronze: storico_riepiloghi / storico_bolle / storico_liste
      ▼ Silver: storico_bolle_clean → storico_bolle_uniche (~428.000)
                storico_liste_clean → storico_liste_uniche (~197.000)
      ▼ Silver prep: logistica_curated.prep_sped
      ▼ Gold: F_PREP_SPED + F_TURNO_PREP_SITO
```

**Trasporti (Outbound)**
```
Oracle TRACK → Landing track-landing/
      ▼ Bronze: spedizioni / vettori_track
      ▼ Silver: spedizioni_clean + s_trasp_mtv → logistica_curated.trasporto  (~40.900 righe)
      ▼ Gold: F_TRASPORTO [grain: movimento] + F_ORDINI [grain: ordine]
      ▼ DM: A_OUTBOUND_MENSILE  (~129 righe)
```

**Tracciabilità lotti (CE178)**
```
Oracle LOGISTIX → Bronze tracciace178 (~12.000 righe/g)
      ▼ Silver: tracciabilita_lotto (~8.800 lotti)
      ▼ Gold: F_TRACCIABILITA_LOTTI [part. ANNO_MESE]
```

**Carrellisti**
```
Oracle LOGISTIX → Bronze cartellino (~180/g) / dettaglio_carr (~10.000/g)
      ▼ Silver: missione_carrellista → sessione_carrellista
      ▼ Gold: F_MOVIMENTAZIONE_CARRELLISTI (~179 righe/g)
      ▼ DM: A_PRODUTTIVITA_MENSILE (~18 righe)
```

---

## 12. Inventario tabelle per schema

### `bronze_<env>.logistica`
**Logistix (multi-sito):** sto_tes_carichi, sto_righe_carico, pesate, tracciace178, dettaglio_carr,
cartellino, imbfmovim, abb_tolti, carrellisti, preparatori, ricevitori, spedizionieri, struttura_mag,
corsie, tabgen, aree_merceologiche, classe_posto_pallet, catena, catena_esterni  
**STAT:** storico_riepiloghi, testate_bolle, storico_bolle, storico_liste, buoni_eco, tipo_attivita_eco  
**CDT_ESTR_RAW:** automezzi, apvpunto_vendita, estrai_spedizioni  
**TRACK:** vettori, spedizioni

### `silver_<env>.logistica`
**Cleansing 1:1:** carico_testata, carico_dettaglio, pesata, ordine, spedizioni_clean,
automezzi_clean, vettori_track_clean, catena_clean, catena_esterni_clean,
storico_liste_clean, storico_bolle_clean, prep_riepilogo, t_pdv, t_vettori,
sessione_carrellista, missione_carrellista, tracciabilita_lotto  
**Elaborazioni intermedie:** storico_liste_uniche, storico_bolle_uniche, catena_unificata,
t_stock, s_trasp_mtv, giacenza_aggregata, costo_trasporto  
**Dimensioni (silver):** dim_sito, dim_operatore, dim_corriere, dim_topografia, dim_pdv *(dep)*, dim_articolo *(dep)*, dim_fornitore *(dep)*

### `silver_<env>.logistica_curated`
carico, giacenze, prep_sped, turno_prep_sito, trasporto, ordini

### `gold_<env>.logistica`
**Fact:** F_CARICO, F_GIACENZE_DAILY, F_PREP_SPED, F_TURNO_PREP_SITO, F_TRASPORTO, F_ORDINI,
F_MOVIMENTAZIONE_CARRELLISTI, F_TRACCIABILITA_LOTTI  
**Dimensioni:** LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA, LU_AREA_MERCL_LOGIS,
LU_ART_RADICE, LU_FORNITORE, LU_PDV, LU_GIORNO, LU_MESE *(retail master da bronze_dev.condiviso)*

### `gold_<env>.logistica_dm`
A_INBOUND_MENSILE, A_OUTBOUND_MENSILE, A_PRODUTTIVITA_MENSILE, A_TURNO_PREP_SITO,
A_GIACENZE_MONTHLY, A_STOCK_MENSILE

---

## 13. Tabelle dismesse

Tabelle rimosse dalla pipeline — non estrarre, non referenziare nei notebook.

| Tabella | Sistema origine | Motivo dismissione |
|---------|-----------------|--------------------|
| `artdgene` | CDT_ESTR | Sinonimo su db-link remoto morto (@TRASPO). Dead-join in AS-IS (nessuna colonna selezionata). |
| `cndpardgene` | CDT_ESTR | Nessun riferimento in pipeline TO-BE. |
| `ass_merceologiche` | CDT_ESTR | Sinonimo @TRASPO inesistente. Nessun consumer. |
| `macro_aggregazioni` | CDT_ESTR | Idem @TRASPO. Nessun consumer. |
| `cndstostock` | CDT_ESTR | Non raggiungibile. Silver fallback: `VAL_STOCK_* → 0` (fisiologico). |
| `gfdit` | CDT_ESTR | Non raggiungibile. Silver fallback: `PDV_FID_COD → '00000'` (fisiologico). |
| `vettori` (CDT_ESTR.VETTORI) | CDT_ESTR | Doppione di `vettori@TRACK`. Fonte unica = TRACK. |
| `contratti_corrieri` | logistix_wl1 | Tabella ORA-00942 (non esiste in Oracle). Schema dismesso. |
| `ordini_testate` | logistix_wl1 | Idem — schema logistix_wl1 dismesso. |
| `ordini_righe` | logistix_wl1 | Idem. |
| `swap` (logistix_wl1) | logistix_wl1 | Idem. |
| `silver_t_prep_sped` | — | Deprecato (OP-17). Non eseguire. |
| `silver_t_trasp_mtv` | — | Deprecato. Non eseguire. |
| `silver_trasp_mtv_build` | — | Deprecato (RS-08, 2026-06-20). Non eseguire. |
| `prep_sped_integrata` | — | Deprecato (RS-04, 2026-06-20). Non eseguire. |
| `silver_timbrature_sessioni` | — | Rimosso (RS-05, 2026-06-20). Leggeva `bronze.t_prep_sped` (CND non estratto); output non consumato. |
| `silver_costo_trasporto` | — | Rimosso (RS-06, 2026-06-20). Output `silver.logistica.costo_trasporto` non consumato da nessun gold. |
| `silver_t_pdv` (CDT_ESTR) | — | Rimosso (RS-02, 2026-06-20). Output non consumato dai fact gold (usano `bronze_dev.condiviso.LU_PDV`). |
| `bronze_pdv` | CND | Rimosso (RS-01, 2026-06-20). Leggeva `cnd-landing/t_pdv` (non estratto); PDV arriva da CDT_DW. |
| Bronze WL* / S_* CDT_ESTR | CDT_ESTR | Tutti rimossi (schema rimosso run 2026-05-XX). |

---

## 14. Regole di layer

### Bronze
- **1:1 con sorgente**: nessuna derivazione, nessun join tra tabelle
- **Schema-on-read**: colonne lette così come arrivano; cast solo se necessario per MERGE
- **Metadati aggiunti**: `_bronze_load_date`, `_bronze_insert_ts`, `_source_file`, `_sito_cod` (multi-sito)
- **MERGE null-safe**: chiave composita con operatore `<=>` per gestire NULL in chiave (es. `BOL_NRO_RIGA`)
- **Deduplicazione pre-MERGE**: `ROW_NUMBER() OVER (PARTITION BY chiave ORDER BY ...)` prima del merge
- **File assente**: `dbutils.notebook.exit("NO_DATA")` — non è un errore, monitorare separatamente

### Silver
- **Normalizzazione sito**: `normalize_sito()` da `logistica_utils` — converte formato numerico (`"20"`) in codice alfa (`"LGAX"`) tramite tabgen
- **surrogate_key_fallback**: `default_val="-1"` per FK orfane; `null_val="ND"` per FK che sono NULL per natura (es. OPERATORE_COD, PREPARATORE_COD)
- **DQ check_not_null**: applicato su chiavi business obbligatorie (non su FK nullable by design)
- **DQ check_row_count**: soglia `min_rows=1` — emette WARNING se 0 righe (non FAIL)
- **DQ S7 (costanza attributi)**: 11 attributi non costanti per bolla in `storico_bolle_uniche` e `storico_liste_uniche` — fisiologici (aggiornamenti progressivi in sorgente). `BOL_NRO_BOLLA` varia per design (chiave 8 colonne è corretta; DQ-01/02 analisi 2026-06-20). Flag `_bolla_multipla` aggiunto a `storico_bolle_uniche` per audit downstream (DQ-03).
- **Pattern #2 incrementale**: ricalcolo delle sole chiavi impattate nel batch, non full-scan
- **NO_DATA graceful exit**: `dbutils.notebook.exit("NO_DATA")` — contato come OK dal runner

### Gold
- **Surrogate key**: tutti i FK risolti via `surrogate_key_fallback` prima della scrittura
- **Membro ND**: `dim_operatore` contiene la riga con `OPERATORE_COD="ND"`, `TIPO=NON_RILEVATO` — assorbe i NULL FK a Gold senza generare orphan
- **Orphan rate**: check post-join, soglia 0% — warning se > 0; validato 0.0% su run 2026-06-17
- **Partizioni**: fact tables partizionate per data o ANNO_MESE per performance query
- **Aggregati DM**: sempre derivati da fact Gold — mai da Silver direttamente
- **Naming**: `LU_*` per lookup, `F_*` per fact, `A_*` per aggregati DataMart (OP-06)
- **Colonne NAT (L-01)**: ogni fact scrive `<dim>_COD_NAT` (chiave naturale ante `surrogate_key_fallback`) per consentire la ri-risoluzione LAD tramite `gold_lad_resolver`. Present in: F_CARICO (4 NAT), F_PREP_SPED (4), F_TURNO_PREP_SITO (4), F_TRASPORTO (2), F_ORDINI (2).

---

## 15. Runbook Operativo

### Alert e soglie

Gli alert inviano notifiche via email e Teams al gruppo `ops-logistico@conad.it`.

| Alert Name | Trigger | Soglia | Severità |
|------------|---------|--------|----------|
| `ALERT_WF_FAILED` | Qualsiasi workflow FAILED | 1 failure | 🔴 CRITICO |
| `ALERT_SLA_BREACH` | Gold non completato entro 05:30 | Orario > 05:30 | 🔴 ALTO |
| `ALERT_QUARANTINE_HIGH` | Rate quarantena > soglia | > 5% righe quarantena | 🟡 MEDIO |
| `ALERT_LAD_RATE` | FK non risolte > soglia | > 1% righe con FK = -1 | 🟡 MEDIO |
| `ALERT_KPI_DELTA` | Delta KPI Databricks vs Oracle > soglia | > 1% su qualsiasi KPI principale | 🔴 ALTO |
| `ALERT_CE178_SCADUTI` | Lotti scaduti con giacenza > 0 | Qualsiasi | 🔴 CRITICO |
| `ALERT_DISK_ADLS` | Utilizzo ADLS2 > soglia | > 85% capacità | 🟡 MEDIO |

Configurazione: `portal.azure.com` → Resource Group `rg-logistico-prod` → Monitor → Alert Rules

### Come leggere i log

**Via UI Databricks:** Workflows → selezionare il workflow → Runs → cliccare sull'ultima run → Logs → `stdout`/`stderr`.

**Formato log strutturato JSON:**
```json
{
  "timestamp": "2026-06-17T03:45:12Z",
  "workflow":  "wf_silver_all_daily",
  "task":      "silver_carichi",
  "level":     "INFO",
  "rows_in":   125432,
  "rows_out":  125398,
  "rows_quarantine": 34,
  "duration_sec": 42,
  "run_date":  "2026-06-16"
}
```

**Metriche chiave da monitorare:**

| Metrica | Campo log | Soglia attenzione |
|---------|-----------|-------------------|
| Righe quarantena | `rows_quarantine` | > 5% di `rows_in` |
| Durata task | `duration_sec` | > 2× durata baseline |
| Righe output | `rows_out` | < 90% di `rows_in` senza quarantena |
| Errori FK | `lad_count` | > 1% |

**Stati task:**

| Stato | Significato | Azione |
|-------|-------------|--------|
| `SUCCESS` | Completato | Nessuna |
| `FAILED` | Errore | Vedere procedure sotto |
| `SKIPPED` | Saltato (dipendenza fallita) | Analizzare task precedente |
| `TIMEDOUT` | Timeout superato | Aumentare timeout o ridurre numPartitions |

### Procedure per anomalie comuni

**Anomalia A — Quadratura fuori soglia**

```
STEP 1 — Quantificare il delta
  SELECT COUNT(*), SUM(qta_ricevuta) FROM gold.logistica.F_CARICO
  WHERE data_arrivo = DATE_SUB(CURRENT_DATE(), 1);
  (confrontare con Oracle via DBA)

STEP 2 — Identificare il layer dove il delta si materializza
  COUNT(*) in Bronze → Silver → Gold per lo stesso giorno

STEP 3 — Se delta in Bronze: estrazione incompleta → rilanciare Bronze con force_reload=true

STEP 4 — Se delta in Silver (silver < bronze): righe in quarantena non conteggiate
  SELECT COUNT(*) FROM logistica.silver_*_quarantine WHERE DATE(bronze_ingest_ts) = ...;

STEP 5 — Se delta in Gold (gold < silver): RESTORE TABLE e rilanciare Gold
  RESTORE TABLE logistica.gold_f_carico TO VERSION AS OF <N-1>;

STEP 6 — Non identificato dopo 5 step: escalation L2. Non modificare dati.
```

**Anomalia B — Missing dimension log > 5% (Late-Arriving Dimensions)**

```
1. Identificare quale dimensione manca:
   SELECT error_code, COUNT(*) FROM logistica.silver_carichi_quarantine
   WHERE DATE(quarantine_ts) = CURRENT_DATE() GROUP BY error_code;

2. Refresh urgente dimensione mancante (Bronze→Silver→Gold)

3. Rilanciare retry LAD:
   dbutils.notebook.run("silver/retry_lad_carichi", 0, {"run_date": "<data>", "max_retry_age_days": "2"})

4. Verificare svuotamento quarantena → rilanciare Gold
```

**Anomalia C — Delta Lake corruption (SNAPSHOT_NOT_FOUND)**

```sql
-- 1. Identificare versioni disponibili
DESCRIBE HISTORY logistica.gold_f_carico;

-- 2. Verificare versione stabile
SELECT * FROM logistica.gold_f_carico VERSION AS OF <N-1> LIMIT 10;

-- 3. Eseguire RESTORE
RESTORE TABLE logistica.gold_f_carico TO VERSION AS OF <N-1>;

-- 4. Verificare integrità
SELECT COUNT(*), MAX(data_load) FROM logistica.gold_f_carico;

-- 5. VACUUM (non ridurre sotto 168h = 7 giorni)
VACUUM logistica.gold_f_carico RETAIN 168 HOURS;
```

**Anomalia D — Workflow timeout** (ex JDBC — non applicabile in v2.0 landing CSV, ma può verificarsi su query DQ Gold con grandi volumi)

Ridurre `numPartitions` del task incriminato e rilanciare manualmente.

### Backfill manuale

**Metodo raccomandato — workflow parametrizzato:**
```
1. Navigare: Workflows → Jobs → wf_bronze_all_daily
2. Cliccare "Run now"
3. Parametri: run_date="2026-06-10", force_reload="true"
4. Ripetere in ordine per Silver e Gold
```

**Backfill range di date (notebook `ops/backfill_range.py`):**
```python
from datetime import date, timedelta
start_date, end_date = date(2026, 6, 1), date(2026, 6, 10)
current = start_date
while current <= end_date:
    run_date = current.strftime("%Y-%m-%d")
    dbutils.notebook.run("bronze/ingest_carichi", 3600, {"run_date": run_date, "force_reload": "true"})
    dbutils.notebook.run("silver/transform_carichi", 1800, {"run_date": run_date})
    dbutils.notebook.run("gold/load_f_carico", 1800, {"run_date": run_date})
    current += timedelta(days=1)
```

### Come sospendere un workflow (via CLI)

```bash
# Sospendere job specifico (es. job_id = 12345)
databricks jobs update --job-id 12345 '{"schedule": {"pause_status": "PAUSED"}}'

# Sospendere tutti i job
databricks jobs list --output JSON | jq -r '.jobs[].job_id' | while read id; do
    databricks jobs update --job-id $id '{"schedule": {"pause_status": "PAUSED"}}'
done
```

### SLA

| Metrica | Obiettivo |
|---------|-----------|
| Completamento tutti i workflow | Entro le 05:30 ogni giorno |
| Dati disponibili in MicroStrategy | Entro le 06:00 ogni giorno |
| Risposta a incident critico L2 | < 30 min dalla rilevazione |
| Risoluzione incident critico | < 2 ore dalla rilevazione |
| Disponibilità report MicroStrategy | > 99.5% mensile |

Il workflow giornaliero è considerato **completato** quando: (1) tutti i task gold in SUCCESS; (2) check quadratura delta < 1% su tutti i KPI principali; (3) check CE178 eseguito; (4) nessun alert critico attivo.

### Contatti ed escalation

```
Alert automatico / segnalazione utente
    ↓
L1 — Operations Lead (entro 15 min)
    ↓ se non risolto in 30 min
L2 — Cloud Architect (reperibile H24)
    ↓ se non risolto in 30 min
L3 — PM Progetto + decisione rollback
    ↓ se impatto critico business
Responsabile Business (Direzione Logistica)
```

---

## 16. Note operative

### Dipendenze di ordinamento Silver (locale)

In produzione Databricks Jobs le dipendenze sono gestite dal DAG. Localmente (`run_all_silver.py`) l'ordine è alfabetico — alcune dipendenze inter-notebook non sono rispettate ma il comportamento è fisiologico (ogni run legge i dati scritti dal run precedente):

| Notebook dipendente | Dipende da | Effetto ordine alfabetico |
|--------------------|------------|---------------------------|
| `silver_t_stock` [8] | `silver_catena_unificata` [20] | Legge catena del run precedente — fisiologico |
| `silver_prep_prep_sped` [24] | `silver_storico_liste_uniche` [31] | Legge liste del run precedente — fisiologico |
| `silver_giacenze_aggregata` [21] | `silver_prep_giacenze` [22] | 0 righe se t_stock non aggiornato — fisiologico |

### Sorgenti CND non estratte giornalmente

Le tabelle `t_pdv`, `t_stock`, `t_prep_sped`, `t_trasp_mtv` non hanno estrazione giornaliera automatica da CND. I notebook Silver emettono `NO_DATA` graceful quando la landing è assente — non bloccano il run.

### Membro ND in dim_operatore

La riga `OPERATORE_COD="ND"` è inserita da `silver_dim_operatore` al termine di ogni run. Garantisce che i NULL FK in `F_PREP_SPED.PREPARATORE_COD` e `F_PREP_SPED.OPERATORE_COD` si aggancino al membro ND invece di diventare orfani (-1).

### BOL_NRO_RIGA è nullable

`storico_bolle.BOL_NRO_RIGA` ha ~2.141 NULL fisiologici per run. È usata come chiave MERGE con operatore null-safe (`<=>`), non come campo business obbligatorio — esclusa da `check_not_null`.

### Row hash pruning (OP-30, incrementalità)

Tre pilastri dell'incrementalità:
1. **Bronze pruning** `_row_hash` (SHA-256 colonne business): le righe identiche non ri-datano `_bronze_load_date` (~22% propagato sul test)
2. **Silver clean**: filtro `_bronze_load_date == run_date` + MERGE upsert null-safe + dedup
3. **Prep grandi** (uniche/prep_sped): pattern #2 **chiavi-impattate** + MERGE

Attivazione pruning: rebuild una-tantum delle bronze (per creare `_row_hash`). Prep piccoli restano full (OP-34). Widget `full_refresh=true` per ricalcolo completo/backfill.

### Watermark OP-35

Tabella `control_<env>.etl.watermark`, chiave `(stage, sistema, tabella, sito)`. Pilota su `silver_storico_liste_clean` validato 2026-06-14. Rollout completato 2026-06-19 su tutti i notebook `_clean`: `storico_bolle_clean`, `storico_liste_clean`, `carichi_testate`, `carichi_dettagli`, `spedizioni_clean`, `ordini`. Pendente: W-05 landing_to_bronze (dipende da infra control catalog cloud).

### Late-arriving dimensions (OP-32)

Implementato come job generico (L-02, 2026-06-20). `notebooks/gold/maintenance/gold_lad_resolver.py` — widget: `fact_table`, `env`, `retail_master_schema`, `dry_run`. Config pre-cablata per F_CARICO, F_PREP_SPED, F_TURNO_PREP_SITO, F_TRASPORTO, F_ORDINI. Re-join su `<dim>_COD_NAT` (natural key ante surrogate_key_fallback). Partitioning preservato da `DESCRIBE DETAIL`. Scheduling L-03 ancora pendente (v. backlog §5a).

### Runner locale

```
tests/local_bronze/run_notebook.py --notebook <path> --run-date YYYY-MM-DD [--siti ...] [--memory-gb N]
```

Scripts PowerShell per re-run completo: `scripts/rerun_1_bronze.ps1`, `rerun_2_silver.ps1`, `rerun_3_gold.ps1`, `rerun_22siti.ps1`.
