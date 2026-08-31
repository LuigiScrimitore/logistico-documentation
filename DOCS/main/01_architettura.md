# Architettura Tecnica — Logistico 2.0

**Ultimo aggiornamento:** 2026-07-02  
**Versione:** 3.1 (stato corrente: environment locale, watermark, integrazione brownfield Databricks)  
**Owner:** Cloud Data Architect — Team Logistico 2.0

> 🧭 **Navigazione**: attività → [`acts/`](acts/) · decisioni → [`adr/`](adr/) · indice unico →
> [`15_backlog_master.md`](15_backlog_master.md). Stato di avanzamento → `sprint_agile/`.

> Questo documento è la **SSOT dell'architettura tecnica** del progetto.  
> Per il dettaglio completo dei deliverable e dell'inventario notebook, vedi `docs/Archive/Documento di Sviluppo Finale.md` (v2.0, 2026-05-30).  
> Per il mapping sorgente→layer completo, vedi `docs/main/03_pipeline_mapping.md`.

---

## 1. Architettura Target (Produzione)

```
Oracle / Logistix / STAT / TRACK
    │ (push CSV/Parquet su ADLS Gen2 landing zone — NO JDBC Oracle su Databricks)
    ▼
[Landing Zone ADLS] — abfss://landing@<account>.dfs.core.windows.net/logistica/
    │ (read → MERGE INTO Delta, schema-on-read per header)
    ▼
[Bronze] — bronze_<env>.logistica.*
    │ append-only / MERGE INTO, _row_hash pruning, _bronze_load_date, _sito_estrazione
    ▼
[Silver — clean] — silver_<env>.logistica.*
    │ cleansing 1:1: julian_to_date, normalize_sito, trim/cast, dedup tecnica
    ▼
[Silver — prep] — silver_<env>.logistica_curated.*
    │ join silver.clean, business logic, chiave-giorno clean_dat_d
    ▼
[Gold Core] — gold_<env>.logistica.{dim_*, f_*, LU_*}
    │ surrogate_key_fallback(-1/ND), check_orphan_rate, chiavi naturali
    ▼
[Gold DataMart] — gold_<env>.logistica_dm.{dm_*}
    │ aggregati mensili per BI
    ▼
[SQL KPI Views] — gold_prod.logistica.{kpi_*}  →  MicroStrategy / BI
```

**Layer di controllo trasversale:**
```
[Control] — control_<env>.etl.watermark
    + control_<env>.parametri.*
```

---

## 2. Unity Catalog — Struttura Cataloghi

Cataloghi nominati **per livello e ambiente**. Dev e prod sono **separati e speculari** su tutti i livelli:

```
bronze_dev  / bronze_prod
  └── logistica                  (tutte le tabelle raw per-sito)

silver_dev  / silver_prod
  └── logistica                  (tabelle cleansed 1:1)
  └── logistica_curated             (elaborazioni intermedie / preprocessing)

gold_dev    / gold_prod
  └── logistica                  (fact F_*, dimension dim_*, LU_*)
  └── logistica_dm               (DataMart: dm_*)

config_dev / config_prod         (layer controllo trasversale — non dati business; D1: config_*)
  └── etl                        (watermark, log run, esiti DQ — scritto dalle pipeline)
  └── parametri                  (mapping, override, correzioni codici, soglie DQ — manuali)
```

> **Anagrafiche master Retail:** condivise in lettura con naming `LU_*`. **Aggancio definitivo a Gold Retail da confermare (OP-02)**. Soluzione attuale (D2 ✅ 2026-07-02): `LU_*` da CDT_DW nello schema proprio `bronze_<env>.condiviso` (isolamento totale, popolato dal push cdt_dw).

