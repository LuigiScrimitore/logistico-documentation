# Linee guida di sviluppo per area — Pipeline Medallion (TO-BE)

> **Contratto di sviluppo** per i 4 Data Engineer d'area (Carichi, Spedizioni, Trasporti, Stock).
> Garantisce coerenza tra le aree sviluppate in parallelo. Il **Data Architect** certifica
> ogni area su questa checklist. Il **Functional Expert** è consultabile per la semantica.
> Riferimento analisi: `Revisione AS-IS to-be - Migrazione CDT_ESTR.md`.

## 1. Regole di layer (vincolanti)

| Layer | Schema/zona | Cosa fa | Cosa NON fa |
|---|---|---|---|
| **Bronze** | `bronze.<area>` | Copia 1:1 della sorgente raw (stesse colonne, stessi record) + metadati `_bronze_*` + `_sito_estrazione` | Nessun join, nessuna aggregazione, nessuna colonna derivata (no `mag_sito_cod`, no `ART_RADICE/VAR`) |
| **Silver — clean** | `silver.clean.*` | Pulizia 1:1: date Julian→date, trim, cast, **normalizzazione sito**, derivazione radice/variante, dedup tecnica | Nessuna business logic, **nessun join tra tabelle**, nessuna chiave-giorno (`clean_dat_d`) |
| **Silver — prep** | `silver.prep.*` | **Fase 1 (modellazione):** join tra tabelle `silver.clean` (incl. elaborazioni intermedie WL: uniche, catena, fill-down). **Fase 2 (calcolo):** logiche business, valorizzazioni, derivazioni, chiave-giorno `clean_dat_d` | Nessun aggancio a lookup dimensionali / surrogate key |
| **Gold — F_\*** | `gold.<area>` | **Fase 3 (normalizzazione):** aggancio lookup dimensioni con `surrogate_key_fallback(-1)` + `check_orphan_rate`, surrogate key, scrittura fact | **Niente modellazione/calcolo** (vengono da `silver.prep`) |
| **Gold_dm — A_\*** | `gold.aggregati` | Aggregati mensili dai fact | Niente nuova business logic |

### 1-bis. Standard a 2 notebook per fatto (UNIFORME su tutte le aree)

Ogni fatto si sviluppa con **esattamente 2 notebook**, indipendentemente dalla complessità:

1. **`silver_prep_<fatto>.py`** → Fase 1 (join `silver.clean`) + Fase 2 (calcolo/logiche). Materializza `silver.prep.<fatto>`.
2. **`gold_f_<fatto>.py`** → Fase 3 (lookup dimensionali + surrogate key) + scrittura `gold.<area>.F_<FATTO>`.

> **🔒 REGOLA D'ORO:** il notebook Gold legge **SEMPRE e SOLO** da `silver.prep.<fatto>`.
> **Mai** dal grezzo, **mai** dal `silver.clean`, **mai** da una sorgente parallela.
> Le 3 fasi vanno sempre eseguite nell'ordine 1→2→3.

> **Nota date/sito (vincolo richiesto):** `julian_to_date` e `normalize_sito` vivono **solo** in `silver.clean` (cleansing bronze→silver). La chiave-giorno `clean_dat_d` (date→int YYYYMMDD) è una preparazione dimensionale → vive in `silver.prep`, **non** nel cleansing.

## 2. Pattern Bronze 1:1

- Leggere la sorgente raw via landing (CSV) → Delta, **schema-on-read** (StringType), `SELECT *`.
- Metadati: `_bronze_load_date`, `_bronze_insert_ts`, `_source_file`, **`_sito_estrazione`** (dal db-link, NON è dato di business).
- **Niente** `mag_sito_cod`/`ART_RADICE`/`ART_VAR` nel Bronze (sono derivate → Silver).
- Filtri: **solo di business** (es. `ARM_TIPO_AREA=1`). **Mai** il flag CDC `*_DATA_ESTRAZIONE_DWH` (gestito come full+finestra a monte nel landing).
- Mode: `full` (anagrafiche), `delta`+finestra data (transazionali), `snapshot` (stock giornaliero).

## 3. Pattern Silver — cleansing (usare SEMPRE le utility condivise)

