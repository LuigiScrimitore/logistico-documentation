# Linee guida di sviluppo per area — Pipeline Medallion (TO-BE)

**Versione:** 2.1 (integrata con Gap Analysis v1.1 + readiness brownfield Databricks)  
**Ultimo aggiornamento:** 2026-07-02  
**Owner:** Cloud Data Architect — Team Logistico 2.0

> **Contratto di sviluppo** per i 4 Data Engineer d'area (Carichi, Spedizioni, Trasporti, Stock).  
> Garantisce coerenza tra le aree sviluppate in parallelo. Il **Data Architect** certifica ogni area su questa checklist.  
> Riferimento analisi: `Revisione AS-IS to-be - Migrazione CDT_ESTR.md`.  
> **Fonte:** aggiorna e integra `DOCS/Linee guida sviluppo per area - Medallion.md` (v1.0) + `DOCS/Gap Analysis - Linee Guida v1.1.md` (2026-05-30).

---

## 1. Regole di layer (vincolanti)

| Layer | Schema/zona | Cosa fa | Cosa NON fa |
|---|---|---|---|
| **Bronze** | `bronze.<area>` | Copia 1:1 della sorgente raw (stesse colonne, stessi record) + metadati `_bronze_*` + `_sito_estrazione` | Nessun join, nessuna aggregazione, nessuna colonna derivata (no `mag_sito_cod`, no `ART_RADICE/VAR`) |
| **Silver — clean** | `silver.clean.*` | Pulizia 1:1: date Julian→date, trim, cast, **normalizzazione sito**, derivazione radice/variante, dedup tecnica | Nessuna business logic, **nessun join tra tabelle**, nessuna chiave-giorno (`clean_dat_d`) |
| **Silver — prep** | `silver.prep.*` | **Fase 1 (modellazione):** join tra tabelle `silver.clean`. **Fase 2 (calcolo):** logiche business, valorizzazioni, derivazioni, chiave-giorno `clean_dat_d` | Nessun aggancio a lookup dimensionali / surrogate key |
| **Gold — F_\*** | `gold.<area>` | **Fase 3 (normalizzazione):** aggancio lookup dimensioni con `surrogate_key_fallback(-1)` + `check_orphan_rate`, surrogate key, scrittura fact | Niente modellazione/calcolo |
| **Gold_dm — A_\*** | `gold.aggregati` | Aggregati mensili dai fact | Niente nuova business logic |

### 1-bis. Standard a 2 notebook per fatto (UNIFORME su tutte le aree)

Ogni fatto si sviluppa con **esattamente 2 notebook**, indipendentemente dalla complessità:

1. **`silver_prep_<fatto>.py`** → Fase 1 (join `silver.clean`) + Fase 2 (calcolo/logiche). Materializza `silver.prep.<fatto>`.
2. **`gold_f_<fatto>.py`** → Fase 3 (lookup dimensionali + surrogate key) + scrittura `gold.<area>.F_<FATTO>`.

> **🔒 REGOLA D'ORO:** il notebook Gold legge **SEMPRE e SOLO** da `silver.prep.<fatto>`. Mai dal grezzo, mai dal `silver.clean`, mai da una sorgente parallela. Le 3 fasi vanno sempre eseguite nell'ordine 1→2→3.

> **Nota date/sito:** `julian_to_date` e `normalize_sito` vivono **solo** in `silver.clean`. La chiave-giorno `clean_dat_d` (date→int YYYYMMDD) è una preparazione dimensionale → vive in `silver.prep`.

---

## 2. Pattern Bronze 1:1