> **⚠️ Integrazione brownfield (2026-07-02):** il target NON è un workspace nuovo ma il **Databricks/DWW aziendale esistente**. I catalog `bronze_dev`/`silver_dev`/`gold_dev`/`config_dev`/`landing_dev` **già esistono**: non si creano, si **referenziano**; il dominio logistico crea solo i propri **schemi** al loro interno (vedi overlay `infra/terraform/brownfield/`). Il codice notebook è già Unity-Catalog-native (nomi a 3 livelli `catalog.schema.table` via `get_catalog()`); lo shim locale collassa a 2 livelli solo su Hive/Derby. Il path di landing/warehouse è astratto in `lib/logistica_utils/storage.py` (`is_databricks()` + `get_landing_root()`), così la migrazione non tocca i notebook. Decisioni D1-D5 **chiuse** (02-03/07/2026): controllo=`config_dev` (D1), anagrafiche in `bronze_<env>.condiviso` (D2), landing UC Volume (D3), prod=`_prod`/stage=`_stage` (D4), quadratura via export su landing (D5). Compute serverless; Git multi-repo in subgroup `logistico`. Vedi `10_piano_migrazione_databricks.md`, `11_devops_handoff_databricks.md`, `12_checklist_infra_setup.md`. **Ingestion in push via AzCopy** ([[ADR-0023]], deciso 2026-08-31 al posto di SFTP; a tendere via processi ODI) dai sorgenti → nessuna connettività Oracle/VNet su Databricks. `landing_mode` external vs managed (C6) da confermare.

---

## 3. Sorgenti Dati — 4 Sistemi

| Sistema | Tipo | Note |
|---------|------|------|
| **LOGISTIX** | Oracle multi-sito | 22 db-link (laix, lbvx…lsvx). Tabelle STO_*, STORICO_*, PESATE, TRACCIACE178, TABGEN, anagrafiche |
| **STAT** (CND) | Oracle mono-sito | T_STOCK, T_PDV, T_VETTORI, T_TRASP_MTV, BUONI_ECO, TIPO_ATTIVITA_ECO |
| **CDT_ESTR_RAW** | Oracle mono-sito | STORICO_LISTE, STORICO_BOLLE, STORICO_RIEPILOGHI, CARTELLINO, CORSIE, AREE_MERCEOLOGICHE, DETTAGLIO_CARR |
| **TRACK** | Oracle mono-sito | SPEDIZIONI, VETTORI, AUTOMEZZI (accesso @TRACK via db-link) |

---

## 4. Ambiente di Sviluppo Locale (Docker)

Il sistema è **completamente sviluppato e validato in locale** prima del deploy su Databricks. L'ambiente locale replica il comportamento produzione.

```
Host Windows (C:\PROGETTI\LOGISTICO\)
    │
    ├── C:\PROGETTI\LOGISTICO_DATA\   (dati reali — fuori dal repo git)
    │     ├── LOGISTIX_DATA/          (CSV per sito: laix/, lbvx/, ..., lsvx/)
    │     ├── STAT_DATA/
    │     ├── CDT_ESTR_DATA/
    │     └── TRACK_DATA/
    │
    └── Container: logistico-spark (Docker)
          ├── Spark locale (pyspark, delta-spark)
          ├── Derby metastore (sessione singola per volta — OP-36)
          └── /workspace/code → mount del repo
```

**Runner di test:**
- `tests/local_bronze/run_all_bronze.py --run-date YYYY-MM-DD` — esegue 39 notebook bronze
- `scripts/rerun_1_bronze.ps1`, `rerun_2_silver.ps1`, `rerun_3_gold.ps1` — per fase (anti-SIGKILL OP-36)
- `scripts/rerun_22siti.ps1` — full pipeline bronze+silver+gold in sessioni docker separate

**Limitazioni note:**
- Derby metastore: una sola sessione Spark alla volta
- Ordinamento notebook alfabetico (no DAG): silver_t_stock [8] < silver_catena_unificata [20] → 0 righe sul giorno (fisiologico, OP-29)
- SIGKILL accumulo memoria su run molto lunghi → workaround `--only FASE` (OP-36)

---

## 5. Inventario Notebook (Stato 2026-06-18)

| Layer | Notebook | Stato |
|-------|----------|-------|
| Bronze | 39 (22 siti × multi-tabella Logistix + STAT + CDT_ESTR_RAW + TRACK) | ✅ Tutti OK |
| Silver clean | ~20 notebook (per ogni tabella sorgente) | ✅ Tutti OK |
| Silver prep | ~26 notebook (elaborazioni intermedie + prep per fatto) | ✅ Tutti OK |
| Gold dim | 7 dimensioni (sito, operatore, corriere, topografia, articolo, fornitore, pdv) + dim_calendario + dim_struttura_merceologica | ✅ Tutti OK |
| Gold fact | 6 fact (F_CARICO, F_PREP_SPED, F_TRASPORTO, F_GIACENZE_DAILY, F_TRACCIABILITA_LOTTI, F_TURNO) | ✅ Tutti OK |
| Gold datamart | 6 DataMart (dm_inbound, dm_stock, dm_outbound, dm_produttivita, dm_giacenze, dm_turno_prep_sito) | ✅ Tutti OK |