| Necessità | Utility `logistica_utils` | Note |
|---|---|---|
| Data Julian → date | `julian_to_date(col)` | =FN_CLEAN_DAT_J |
| Data → int YYYYMMDD | `clean_dat_d(col)` | =FN_CLEAN_DAT_D (default 0) |
| Str YYYYMMDD → int | `clean_dat_v(col)` | =FN_CLEAN_DAT_V (default 19000101) |
| Codice sito → canonico 2 cifre | `normalize_sito(col, alias_map)` + `get_sito_alias_map(spark, bronze_schema)` | LGAX→20, 5→05 (lookup TABGEN nro_tab=7) |
| Articolo radice | `art_radice(col)` | =FN_GET_RADICE (LOGISTIX/SWAP/STAT) |
| Articolo variante | `art_variante(col)` | =FN_GET_VARIANTE_LOGISTICA |
| Trim/cast/null | funzioni Spark standard | TRIM, COALESCE, cast espliciti |

> Regola: il cleansing è **idempotente** e **non perde record** (1 riga bronze → 1 riga silver, salvo dedup tecnica dichiarata).

## 4. Pattern Silver — prep (Fase 1 modellazione + Fase 2 calcolo)

Notebook `silver_prep_<fatto>.py`. Le elaborazioni intermedie WL (uniche, catena, fill-down)
possono restare come tabelle `silver.clean` *normalizzanti* a monte, oppure essere inline nel prep.

**Fase 1 — Modellazione (join tra `silver.clean`):**
- **"UNICHE"** (spedizioni): `GROUP BY 8 chiavi` con `COUNT`(num righe)/`SUM`(quantità)/`MIN`(anagrafici)/`MAX`(date,prezzi). Aggiungere **DQ check** `COUNT(DISTINCT col)=1` sugli attributi che devono essere costanti per chiave.
- **CATENA** (stock): `WL2_CATENA = CATENA UNION CATENA_ESTERNI`. ⚠️ Non usare `UNION` su tupla intera (anomalia legacy): **dedup esplicita per chiave logica** con regola di precedenza.
- **Fill-down vettore** (trasporti): `first_value(col, ignore_nulls) over (partition by NUM_GITA)` — NON `MAX` arbitrario. DQ check `COUNT(DISTINCT vettore)>1` per gita.
- Join principali del modello fact (es. testata⋈dettaglio, liste⋈bolle, catena⋈struttura_mag).

**Fase 2 — Calcolo (business logic):**
- Logiche delle viste `V_*` e procedure `SP_INS_T_*`: valorizzazioni, durate, derivazioni, flag.
- Chiave-giorno `clean_dat_d` (date→int YYYYMMDD) sui campi data che diventano dimensione calendario.
- Output: tabella `silver.prep.<fatto>` business-completa ma **senza** surrogate key dimensionali.

## 5. Pattern Gold — F_* (Fase 3 normalizzazione + aggancio dimensioni)