- Leggere la sorgente raw via landing (CSV o Parquet — vedi §9 Gap #2) → Delta, **schema-on-read per nome header** (StringType), `SELECT *`.
- **Mai `.schema()` posizionale** su CSV: leggere sempre per nome colonna (header). Aggiungere colonne sorgente senza rompere i notebook esistenti.
- Metadati: `_bronze_load_date`, `_bronze_insert_ts`, `_source_file`, **`_sito_estrazione`** (dal db-link, NON è dato di business).
- **Niente** `mag_sito_cod`/`ART_RADICE`/`ART_VAR` nel Bronze (sono derivate → Silver).
- Filtri: **solo di business** (es. `ARM_TIPO_AREA=1`). **Mai** il flag CDC `*_DATA_ESTRAZIONE_DWH` (gestito come full+finestra a monte nel landing).
- Mode: `full` (anagrafiche), `delta`+finestra data (transazionali), `snapshot` (stock giornaliero).

---

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

---

## 4. Pattern Silver — prep (Fase 1 modellazione + Fase 2 calcolo)

**Fase 1 — Modellazione (join tra `silver.clean`):**
- **"UNICHE"** (spedizioni): `GROUP BY 8 chiavi` con `COUNT`/`SUM`/`MIN`/`MAX`. Aggiungere **DQ check** `COUNT(DISTINCT col)=1` sugli attributi costanti per chiave.
- **CATENA** (stock): `WL2_CATENA = CATENA UNION CATENA_ESTERNI`. ⚠️ Non usare `UNION` su tupla intera: **dedup esplicita per chiave logica** con regola di precedenza.
- **Fill-down vettore** (trasporti): `first_value(col, ignore_nulls) over (partition by NUM_GITA)` — NON `MAX` arbitrario.

**Fase 2 — Calcolo (business logic):**
- Logiche delle viste `V_*` e procedure `SP_INS_T_*`: valorizzazioni, durate, derivazioni, flag.
- Chiave-giorno `clean_dat_d` (date→int YYYYMMDD) sui campi data che diventano dimensione calendario.
- Output: tabella `silver.prep.<fatto>` business-completa ma **senza** surrogate key dimensionali.

---

## 5. Pattern Gold — F_* (Fase 3 normalizzazione + aggancio dimensioni)

**Legge SOLO da `silver.prep.<fatto>`** (regola d'oro §1-bis).

- Aggancio dimensioni per **codice naturale** con `surrogate_key_fallback(col, lu_df, lu_pk, default_val="-1", null_val="ND")` + `check_orphan_rate(df, col, notebook)`.
  - `default_val="-1"` → orphan vero (codice presente nel sorgente ma non in dim) → SCONOSCIUTO
  - `null_val="ND"` → NULL nel sorgente (es. PREPARATORE_COD NULL) → membro NON_RILEVATO in dim_operatore
- Lookup retail condivise: schema `bronze_<env>.condiviso` (D2 ✅) → aggancio futuro a Gold Retail (OP-02).
- Partizione/scrittura: dynamic partition overwrite o MERGE; **mai** `replaceWhere` statico su date di business multiple, **mai** dedup `MIN(ROWID)`.

### 5-bis. Pattern incrementale (delta giornaliero) — OP-30

Tre meccanismi standard:

1. **Bronze pruning (`_row_hash`).** Nei bronze DELTA_MERGE: `bronze_df = add_row_hash(bronze_df)` + MERGE con `whenMatchedUpdate(condition="tgt._row_hash <> src._row_hash")`. Le righe identiche non vengono ri-datate → `_bronze_load_date` = "ultima modifica". Helper: `add_row_hash`, `bronze_merge_upsert` in `logistica_utils/utils.py`. Chiavi MERGE **sempre null-safe (`tgt.k <=> src.k`)**.  
   - Lettura CSV **per nome (header)**, MAI `.schema()` posizionale.

2. **Clean incrementale.** Widget `full_refresh` (default false). Incrementale = `filter(_bronze_load_date == run_date)` + **MERGE upsert** sulla chiave naturale (null-safe) + `dropDuplicates(MERGE_KEYS)`. `full_refresh`/prima-volta → CTAS overwrite. Snapshot → dynamic partition overwrite per giorno.

3. **Pattern #2 prep (chiavi-impattate).** Per uniche/join su volumi grandi: `impacted = <input>.filter(_silver_load_date == run_date).select(<chiavi>).distinct()`; ri-aggregare/ri-join l'intero storico delle sole chiavi impattate (join **null-safe** `eqNullSafe`) → MERGE upsert. `full_refresh` → ricalcolo completo.

**Regole d'oro incrementale:** chiavi MERGE null-safe; dedup deterministico (tiebreaker stabili nel `Window.orderBy`); verificare `righe == distinct(chiavi)` e cross-giorno=0 post-run. Attivare il pruning richiede un rebuild una-tantum delle bronze preesistenti.

### 5-ter. Pattern watermark — OP-35 (parzialmente implementato)

Tabella `control_<env>.etl.watermark`, chiave `(stage, sistema, tabella, sito)`. Sostituisce il `run_date` fisso con un range basato sull'ultima data processata con successo — abilita catch-up multi-giorno in un solo run.

Helper in `logistica_utils/utils.py`: `read_watermark`, `update_watermark` (transazionale: FAIL non avanza `last_processed_date`), `pending_landing_dates`.

**Stato:** pilota `silver_storico_liste_clean` validato. Rollout pendente: `storico_bolle_clean`, carichi, spedizioni, ordini. Design completo: `docs/Archive/Design - Watermark ETL (OP-35).md`.

---

## 6. Anomalie legacy da NON replicare (correggere nel TO-BE)

| Anomalia | Correzione |
|---|---|
| `SEC_PREP_PREL` con `DDD` (non cross-year) | `unix_timestamp(fine)-unix_timestamp(inizio)` + DQ `>=0` |
| `MIN(DATA_FINE_PRELIEVO)` nelle UNICHE | valutare `MAX` (semantica "ultimo istante") |
| Dedup `MIN(ROWID)` | chiave esplicita + window deterministica |
| Filtro DQ via `UPDATE` sul sorgente | quarantena DQ in Bronze/Silver (no scrittura sorgente — **READ-ONLY Oracle**) |
| `WL2_CATENA UNION` su tupla intera | dedup per chiave logica + precedenza |
| `SYSDATE` placeholder (DATA_RIEP in WL2) | derivare da RPLPR in Silver |

---

## 7. Checklist di certificazione (Data Architect)

Per ogni area, prima del via libera:
- [ ] Bronze è 1:1 col sorgente (nessuna derivata, nessun join)
- [ ] Lettura CSV per nome header (mai `.schema()` posizionale)
- [ ] `silver.clean` fa solo cleansing 1:1 (date Julian→date, `normalize_sito`, trim/cast, dedup tecnica) — **nessun join, nessuna chiave-giorno**
- [ ] Il fatto ha **esattamente 2 notebook**: `silver_prep_<fatto>` + `gold_f_<fatto>` (§1-bis)
- [ ] Modellazione (join) e calcolo (logiche) sono in `silver.prep`; surrogate key/lookup dimensionali solo in Gold
- [ ] **REGOLA D'ORO:** il Gold legge SOLO da `silver.prep.<fatto>` (mai grezzo, mai clean, mai sorgente parallela)
- [ ] Nessuna catena parallela: ogni `silver.prep` costruito è effettivamente consumato dal suo Gold
- [ ] Le anomalie §6 sono corrette (non replicate)
- [ ] DQ: orphan-rate sugli agganci (`check_orphan_rate`), check costanza UNICHE, check fill-down
- [ ] `surrogate_key_fallback` usa `default_val="-1"` (orphan vero) e `null_val="ND"` (NULL sorgente) dove appropriato
- [ ] **Incrementale (§5-bis):** bronze `_row_hash` pruning + MERGE null-safe; clean filtro `_bronze_load_date`+MERGE+dedup; prep grandi con pattern #2 chiavi-impattate; post-run `righe == distinct(chiavi)` e cross-giorno=0
- [ ] Naming coerente (`LU_*`, `F_*`, `A_*`; FQN catalog.schema.table)
- [ ] Punti DECISIONE-BUSINESS aperti documentati (non bloccano, ma tracciati)

---

## 8. Ripartizione sorgenti per area

| Area | Sorgenti raw | Target |
|---|---|---|
| **Carichi** | STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE, TRACCIACE178, ARTDGENE | F_CARICO |
| **Spedizioni** | STORICO_LISTE, STORICO_BOLLE, STORICO_RIEPILOGHI, SPEDIZIONI, ESTRAI_SPEDIZIONI, CORSIE, AREE_MERCEOLOGICHE | F_PREP_SPED (da T_PREP_SPED) |
| **Trasporti** | SPEDIZIONI@TRACK, VETTORI, AUTOMEZZI, T_TRASP_MTV, T_VETTORI, T_PDV | F_TRASPORTO, T_VETTORI |
| **Stock** | CATENA, CATENA_ESTERNI, T_STOCK, STRUTTURA_MAG, MACRO_AGGREGAZIONI | F_GIACENZE/T_STOCK |
| **Carrellisti** | DETTAGLIO_CARR, CARTELLINO, IMBFMOVIM | F_TURNO (missioni/sessioni) |
| **Comuni** | TABGEN, utility, db-link @TRACK, WL1_MAG_SITO_STORICO (config), 22 db-link LOGISTIX | fondamenta, dim_operatore recovery |

---

## 9. Pendenze Gap Analysis v1.1 (da Gap Analysis - Linee Guida v1.1.md, 2026-05-30)

> Integra la gap analysis condotta sulle risposte di Reply alle linee guida v1.1.  
> File originale archiviato in `docs/Archive/Gap Analysis - Linee Guida v1.1.md`.

### 🟢 Gap #2 — Supporto file Parquet in Bronze ✅ FATTO (2026-06-20, G-01)

Risolto: `detect_format` + `read_landing` centralizzate in `utils.py`; runner con `--file-format`;
35 notebook Bronze migrati; workflow con `file_format: "auto"`.

### ✅ Gap #3 — Storage / landing su DWH esistente (D3 confermato 2026-07-02)

**Aggiornamento:** con l'integrazione nel DWH esistente **non** creiamo storage credential/external
location proprie (le gestisce il team piattaforma). **D3 confermato: UC Volume** in `landing_dev`
(`landing_mode = "volume"`, path `/Volumes/landing_dev/logistica/files`). Il path di landing è astratto
in `lib/logistica_utils/storage.py`. Il modulo greenfield `modules/unity_catalog` (che creava
credential+external location) **non si applica**. Push file via **SFTP**, formato CSV (Parquet pronto).

**Effort:** ~0.25 gg DevOps (`terraform apply` overlay). Vedi `11_devops_handoff_databricks.md`.

### ✅ Gap #4 — Multi-repo GitLab (confermato DevOps 2026-07-03)

**Aggiornamento:** target confermato = **multi-repo in un subgroup GitLab** `logistico` (NON mono-repo).
Un progetto = un repository: `logistico-infrastructure`, `logistico-workflows`, `logistico-lib`.
`databricks.yml` (DAB) versiona i job con compute **serverless**. Lo script `git_monorepo_import.sh`
è **obsoleto**. Prerequisiti: attivazione utenze + creazione subgroup con permessi (mail a Extrared,
vedi `12_checklist_infra_setup.md`).

**Effort:** ~1.5 gg DevOps (FASE C in `11_devops_handoff_databricks.md`).

### 🟡 Gap #5 — Secret Databricks via GitLab CI (rivisto brownfield 2026-07-02)

**Aggiornamento:** le credenziali **Oracle non servono più** su Databricks (ingestion in **push**) →
niente secret scope Oracle. Restano solo i token Databricks (`DATABRICKS_HOST/TOKEN` dev+prod) come
masked variable GitLab CI per il deploy del bundle. `secret_helper.py` invariato.

**Effort:** ~0.25 gg DevOps.

### 🟢 Gap #1 — Condivisione Anagrafiche (COERENTE)
Le `LU_*` condivise sono in `gold` per dominio con permessi di lettura. Nome/percorso definitivo da OP-02.

### 🟢 Gap #6 — Naming Convention e Schemi Gold (COERENTE)
`gold_<env>.logistica.*`, `gold_<env>.logistica_dm.*`. Dev e prod separati e speculari su tutti i livelli (incluso Gold).

### 🟢 Gap #8b — SparkSQL consentito (COERENTE)
10 view KPI in `sql/kpi/` e uso di `spark.sql()` nei notebook sono conformi.

### 🟢 Gap #9 — Orchestrazione DAB, no Airflow (COERENTE)
**7** workflow YAML in `workflows/` usano Databricks Asset Bundles. Scheduling a cascata (00:30 → 06:00).
Compute **serverless**: nessun `job_clusters`, dipendenze via blocco `environments` (ADR-0009 / ACT_9007).
Wave E non ha un workflow proprio: CE178 in `logistica_carichi`, carrellisti in `logistica_prep_sped` (ACT_9008).

### 🟢 Gap #10 — Sviluppo in Dev (GitFlow — COERENTE)
Infrastruttura condivisa in dev, branch-based per job ad hoc, merge alla fine dello sviluppo.

### 🔵 Gap #7 — Split repo per area (Bassa priorità — post go-live)
La struttura attuale (unico repo `logistica`) è accettabile. Predisposta la struttura `notebooks/` per area per facilitare eventuale split futuro. **Non blocca lo sviluppo attuale.**

### 🔵 Gap #8a — Wheel Reply vs logistica_utils (Bassa priorità — post go-live)
`logistica_utils` è già sviluppata e testata (64 test). Prima di eventuale migrazione alla wheel Reply, richiedere documentazione API e valutare compatibilità. **Non modificare ora.**

---

*Documento aggiornato da: `DOCS/Linee guida sviluppo per area - Medallion.md` (v1.0) + `DOCS/Gap Analysis - Linee Guida v1.1.md` (2026-05-30).*  
*Entrambe le fonti sono archiviate in `docs/Archive/`.*