**Ultimo run completo (2026-06-17):** Bronze 36/36 ✅ | Silver 45/45 ✅ | Gold 26/26 ✅

---

## 6. Pattern e Convenzioni Tecniche

### 6.1 Naming Convention

```
Tabelle Bronze:    {catalog_bronze}.logistica.{nome_tabella_sorgente}[_{sito}]
Tabelle Silver:    {catalog_silver}.logistica.{nome_business}
                   {catalog_silver}.logistica_curated.{nome_prep}
Tabelle Gold Core: gold_prod.logistica.{prefisso}_{nome}
  Prefissi Gold:   dim_  (dimensioni)
                   f_    (fact tables)
                   LU_   (lookup condivise)
Tabelle DataMart:  gold_prod.logistica_dm.dm_{nome}
SQL KPI Views:     gold_prod.logistica.kpi_{nome}
Control:           control_{env}.etl.watermark
                   control_{env}.parametri.*

Notebook:          {livello}_{area}_{nome}.py
Workflow YAML:     logistica_{area}.yml
```

### 6.2 Idempotenza (MERGE INTO ovunque)

| Livello | Strategia |
|---------|-----------|
| Bronze (transazionale) | MERGE INTO su chiave naturale + `_row_hash` pruning (update solo se riga cambiata) |
| Bronze (anagrafica) | Full-load con replaceWhere su data batch |
| Silver clean | MERGE INTO su chiave naturale business (null-safe `<=>`) |
| Silver prep | MERGE upsert su chiave impattata (pattern #2) |
| Gold Core (fatti giornalieri) | replaceWhere su data |
| Gold Core (fatti cumulativi) | MERGE INTO su chiave naturale composita |
| Gold DataMart | replaceWhere su anno/mese |

### 6.3 surrogate_key_fallback — Semantica dei valori sentinel

```python
surrogate_key_fallback(col, lu_df, lu_pk,
    default_val="-1",   # orphan VERO: codice presente in sorgente ma non in dim
    null_val="ND"       # NULL sorgente: dimensione non rilevata/applicabile
)
```

- **`-1` (SCONOSCIUTO):** codice presente nel fact ma non ancora in dim → late-arriving, da ri-risolvere (OP-32)
- **`ND` (NON_RILEVATO):** NULL nel sorgente → membro dedicato in dim, semanticamente corretto

### 6.4 Gestione NULL nelle chiavi MERGE

Tutte le chiavi MERGE usano **null-safe equality** (`<=>` in Spark, `eqNullSafe()`):
```python
condition = "tgt.k1 <=> src.k1 AND tgt.k2 <=> src.k2"
```
Non usare `=` su colonne nullable (produce mismatch su NULL vs NULL).

### 6.5 Sicurezza — Read-Only Oracle

**Per nessun motivo eseguire UPDATE/INSERT sugli schemi Oracle sorgente** (LOGISTIX, STAT, CDT_ESTR_RAW, TRACK). L'Oracle è in sola lettura. Qualsiasi marcatura di record come "letti" è proibita. I flag legacy `*_DATA_ESTRAZIONE_DWH` NON sono usabili per questo motivo.

---

## 7. Regole di Business Critiche

### 7.1 Regola 30 Minuti Attrezzaggio (F_PREP_SPED)

```
Per ogni (cod_operatore, data_prep, cod_sito):
  - Sessione rank=1 (prima del giorno): ore_produttive = MAX(0, durata_minuti - 30) / 60
  - Sessioni rank>1: ore_produttive = durata_minuti / 60
  
produttivita_colli_ora = CASE
  WHEN SUM(ore_produttive) > 0 THEN colli_preparati / SUM(ore_produttive)
  ELSE 0
END
```

**Test coperti (9 test pytest):** 2h→1.5h, 20min→0, 30min→0, 31min→1/60h, multi-sito, protezione /0.

### 7.2 Calcolo Costo Trasporto a Fasce Peso

```sql
costo_stimato = CASE
  WHEN peso_kg <= 30   THEN tariffa_fascia_a * peso_kg
  WHEN peso_kg <= 100  THEN tariffa_fascia_b * peso_kg
  WHEN peso_kg <= 300  THEN tariffa_fascia_c * peso_kg
  ELSE                      tariffa_fascia_d * peso_kg
END * 1.2  -- fallback +20% se corriere non in contratto
```

### 7.3 Incrementalità Bronze — Row Hash Pruning

```python
# Solo le righe cambiate vengono re-datate (propagazione delta reale ~22%)
bronze_df = add_row_hash(bronze_df)  # SHA-256 colonne business
MERGE ON chiave
WHEN MATCHED AND tgt._row_hash <> src._row_hash THEN UPDATE  # ← solo se cambiato
WHEN NOT MATCHED THEN INSERT
```

---

## 8. Watermark / Controllo Incrementale (OP-35)

### 8.1 Problema risolto

Senza watermark: il catch-up di N giorni di solo-landing richiedeva N run sequenziali. Con watermark: un solo run processa il range completo (`_bronze_load_date > process_from`).

### 8.2 Modello dati

**Tabella:** `control_<env>.etl.watermark`  
**Chiave MERGE:** `(stage, sistema, tabella, sito)`

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| `stage` | STRING | `landing_to_bronze` \| `bronze_to_clean` \| `clean_to_prep` |
| `sistema` | STRING | `logistix` \| `stat` \| `track` \| `cdt_estr_raw` |
| `tabella` | STRING | nome tabella, es. `storico_liste` |
| `sito` | STRING | sito logistix oppure `_ALL_` per mono-sito |
| `last_processed_date` | DATE | ultima data processata con successo |
| `esito` | STRING | `OK` \| `FAIL` |
| `rows_processed` | BIGINT | diagnostico |
| `message` | STRING | nota/errore su FAIL |

**Regola transazionale critica:** `update_watermark` avanza `last_processed_date` **solo su esito OK** (dopo che il target è stato scritto). Su FAIL scrive l'errore senza avanzare → il retry riparte esattamente dalla data fallita.

### 8.3 Stato implementativo (2026-06-14)

| Step | Stato |
|------|-------|
| Helper (`get_control_table`, `ensure_watermark_table`, `read_watermark`, `update_watermark`, `pending_landing_dates`) | ✅ Fatto |
| Layer `control` in `get_catalog` | ✅ Fatto |
| `config_dev_etl` in `DB_NAMES` runner locale (D1: config_dev) | ✅ Fatto |
| Test `test_watermark.py` (7 scenari — ALL_OK) | ✅ Fatto |
| Pilota `silver_storico_liste_clean` (catch-up 2 giorni → 1 run) | ✅ Fatto |
| Rollout altri clean (storico_bolle, carichi, spedizioni, ordini) | ⏳ Pendente |
| Stage `landing_to_bronze` nell'orchestratore | ⏳ Pendente |
| Deploy Terraform control catalog a regime | ⏳ Pendente |

**Dettaglio design:** `docs/Archive/Design - Watermark ETL (OP-35).md`.

---

## 9. Architettura Produzione — Workflow Databricks (8 job)

| File | Schedule | Descrizione |
|------|----------|-------------|
| `workflows/logistica_landing_ingestion.yml` | 00:30 | CSV/Parquet da ADLS landing zone → Bronze MERGE INTO Delta (tutti i Bronze) |
| `workflows/logistica_dim_refresh.yml` | 01:00 | Bronze→Silver→Gold dimensioni (fan-out parallelo) |
| `workflows/logistica_carichi.yml` | 02:00 | Bronze→Silver→Gold carichi, pesate, giacenze daily |
| `workflows/logistica_giacenze.yml` | 03:30 | Bronze→Silver→Gold giacenze |
| `workflows/logistica_prep_sped.yml` | 04:30 | Bronze→Silver→Gold preparazione spedizioni |
| `workflows/logistica_trasporti.yml` | 05:00 | Bronze→Silver→Gold trasporti e ordini |
| `workflows/logistica_aggregati.yml` (job `logistica_datamart`) | 06:00 | 6 DataMart in parallelo (schema gold_prod.logistica_dm) |

> **Wave E non ha un workflow dedicato** (ACT_9008): la **tracciabilità CE178** è orchestrata in
> `logistica_carichi.yml` (task `silver_tracciabilita_lotto`, `gold_f_tracciabilita_lotti`) e i
> **carrellisti** in `logistica_prep_sped.yml` (`bronze_dettaglio_carr`, `bronze_imbfmovim`,
> `silver_missione/sessione_carrellista`, `gold_f_movimentazione_carrellisti`). Il placeholder
> `logistica_wave_e.yml` (deprecato, `tasks: []`) è stato **rimosso** il 2026-08-04.

---

## 10. Checklist Go-Live (riepilogo)

### Provisioning Infrastruttura (DevOps)
- [ ] Provisioning Azure Databricks Workspace prod
- [ ] Azure ADLS Gen2 storage account + container landing
- [ ] `terraform apply` (unity_catalog: schemi, Volume/external location landing, grants) — **nessuna
      risorsa compute**: i job girano su serverless e le cluster policy non si applicano (ADR-0009, ACT_9007)
- [ ] ~~Azure Key Vault + Databricks Secret Scope~~ → **non necessario** (D5/ADR-0005: nessun segreto Oracle).
      Auth CI **via Managed Identity** (no secret di deploy) — già attiva in DEV (2026-08-27)
- [ ] Storage Credential separata per dominio Logistica (Gap #3)
- [x] ~~GitLab secrets → Databricks Secret Scope~~ → superato: **auth via Managed Identity**, nessun secret (Gap #5)

### Configurazione Sorgenti
- [ ] Configurazione push CSV/Parquet sistemi sorgente → ADLS (Logistix 22 siti, CND/STAT)
- [ ] Validazione formato file (delimiter, encoding UTF-8, header row, CSV vs Parquet)
- [ ] SLA completamento push confermati (OP-09)

### Deploy Applicativo
- [ ] `databricks bundle deploy --target prod` (**7** workflow visibili in Databricks Jobs UI)
- [ ] `logistica_utils`: wheel dichiarato come dipendenza nell'`environments` dei job serverless
      (non più "cluster library" — ACT_9007); su GitLab pubblicato nel Package Registry (ADR-0016)
- [ ] GitLab CI/CD PROD: gate manuale sui tag `v*` (in DEV: `deploy_dev` già verde via MSI, 7 job)
- [ ] Supporto Parquet implementato nei Bronze (Gap #2)

### Validazione
- [ ] Test E2E primo carico completo (landing → Bronze → Silver → Gold → DataMart)
- [ ] Record count vs sorgente Oracle delta < 0.1%
- [ ] Orphan rate tutti i fact < 1% (target 0.0%)
- [ ] KPI views: confronto vs CDT_DW storico (scostamento < 1%)
- [ ] Schema definitivo lookup master Retail (OP-02) confermato da Reply

### Shadow Mode & Cut-Over
- [ ] 10 giorni lavorativi shadow run parallelo
- [ ] Scostamento KPI < 1% per tutti i 10 KPI monitorati
- [ ] Rollback plan testato in DEV e approvato
- [ ] Formazione utenti BI + MicroStrategy connection

---

## Riferimenti
- `docs/Archive/Documento di Sviluppo Finale.md` — inventario completo deliverable (v2.0, 2026-05-30)
- `docs/Archive/Design - Watermark ETL (OP-35).md` — design watermark completo (2026-06-14)
- `docs/main/03_pipeline_mapping.md` — mapping sorgente→layer completo
- `docs/main/03_linee_guida.md` — contratto di sviluppo per area
- `docs/main/10_piano_migrazione_databricks.md` — piano migrazione brownfield + decisioni D1-D5
- `docs/main/11_devops_handoff_databricks.md` — handoff DevOps: Terraform brownfield, Git multi-repo, DAB
- `docs/main/12_checklist_infra_setup.md` — checklist infra + mail al cliente + stato punti aperti
- `docs/main/milestones/` — deliverable di chiusura per fase (fase_0…fase_8); assorbono i vecchi `fasi/F*` (archiviati in `docs/Archive/fasi/`)
- `docs/main/sprint_agile/` — master SAL settimanali per sprint (0.1…8.4)
- `DOCS/piani/cutover_plan.md` — piano cut-over (T-7gg→T=08:00, 15 smoke test)
- `DOCS/piani/rollback_plan.md` — procedura rollback 6 step
- `DOCS/runbook.md` — runbook operativo