Notebook `gold_f_<fatto>.py`. **Legge SOLO da `silver.prep.<fatto>`** (regola d'oro §1-bis).
- **Niente** modellazione né calcolo: arrivano già da `silver.prep`. Qui solo aggancio dimensioni e scrittura.
- Aggancio dimensioni per **codice naturale** con `surrogate_key_fallback(col, lu_df, lu_pk, default_val="-1")` + `check_orphan_rate(df, col, notebook)`.
- Lookup retail condivise: schema `cdtdw.condiviso` (workaround) → `gold_prod.condiviso` (OP-02). Lookup logistiche: `gold_prod.logistica.LU_*`.
- Partizione/scrittura: dynamic partition overwrite o MERGE; **mai** `replaceWhere` statico su date di business multiple, **mai** dedup `MIN(ROWID)`.

### 5-bis. Pattern incrementale (delta giornaliero) — OP-30

Obiettivo: a ogni run un nuovo giorno tocca **solo il delta reale** a ogni layer. Tre meccanismi standard:

1. **Bronze pruning (`_row_hash`).** Nei bronze in `DELTA_MERGE`: aggiungere `bronze_df = add_row_hash(bronze_df)` (firma SHA-256 delle sole colonne business) e fare il MERGE con `whenMatchedUpdate(condition="tgt._row_hash <> src._row_hash", set=...)`. Le righe **identiche** non vengono ri-scritte/ri-datate → `_bronze_load_date` = "ultima modifica". Helper: `add_row_hash`, `bronze_merge_upsert` in `logistica_utils/utils.py`. Chiavi MERGE **sempre null-safe (`tgt.k <=> src.k`)**.
   - Lettura CSV **per nome (header)**, MAI `.schema()` posizionale (la sorgente cresce di colonne → disallineamento → colonne azzerate). 1:1 = tutte le colonne sorgente.
2. **Clean incrementale.** Widget `full_refresh` (default false). Incrementale = `filter(_bronze_load_date == run_date)` + **MERGE upsert** sulla chiave naturale (null-safe) + `dropDuplicates(MERGE_KEYS)` (sorgente univoca → niente "multiple source rows matched"). `full_refresh`/prima-volta → CTAS overwrite. Snapshot (giacenze) → dynamic partition overwrite per giorno.
3. **Pattern #2 prep (chiavi-impattate).** Per uniche/join su volumi grandi: `impacted = <input>.filter(_silver_load_date == run_date).select(<chiavi>).distinct()`; ri-aggregare/ri-join **l'intero storico delle sole chiavi impattate** (join **null-safe** `eqNullSafe`) → MERGE upsert. `full_refresh` → ricalcolo completo. Sui prep piccoli (full in pochi sec) non conviene (OP-34).

**Regole d'oro incrementale:** chiavi MERGE null-safe (le sorgenti hanno null sporadici); dedup deterministico (tiebreaker stabili nel `Window.orderBy`); verificare sempre `righe == distinct(chiavi)` e che i dup siano same-day (cross-giorno=0) post-run. Attivare il pruning richiede un **rebuild una-tantum** delle bronze preesistenti (per creare `_row_hash`).

## 6. Anomalie legacy da NON replicare (correggere nel TO-BE)

| Anomalia | Correzione |
|---|---|
| `SEC_PREP_PREL` con `DDD` (non cross-year) | `unix_timestamp(fine)-unix_timestamp(inizio)` + DQ `>=0` |
| `MIN(DATA_FINE_PRELIEVO)` nelle UNICHE | valutare `MAX` (semantica "ultimo istante") |
| Dedup `MIN(ROWID)` | chiave esplicita + window deterministica |
| Filtro DQ via `UPDATE` sul sorgente | quarantena DQ in Bronze/Silver (no scrittura sorgente) |
| `WL2_CATENA UNION` su tupla intera | dedup per chiave logica + precedenza |
| `SYSDATE` placeholder (DATA_RIEP in WL2) | derivare da RPLPR in Silver |

## 7. Checklist di certificazione (Data Architect)

Per ogni area, prima del via libera:
- [ ] Bronze è 1:1 col sorgente (nessuna derivata, nessun join)
- [ ] `silver.clean` fa solo cleansing 1:1 (date Julian→date, `normalize_sito`, trim/cast, dedup tecnica) — **nessun join, nessuna chiave-giorno**
- [ ] Il fatto ha **esattamente 2 notebook**: `silver_prep_<fatto>` + `gold_f_<fatto>` (§1-bis)
- [ ] Modellazione (join) e calcolo (logiche) sono in `silver.prep`; surrogate key/lookup dimensionali solo in Gold
- [ ] **REGOLA D'ORO:** il Gold legge SOLO da `silver.prep.<fatto>` (mai grezzo, mai clean, mai sorgente parallela)
- [ ] Nessuna catena parallela: ogni `silver.prep` costruito è effettivamente consumato dal suo Gold
- [ ] Le anomalie §6 sono corrette (non replicate)
- [ ] DQ: orphan-rate sugli agganci, check costanza UNICHE, check fill-down
- [ ] **Incrementale (§5-bis):** bronze `_row_hash` pruning + MERGE null-safe; clean filtro `_bronze_load_date`+MERGE+dedup; prep grandi con pattern #2 chiavi-impattate; post-run `righe == distinct(chiavi)` e cross-giorno=0
- [ ] Naming coerente (`LU_*`, `F_*`, `A_*`; FQN catalog.schema.table)
- [ ] Punti DECISIONE-BUSINESS aperti documentati (non bloccano, ma tracciati)

## 8. Ripartizione sorgenti per area

| Area | Sorgenti raw | Target |
|---|---|---|
| **Carichi** | STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE, TRACCIACE178, ARTDGENE | F_CARICO |
| **Spedizioni** | STORICO_LISTE, STORICO_BOLLE, storico_riepiloghi, SPEDIZIONI, ESTRAI_SPEDIZIONI, CORSIE, AREE_MERCEOLOGICHE | F_PREP_SPED (da T_PREP_SPED) |
| **Trasporti** | vettori@TRACK, VETTORI, AUTOMEZZI, SPEDIZIONI(cond.) | F_TRASPORTO, T_VETTORI |
| **Stock** | CATENA, CATENA_ESTERNI, CNDSTOSTOCK, STRUTTURA_MAG, MACRO_AGGREGAZIONI* | F_GIACENZE/T_STOCK |
| **Comuni** | TABGEN, utility, db-link @TRACK, WL1_MAG_SITO_STORICO (config) | fondamenta |

---

*Le fondamenta comuni (utility cleansing) sono in `logistica_utils`. Lo sviluppo procede per area in parallelo; il run di ingestion e i quality test sono a cura del committente a sviluppi terminati.*
