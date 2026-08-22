# Piano di Sviluppo — Logistico 2.0
## Migrazione Oracle → Databricks (Medallion Architecture)

**Versione:** 1.0  
**Data:** 2026-05-29  
**Progetto:** Logistico 2.0 — CNO Data Platform  
**Stack:** PySpark · Spark SQL · Delta Lake · Azure ADLS Gen2 · Unity Catalog · Databricks Workflows · GitLab CI/CD · Terraform  

---

## Indice

1. [Principi Guida](#1-principi-guida)
2. [Struttura delle Fasi e Wave](#2-struttura-delle-fasi-e-wave)
3. [FASE 0 — Fondamenta Infrastrutturali](#fase-0--fondamenta-infrastrutturali)
4. [FASE 1 — Master Data & Dimensioni Condivise](#fase-1--master-data--dimensioni-condivise)
5. [FASE 2 — Wave A: Area Carichi (Inbound)](#fase-2--wave-a-area-carichi-inbound)
6. [FASE 3 — Wave B: Area Giacenze (Stock)](#fase-3--wave-b-area-giacenze-stock)
7. [FASE 4 — Wave C: Area Preparazione Spedizioni (Picking)](#fase-4--wave-c-area-preparazione-spedizioni-picking)
8. [FASE 5 — Wave D: Area Trasporti (Outbound)](#fase-5--wave-d-area-trasporti-outbound)
9. [FASE 6 — Wave E: Tracciabilità CE 178 & Movimentazione Carrellisti](#fase-6--wave-e-tracciabilità-ce-178--movimentazione-carrellisti)
10. [FASE 7 — KPI Aggregati & Layer Reporting](#fase-7--kpi-aggregati--layer-reporting)
11. [FASE 8 — Shadow Mode, Validazione & Cut-Over](#fase-8--shadow-mode-validazione--cut-over)
12. [Matrice Dipendenze Inter-Sprint](#matrice-dipendenze-inter-sprint)
13. [Rischi e Mitigazioni](#rischi-e-mitigazioni)

---

## 1. Principi Guida

| # | Principio | Implicazione pratica |
|---|-----------|----------------------|
| 1 | **Idempotenza** | Ogni notebook/job deve poter essere rieseguito senza effetti collaterali. Usare MERGE INTO / replaceWhere su Delta. |
| 2 | **Zero Data Loss** | Anagrafiche mancanti → surrogate key -1 (COALESCE), mai scarto silenzioso. |
| 3 | **Separazione Layer** | Bronze: append-only raw. Silver: cleansed 1:1 con sorgente. Gold: modello dimensionale. Nessun salto di layer. |
| 4 | **Testabilità** | Ogni notebook ha un corrispondente test di data quality (volumetria, null check, referential integrity) eseguibile standalone. |
| 5 | **Autonomia dello Sprint** | Ogni task è completabile in 5-10 gg lavorativi da un singolo sviluppatore/coppia senza blocchi cross-team (eccetto pre-requisiti espliciti). |
| 6 | **Shadow Mode** | Ogni area funzionale viene eseguita in parallelo con Oracle per ≥ 10 giorni lavorativi prima del cut-over. |
| 7 | **GitLab First** | Tutto il codice, i notebook e i Terraform plan viaggiano via GitLab. I deploy su Databricks avvengono solo tramite CI/CD pipeline. |

---

## 2. Struttura delle Fasi e Wave

```
FASE 0  ─── Infrastruttura & DevOps Foundation          [Sprint 0.1 – 0.3]
FASE 1  ─── Master Data & Dimensioni Condivise           [Sprint 1.1 – 1.3]
FASE 2  ─── Wave A: Carichi                              [Sprint 2.1 – 2.4]
FASE 3  ─── Wave B: Giacenze                             [Sprint 3.1 – 3.4]
FASE 4  ─── Wave C: Preparazione Spedizioni              [Sprint 4.1 – 4.5]
FASE 5  ─── Wave D: Trasporti                            [Sprint 5.1 – 5.4]
FASE 6  ─── Wave E: Tracciabilità & Carrellisti          [Sprint 6.1 – 6.3]
FASE 7  ─── KPI Aggregati & Reporting                    [Sprint 7.1 – 7.3]
FASE 8  ─── Shadow Mode, Validazione & Cut-Over          [Sprint 8.1 – 8.4]
```

Le Fasi 2–6 sono **parallelizzabili** tra loro dopo il completamento di Fase 0 e Fase 1.  
Le wave successive di ogni area (Silver → Gold) dipendono dalla wave Bronze della stessa area.

---

## FASE 0 — Fondamenta Infrastrutturali

> **Obiettivo:** Ambiente Databricks funzionante, CI/CD attiva, struttura Unity Catalog creata, connettività ai sorgenti Oracle verificata.  
> **Pre-requisito:** Nessuno.  
> **Output:** Ambiente DEV e PROD pronti; pipeline GitLab → Databricks attiva; accesso JDBC verificato.

---

### Sprint 0.1 — Unity Catalog & Storage Foundation
**Durata:** 7 giorni lavorativi  
**Team:** Infrastructure Engineer + Data Engineer senior  
**Pre-requisiti:** Sottoscrizione Azure attiva, Databricks Workspace esistente, Service Principal creato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 0.1.1 | **Creazione cataloghi Unity Catalog** | Creare via Terraform: `bronze_dev`, `bronze_prod`, `silver_dev`, `silver_prod`, `gold_dev`, `gold_prod`, `control_dev`, `control_prod` (dev e prod separati e speculari su tutti i livelli). Applicare tagging (environment, domain=logistica, owner). | 8 cataloghi creati e verificati in UI |
| 0.1.2 | **Creazione schemi per dominio logistico** | Schema `logistica` (bronze, silver, gold); `prep_logistica` (silver); `logistica_dm` (gold); `etl` + `parametri` (control). Le anagrafiche master Retail sono condivise in lettura (LU_*, schema TBD OP-01/02), NON uno schema "condiviso" nostro in bronze/silver. | Schema creati con commenti descrittivi |
| 0.1.3 | **Storage Credential & External Location** | Registrare Access Connector su ADLS Gen2 in Unity Catalog. Creare External Location per path `abfss://logistica@<storage>.dfs.core.windows.net/`. Verificare accesso read/write. | External Location testata con `LIST` e `PUT` |
| 0.1.4 | **Azure Key Vault + Databricks Secret Scope** | Configurare Key Vault con segreti: `oracle-logistix-jdbc-url`, `oracle-logistix-user`, `oracle-logistix-password`, `oracle-exadata-*`. Creare Databricks Secret Scope puntato a Key Vault. | Secret leggibili da notebook con `dbutils.secrets.get()` |
| 0.1.5 | **Cluster Policy & Job Compute** | Definire cluster policy per job (node type, auto-terminate, Spark config standard). Separare cluster DEV (interattivo) da PROD (job-only). | Policy applicata, cluster di test avviato e terminato correttamente |
| 0.1.6 | **Terraform state & moduli** | Inizializzare Terraform backend su Azure Blob Storage. Strutturare moduli: `unity_catalog`, `compute`, `networking`. | `terraform plan` verde, `terraform apply` eseguito su DEV |
| 0.1.7 | **Validazione accessi e permessi** | Verificare che il Service Principal abbia solo i permessi necessari (least privilege): READ su sorgenti, WRITE su ADLS logistica, USE CATALOG su cataloghi assegnati. | Checklist permessi completata e firmata |

**Criteri di Accettazione Sprint 0.1:**
- [ ] Gli 8 cataloghi (bronze/silver/gold/control × dev/prod) esistono in Unity Catalog e sono visibili in Data Explorer
- [ ] Un notebook di test legge un secret da Key Vault senza errori
- [ ] `terraform apply` idempotente (seconda esecuzione: 0 changes)

---

### Sprint 0.2 — GitLab CI/CD & Databricks Asset Bundles
**Durata:** 5 giorni lavorativi  
**Team:** DevOps Engineer + Data Engineer  
**Pre-requisiti:** Sprint 0.1 completato, GitLab repository creato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 0.2.1 | **Struttura repository GitLab** | Definire layout cartelle: `infra/terraform/`, `notebooks/bronze/`, `notebooks/silver/`, `notebooks/gold/`, `workflows/`, `tests/`, `lib/`. Aggiungere `.gitignore`, `README.md`, branch protection su `main`. | Repository strutturato, branch `develop` e `main` creati |
| 0.2.2 | **Databricks Asset Bundles (DAB) setup** | Creare `databricks.yml` con target `dev` e `prod`. Mappare variabili di ambiente (catalog, schema, cluster_id). | `databricks bundle validate` verde |
| 0.2.3 | **Pipeline GitLab CI - Stage DEV** | Definire `.gitlab-ci.yml`: stage `validate` (lint PySpark, SQL format check), stage `deploy-dev` (bundle deploy su DEV). Trigger su push a `develop`. | Push su develop → deploy automatico su DEV Databricks |
| 0.2.4 | **Pipeline GitLab CI - Stage PROD** | Stage `deploy-prod` protetto (manual approval). Trigger su merge request approvata su `main`. | MR approvata → deploy su PROD (con gate manuale) |
| 0.2.5 | **Libreria Python condivisa (lib/)** | Creare package `logistica_utils`: funzioni comuni per secret reading, logging strutturato, Delta merge helper, data quality checks. Pubblicare come wheel su Databricks Volumes. | `from logistica_utils import delta_merge` funzionante in notebook |

**Criteri di Accettazione Sprint 0.2:**
- [ ] Push su branch `develop` trigghera pipeline e deploya notebook su DEV
- [ ] `logistica_utils` wheel installabile da Databricks cluster
- [ ] Struttura repository documentata in `README.md`

---

### Sprint 0.3 — Connettività Sorgenti Oracle & Test Ingestion
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer + DBA Oracle (supporto)  
**Pre-requisiti:** Sprint 0.1 e 0.2 completati. Accesso di rete ai database sorgenti.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 0.3.1 | **Test connettività JDBC Oracle → Databricks** | Verificare raggiungibilità network (NSG, firewall) da Databricks cluster verso Oracle Logistix, Oracle Exadata. Testare con `spark.read.format("jdbc")` su una tabella piccola (es. tabella di codici). | SELECT di 10 righe da Oracle Logistix riuscito |
| 0.3.2 | **Benchmark performance JDBC** | Misurare throughput JDBC su tabelle grandi (STO_TES_CARICHI ~500K righe, GIACENZE_DAILY ~2M righe). Valutare partitioning JDBC (`numPartitions`, `partitionColumn`, `lowerBound`, `upperBound`). | Report con tempi di estrazione e configurazione ottimale per tabella |
| 0.3.3 | **Validare strategia di ingestion per sorgente** | Per ogni sorgente: decidere JDBC full-load vs JDBC incremental (watermark su colonna data). Documentare in tabella di decisione. Raccogliere lista completa tabelle sorgente per dominio logistico. | Decision matrix ingestion strategy per tabella |
| 0.3.4 | **Notebook template Bronze** | Creare template notebook PySpark parametrizzato: lettura JDBC con watermark, write Delta append-only, logging metadati (righe lette, righe scritte, data_run). | Template verificato su una tabella campione |
| 0.3.5 | **Notebook template Silver** | Creare template notebook Spark SQL: lettura Bronze Delta, deduplicazione (ROW_NUMBER per chiave), type casting, MERGE INTO Silver. Gestione nullable e default. | Template verificato su dato campione |
| 0.3.6 | **Notebook template Gold Fact** | Creare template notebook Spark SQL: lettura Silver + dimensioni, JOIN con surrogate key fallback (-1), replaceWhere Delta su partizione data. | Template verificato su dato campione |
| 0.3.7 | **Definire standard logging & alerting** | Integrare logging strutturato (JSON) su ogni notebook. Configurare Databricks Workflows alert su failure (email/Teams webhook). | Alert email ricevuta su job di test fallito intenzionalmente |

**Criteri di Accettazione Sprint 0.3:**
- [ ] Connessione JDBC a tutti i database sorgente verificata con SELECT di test
- [ ] I 3 template (Bronze, Silver, Gold) eseguibili senza errori su dati campione
- [ ] Alert notifica configurata e testata

---

## FASE 1 — Master Data & Dimensioni Condivise

> **Obiettivo:** Costruire tutte le dimensioni condivise in `gold_prod` (Calendario, Articoli, Fornitori, PDV, Siti, Operatori, Corrieri). Sono prerequisito per tutte le Fact Table.  
> **Pre-requisiti:** Fase 0 completata.  
> **Output:** Tabelle `gold_prod.logistica.*` e `gold_prod.condiviso.*` popolate e validate.

---

### Sprint 1.1 — Dimensione Calendario & Strutture Merceologiche
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 0.x completati.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 1.1.1 | **DIM_CALENDARIO** | Generare in PySpark tabella calendario da 2018-01-01 a 2030-12-31. Attributi: GIORNO_ID (INT YYYYMMDD), DATA (DATE), ANNO, SEMESTRE, TRIMESTRE, MESE, SETTIMANA_ISO, GIORNO_SETTIMANA, FLAG_FESTIVO_IT, FLAG_LAVORATIVO. Caricare in `gold_prod.condiviso.dim_calendario`. | Tabella con ~4.400 righe, zero null su GIORNO_ID |
| 1.1.2 | **DIM_MESE, DIM_TRIMESTRE, DIM_ANNO** | Generare tabelle aggregate di calendario per drill-down MicroStrategy. Attributi coerenti con DIM_CALENDARIO. | 3 tabelle caricate |
| 1.1.3 | **DIM_STRUTTURA_MERCEOLOGICA** | Estrarre da Oracle (sorgente anagrafica CDR/merceologie): MACRO_AGGREGATO, AGGREGATO, CATEGORIA, SOTTOCATEGORIA, CODICE_MERCE. MERGE INTO Silver, poi MERGE INTO Gold. | Tabella in `gold_prod.condiviso` con gerarchia 5 livelli |
| 1.1.4 | **Test DQ Calendario** | Verificare: nessun buco di date, FLAG_FESTIVO corretto per almeno 5 festività note, COUNT = atteso. | Test automatico verde |

**Criteri di Accettazione Sprint 1.1:**
- [ ] DIM_CALENDARIO contiene tutte le date nell'intervallo richiesto
- [ ] DIM_STRUTTURA_MERCEOLOGICA caricata con gerarchia completa a 5 livelli
- [ ] Test DQ verde (suite pytest o notebook di validazione)

---

### Sprint 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 1.1 completato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 1.2.1 | **Bronze: tabelle anagrafiche Oracle** | Ingestion JDBC di: ART_ARTICOLI (o equivalente), ART_RADICI, FORNITORI, PUNTI_VENDITA, CODICI_PDV. Append-only, con timestamp_ingestion. | Tabelle Bronze caricate |
| 1.2.2 | **Silver DIM_ARTICOLO** | Deduplica per ART_COD (max VERSION o max DATA_AGG). Cast tipologici. Attributi: ART_ID, ART_COD, ART_DESCR, RADICE_ID, RADICE_DESCR, MACRO_AGG_MERCL, FLAG_ATTIVO. MERGE INTO Silver. | Tabella Silver senza duplicati per ART_COD |
| 1.2.3 | **Silver DIM_FORNITORE** | Deduplica per FORNITORE_ID. Attributi: FORNITORE_ID, FORNITORE_DESCR, NAZIONE, CATEGORIA_FORNITORE, FLAG_ATTIVO. MERGE INTO Silver. | Tabella Silver senza duplicati |
| 1.2.4 | **Silver DIM_PDV** | Deduplica per PDV_ID. Attributi: PDV_ID, PDV_DESCR, REGIONE, AREA_COMMERCIALE, TIPOLOGIA_PDV, FLAG_ATTIVO, CODICE_SOCI. MERGE INTO Silver. | Tabella Silver senza duplicati |
| 1.2.5 | **Gold DIM_ARTICOLO** | MERGE INTO `gold_prod.condiviso.dim_articolo` con SCD Type 1 (overwrite attributi descrittivi). Join con DIM_STRUTTURA_MERCEOLOGICA per denormalizzare gerarchia. | Tabella Gold con gerarchia merceologica denormalizzata |
| 1.2.6 | **Gold DIM_FORNITORE, DIM_PDV** | Analoga a sopra. | 2 tabelle Gold caricate |
| 1.2.7 | **Test DQ Anagrafiche** | Verifica: nessun ART_ID duplicato in Gold, nessun FK null tra DIM_ARTICOLO e DIM_STRUTTURA_MERCEOLOGICA, COUNT confrontato con Oracle (±0%). | Test DQ verde, report di confronto |

**Criteri di Accettazione Sprint 1.2:**
- [ ] DIM_ARTICOLO, DIM_FORNITORE, DIM_PDV in Gold popolate e senza duplicati
- [ ] Confronto volumetrico con Oracle: differenza ≤ 0.1%
- [ ] Pipeline CI/CD deploya i notebook su DEV senza errori

---

### Sprint 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 1.1 completato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 1.3.1 | **Bronze: siti logistici, operatori, corrieri** | Ingestion JDBC di: MAG_SITI, OPERATORI, OPERATORI_SOCI, CORRIERI, CONTRATTI_CORRIERI. Append-only. | Tabelle Bronze caricate |
| 1.3.2 | **Silver DIM_SITO_LOGISTICO** | Deduplica per MAG_SITO_ID. Attributi: SITO_ID, SITO_DESCR, TIPOLOGIA (MAGAZZINO/PIATTAFORMA), REGIONE, SUPERFICIE_MQ, CAPACITA_PALLET, FLAG_ATTIVO. | Silver senza duplicati |
| 1.3.3 | **Silver DIM_OPERATORE** | Deduplica per OPERATORE_ID. Attributi: OPERATORE_ID, NOME, COGNOME, MATRICOLA, TIPOLOGIA (CARRELLISTA/PICKER/CAPO_TURNO), SITO_ID, FLAG_ATTIVO. | Silver senza duplicati |
| 1.3.4 | **Silver DIM_CORRIERE** | Deduplica per CORRIERE_ID. Attributi: CORRIERE_ID, CORRIERE_DESCR, TIPO_SERVIZIO, FLAG_ATTIVO. | Silver senza duplicati |
| 1.3.5 | **Silver DIM_TOPOGRAFIA_MAGAZZINO** | Struttura gerarchica: CORSIA → SCAFFALE → LIVELLO → CELLA. Attributi per cella: CAPACITA_UM, TIPO_STOCCAGGIO. | Silver con gerarchia 4 livelli |
| 1.3.6 | **Gold DIM_SITO, DIM_OPERATORE, DIM_CORRIERE, DIM_TOPOGRAFIA** | MERGE INTO `gold_prod.logistica.*`. SCD Type 1 per tutti. | 4 tabelle Gold caricate |
| 1.3.7 | **Workflow Databricks: dim_refresh** | Creare Databricks Workflow `logistica_dim_refresh` con task chain: Bronze → Silver → Gold per tutte le dimensioni. Schedulato giornalmente alle 01:00. Dependency graph corretto. | Workflow eseguito con successo end-to-end |

**Criteri di Accettazione Sprint 1.3:**
- [ ] Tutte le dimensioni logistiche caricate in Gold
- [ ] Workflow `logistica_dim_refresh` eseguito con successo (tutti i task verdi)
- [ ] DQ check: nessun OPERATORE_ID duplicato, nessun SITO_ID null

---

## FASE 2 — Wave A: Area Carichi (Inbound)

> **Obiettivo:** Migrare il flusso Oracle `CDT_ESTR.REPLICA_CARICHI` + `CDT_SA.SP_CARICO_*` + `CDT_DW.SP_LOAD_F_CARICO` in Medallion Architecture.  
> **Sorgenti Oracle:** STO_TES_CARICHI, STO_DET_CARICHI, PESATE, TRACCIACE178 (via Logistix e Exadata).  
> **Output Gold:** `gold_prod.logistica.f_carico`  
> **Pre-requisiti:** Fase 0 + Sprint 1.1, 1.2, 1.3.

---

### Sprint 2.1 — Bronze Carichi: Ingestion Layer
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Template Bronze (0.3.4), connettività Oracle (0.3.1).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 2.1.1 | **Analisi tabelle sorgente carichi** | Reverse engineering di `CDT_ESTR.REPLICA_CARICHI` e `CDT_ESTR.ESTRAI_CARICO`. Identificare tutte le tabelle Oracle lette (STO_TES_CARICHI, STO_DET_CARICHI, PESATE, TRACCIACE178, T_INIZIO_CARICO). Documentare chiavi, colonne watermark, volumi. | Documento mapping sorgente-destinazione |
| 2.1.2 | **Notebook `bronze_carichi_testate`** | JDBC da Logistix: `STO_TES_CARICHI`. Watermark su `DATA_CARICO`. Partitioning JDBC su DATA_CARICO (numPartitions=8). Append-only su `bronze_dev.logistica.sto_tes_carichi`. Schema: tutti i campi originali + `_ingestion_timestamp`, `_source_system`. | Tabella Bronze con full load storico (backfill) |
| 2.1.3 | **Notebook `bronze_carichi_dettagli`** | JDBC da Logistix: `STO_DET_CARICHI`. Watermark su `DATA_RIGA`. Append-only su `bronze_dev.logistica.sto_det_carichi`. | Tabella Bronze con full load storico |
| 2.1.4 | **Notebook `bronze_pesate`** | JDBC da Logistix: `PESATE`. Watermark su `DATA_PESATA`. Append-only su `bronze_dev.logistica.pesate`. | Tabella Bronze |
| 2.1.5 | **Notebook `bronze_traccia_ce178`** | JDBC da sorgente CE178: `TRACCIACE178`. Watermark su `DATA_TRACCIATA`. Append-only su `bronze_dev.logistica.traccia_ce178`. | Tabella Bronze |
| 2.1.6 | **Backfill storico** | Eseguire ingestion per tutto il periodo storico richiesto (tipicamente 3-5 anni). Gestire partizionamento temporale per evitare timeout. | Storico caricato, volumi verificati vs Oracle |
| 2.1.7 | **Workflow `logistica_bronze_carichi`** | Task chain: 4 notebook in parallelo (testate, dettagli, pesate, CE178). Schedulato giornalmente alle 02:00. Retry policy: 2 tentativi, wait 5 min. | Workflow eseguito con successo |

**Criteri di Accettazione Sprint 2.1:**
- [ ] Tutte e 4 le tabelle Bronze caricate con storico completo
- [ ] COUNT(*) Bronze ≈ COUNT(*) Oracle (±0.5%) per ogni tabella
- [ ] Workflow schedulato e verificato con 2 esecuzioni consecutive

---

### Sprint 2.2 — Silver Carichi: Cleansing & Deduplication
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 2.1 completato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 2.2.1 | **Analisi trasformazioni CDT_SA per Carichi** | Leggere `CDT_SA.sql` per le procedure SP_CARICO_*, SP_NORM_CARICO, SP_CHECK_CARICO. Mappare ogni trasformazione in Spark SQL equivalente. Documentare: cast tipi, gestione null, regole deduplication, business rules. | Documento di mapping PL/SQL → Spark SQL |
| 2.2.2 | **Notebook `silver_carichi_testate`** | Da Bronze `sto_tes_carichi`. Deduplicazione: ROW_NUMBER() PARTITION BY CARICO_ID ORDER BY _ingestion_timestamp DESC. Cast: DATA_CARICO → DATE, PESO_LORDO/NETTO → DECIMAL(18,4), CODICE_FORNITORE → STRING. Normalize null: COALESCE(CODICE_FORNITORE, 'SCONOSCIUTO'). MERGE INTO `silver_dev.logistica.carico_testata`. | Silver deduplicata |
| 2.2.3 | **Notebook `silver_carichi_dettagli`** | Da Bronze `sto_det_carichi`. Deduplicazione per (CARICO_ID, RIGA_ID). Cast colonne numeriche. Gestione articoli non presenti in DIM_ARTICOLO (flag `_art_non_trovato` = true, ART_ID = -1). MERGE INTO `silver_dev.logistica.carico_dettaglio`. | Silver con flag qualità |
| 2.2.4 | **Notebook `silver_pesate`** | Da Bronze `pesate`. Deduplicazione per (CARICO_ID, SEQ_PESATA). Validazione: PESO_NETTO > 0 (righe KO in colonna `_dq_peso_negativo`). MERGE INTO `silver_dev.logistica.pesata`. | Silver con DQ flag |
| 2.2.5 | **Notebook `silver_traccia_ce178`** | Da Bronze `traccia_ce178`. Deduplicazione per (LOT_ID, ART_ID, DATA_TRACCIATA). MERGE INTO `silver_dev.logistica.traccia_ce178`. | Silver deduplicata |
| 2.2.6 | **Suite test DQ Silver Carichi** | Verificare: nessun CARICO_ID duplicato in silver_carichi_testate, % record con `_art_non_trovato` < 2%, PESO_NETTO sempre ≥ 0. Eseguire come notebook separato, output come tabella Delta `silver_dev.logistica._dq_carichi`. | Notebook DQ eseguibile standalone, report leggibile |
| 2.2.7 | **Aggiornare Workflow** | Aggiungere task Silver dopo Bronze nel workflow `logistica_carichi`. Dipendenza: Silver_* dopo Bronze_*. | Workflow aggiornato, test run verde |

**Criteri di Accettazione Sprint 2.2:**
- [ ] Silver testate e dettagli senza duplicati su chiave primaria
- [ ] DQ report: % record anomali documentata e sotto soglia
- [ ] Workflow Silver eseguito end-to-end senza errori

---

### Sprint 2.3 — Gold F_CARICO: Fact Table
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 2.2 + Sprint 1.2, 1.3 (dimensioni caricate).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 2.3.1 | **Analisi `SP_LOAD_F_CARICO` Oracle** | Decostruire la stored procedure in CDT_DW.sql. Identificare: JOIN tra SA tables, aggregazioni, regole di allocazione KPI (lead time calcolo, peso netto/lordo). Documentare grain della fact: 1 riga = 1 riga di dettaglio carico. | Documento grain + trasformazioni Gold |
| 2.3.2 | **Notebook `gold_f_carico`** | Join Silver: carico_testata ⋈ carico_dettaglio ⋈ pesata (LEFT JOIN, 1 pesata per carico). Lookup dimensioni: DIM_FORNITORE, DIM_ARTICOLO, DIM_SITO, DIM_CALENDARIO. COALESCE su ogni FK → -1 se non trovato. Calcolo misure: PESO_NETTO, PESO_LORDO, QTA_RICEVUTA, QTA_ATTESA, DELTA_QTA, LEAD_TIME_GG (= DATA_CARICO - DATA_ORDINE). Partizione Delta: `anno_mese` (YYYYMM). replaceWhere su partizione del giorno elaborato. | Fact table F_CARICO in `gold_prod.logistica.f_carico` |
| 2.3.3 | **Gestione Late-Arriving Dimensions** | Per FORNITORE_ID non in DIM_FORNITORE: inserire in coda `silver_dev.logistica._dim_missing_fornitore` per riconciliazione manuale. Stessa logica per ART_ID. | Tabella di log dimensioni mancanti |
| 2.3.4 | **Test di confronto Gold vs Oracle** | Estrarre da Oracle (CDT_DW.F_CARICO) totali aggregati per mese: SUM(PESO_NETTO), SUM(QTA_RICEVUTA), COUNT(*). Confrontare con Gold. Produrre report di quadratura. | Report quadratura con differenza < 0.1% |
| 2.3.5 | **Aggiornare Workflow carichi** | Aggiungere task Gold dopo Silver. Aggiungere task DQ confronto Gold vs Oracle. | Workflow completo Bronze→Silver→Gold→DQ eseguito |

**Criteri di Accettazione Sprint 2.3:**
- [ ] F_CARICO popolata con grain corretto (1 riga = 1 riga dettaglio carico)
- [ ] Quadratura vs Oracle: SUM(PESO_NETTO) differenza ≤ 0.1% per ogni mese dell'ultimo anno
- [ ] Nessun CARICO_ID in Gold con FORNITORE_ID NULL (sostituito da -1)

---

### Sprint 2.4 — KPI Carichi & Validazione Funzionale
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst  
**Pre-requisiti:** Sprint 2.3 completato.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 2.4.1 | **Vista `gold_kpi_lead_time_fornitore`** | Aggregazione mensile su F_CARICO: AVG(LEAD_TIME_GG), MIN, MAX, PERCENTILE(0.9) per FORNITORE_ID, SITO_ID, ANNO_MESE. Vista materializzata in `gold_prod.logistica`. | Vista interrogabile da MicroStrategy |
| 2.4.2 | **Vista `gold_kpi_qualita_ricevimento`** | % righe con DELTA_QTA ≠ 0, % righe con DQ flag attivi, per FORNITORE e MESE. | Vista interrogabile |
| 2.4.3 | **Validazione funzionale con BA** | Il Business Analyst verifica i KPI su un report MicroStrategy prototipo (o query SQL diretta) su 3 mesi di dati. Confronto vs report Oracle esistente. | Sign-off funzionale (verbal o email) |
| 2.4.4 | **Documentazione area Carichi** | Aggiornare README del repository: lista tabelle Bronze/Silver/Gold, grain, descrizione misure, scheduling. | README aggiornato e committato |

**Criteri di Accettazione Sprint 2.4:**
- [ ] Viste KPI interrogabili e corrispondenti ai report Oracle
- [ ] Sign-off funzionale del Business Analyst
- [ ] README documenta il flusso end-to-end

---

## FASE 3 — Wave B: Area Giacenze (Stock)

> **Obiettivo:** Migrare `REPLICA_LOGISTIX` (fotografie giornaliere giacenze) + `CDT_SA.SP_STOCK_*` + `CDT_DW.SP_LOAD_F_GIACENZE`.  
> **Sorgenti Oracle:** GIACENZE_DAILY (snapshot), MOVIMENTI_MAGAZZINO.  
> **Output Gold:** `gold_prod.logistica.f_giacenze_daily`, `f_giacenze_monthly`  
> **Pre-requisiti:** Fase 0 + Sprint 1.x.

---

### Sprint 3.1 — Bronze Giacenze: Snapshot Giornaliero
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 0.3, 1.3.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 3.1.1 | **Analisi struttura snapshot giacenze Oracle** | Decostruire `CDT_ESTR.REPLICA_LOGISTIX` e `ESTRAI_STOCK`. Capire: la tabella Oracle è una fotografia point-in-time o accumula? Quale colonna identifica la data foto? Quale la chiave (ART_ID, SITO_ID, CELLA_ID)? | Documento struttura snapshot |
| 3.1.2 | **Notebook `bronze_giacenze_snapshot`** | JDBC full-load giornaliero (la tabella sorgente è già una fotografia). Append-only Delta con partizione su `DATA_FOTO`. Colonne: tutti i campi originali + `_ingestion_timestamp`. Tabella: `bronze_dev.logistica.giacenze_snapshot`. | Snapshot Bronze per ogni giorno storico |
| 3.1.3 | **Backfill storico giacenze** | Caricare storico disponibile (es. 2 anni). La sorgente Oracle potrebbe non avere tutto lo storico: documentare il periodo disponibile. | Backfill eseguito, periodo documentato |
| 3.1.4 | **Notebook `bronze_movimenti_magazzino`** | Se disponibile: JDBC su MOVIMENTI_MAGAZZINO. Incrementale con watermark su DATA_MOVIMENTO. | Tabella Bronze movimenti |
| 3.1.5 | **Workflow `logistica_bronze_giacenze`** | Task singolo giornaliero alle 03:00. Append snapshot del giorno. | Workflow schedulato e testato |

**Criteri di Accettazione Sprint 3.1:**
- [ ] Snapshot Bronze disponibile per ogni giorno dell'ultimo anno
- [ ] COUNT per DATA_FOTO coerente con Oracle
- [ ] Workflow schedulato

---

### Sprint 3.2 — Silver Giacenze: Normalizzazione
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 3.1.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 3.2.1 | **Analisi `SP_STOCK_*` Oracle** | Mappare trasformazioni: TO_NUMBER su peso/volume, gestione celle vuote, normalizzazione unità di misura (KG, L, PZ). | Documento mapping |
| 3.2.2 | **Notebook `silver_giacenze_daily`** | Da Bronze snapshot. Deduplicazione per (DATA_FOTO, ART_ID, SITO_ID, CELLA_ID). Cast: PESO → DECIMAL(18,4), VOLUME → DECIMAL(18,4), QTA → DECIMAL(18,4). Normalizzazione UM (converti tutto in UM base). MERGE INTO `silver_dev.logistica.giacenze_daily` con replaceWhere su DATA_FOTO. | Silver per ogni giorno senza duplicati |
| 3.2.3 | **Notebook `silver_giacenze_aggregata`** | Aggregazione giornaliera per (DATA_FOTO, ART_ID, SITO_ID): somma QTA, PESO, VOLUME, VALORE_STOCK. Serve come base per KPI saturazione. MERGE INTO `silver_dev.logistica.giacenze_agg_daily`. | Silver aggregata giornaliera |
| 3.2.4 | **DQ Silver Giacenze** | Verifica: nessun record con QTA < 0 (flag), % celle vuote, coerenza PESO vs VOLUME per categorie merceologiche note. | Report DQ |

**Criteri di Accettazione Sprint 3.2:**
- [ ] Silver daily senza duplicati su (DATA_FOTO, ART_ID, SITO_ID, CELLA_ID)
- [ ] Cast numerici corretti (nessun errore di overflow)

---

### Sprint 3.3 — Gold F_GIACENZE: Daily & Monthly
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 3.2 + Dimensioni (1.x).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 3.3.1 | **Analisi `SP_LOAD_F_GIACENZE` Oracle** | Decostruire la procedura: grain, JOIN dimensioni, misure calcolate. | Documento grain |
| 3.3.2 | **Notebook `gold_f_giacenze_daily`** | Join Silver giacenze_daily con DIM_ARTICOLO, DIM_SITO, DIM_TOPOGRAFIA, DIM_CALENDARIO. Misure: QTA_DISPONIBILE, QTA_IMPEGNATA, QTA_IN_TRANSITO, PESO_NETTO_KG, VOLUME_M3, VALORE_STOCK_EUR. replaceWhere su partizione DATA_FOTO. | F_GIACENZE_DAILY |
| 3.3.3 | **Notebook `gold_f_giacenze_monthly`** | Aggregazione mensile da F_GIACENZE_DAILY: media giornaliera, max, min, fine mese. KPI: GIORNI_COPERTURA = QTA_DISPONIBILE / AVG_VENDUTO_GIORNO (join con F_ORDINI). | F_GIACENZE_MONTHLY |
| 3.3.4 | **Vista `gold_kpi_saturazione_magazzino`** | Per SITO_ID, MESE: VOLUME_OCCUPATO / CAPACITA_SITO (da DIM_SITO). Saturazione %. | Vista KPI |
| 3.3.5 | **Vista `gold_kpi_aging_articoli`** | Articoli in giacenza per classe aging: <30gg, 30-90gg, 90-180gg, >180gg. Calcolato rispetto a DATA_PRIMO_ARRIVO. | Vista KPI aging |
| 3.3.6 | **Quadratura vs Oracle** | Confronto SUM(QTA_DISPONIBILE) per ART_ID, SITO_ID, DATA_FOTO tra Gold e CDT_DW.F_GIACENZE_DAILY Oracle. | Report quadratura |

**Criteri di Accettazione Sprint 3.3:**
- [ ] F_GIACENZE_DAILY e F_GIACENZE_MONTHLY popolate
- [ ] Quadratura QTA_DISPONIBILE ≤ 0.1% su ogni giorno dell'ultimo mese

---

### Sprint 3.4 — Workflow Giacenze & Validazione
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst  
**Pre-requisiti:** Sprint 3.3.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 3.4.1 | **Workflow completo `logistica_giacenze`** | Bronze → Silver_Daily → Silver_Agg → Gold_Daily → Gold_Monthly → KPI. Scheduling 03:30. | Workflow end-to-end eseguito |
| 3.4.2 | **Validazione funzionale giacenze** | BA verifica: saturazione magazzino, aging articoli, valore stock su report prototipo. | Sign-off funzionale |
| 3.4.3 | **Documentazione** | README area Giacenze. | Documentazione committata |

---

## FASE 4 — Wave C: Area Preparazione Spedizioni (Picking)

> **Obiettivo:** Migrare `REPLICA_PREP_SPED_NEW` + `CDT_SA.SP_AGG_ANAG_PREP_SPED*` + `CDT_DW.SP_LOAD_F_PREP_PROD_OPER`.  
> **Sorgenti Oracle:** RIEPILOGHI (testate), TESTATE_BOLLE (righe bolla), TIMBRATURE.  
> **Output Gold:** `f_prep_sped`, `f_turno_prep_sito`, KPI produttività operatori.  
> **Note:** Area più complessa: regola 30 minuti attrezzaggio, Window Functions per turni.  
> **Pre-requisiti:** Fase 0 + Sprint 1.x.

---

### Sprint 4.1 — Bronze Preparazione Spedizioni
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 0.3, 1.3 (DIM_OPERATORE disponibile).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 4.1.1 | **Analisi tabelle sorgente Prep Spedizioni** | Decostruire `CDT_ESTR.REPLICA_PREP_SPED_NEW`. Identificare: RIEPILOGHI (1 riga = 1 riepilogo turno), TESTATE_BOLLE (1 riga = 1 bolla), righe bolla (dettaglio articoli), TIMBRATURE (badge operatori). Documentare chiavi e watermark. | Mapping sorgente |
| 4.1.2 | **Notebook `bronze_prep_riepiloghi`** | JDBC RIEPILOGHI. Watermark su DATA_RIEPILOGO. Append-only `bronze_dev.logistica.prep_riepiloghi`. | Bronze Riepiloghi |
| 4.1.3 | **Notebook `bronze_prep_bolle_testate`** | JDBC TESTATE_BOLLE. Watermark su DATA_BOLLA. Append-only `bronze_dev.logistica.prep_bolle_testate`. | Bronze Testate Bolle |
| 4.1.4 | **Notebook `bronze_prep_bolle_righe`** | JDBC righe bolla. Watermark su DATA_RIGA. Append-only `bronze_dev.logistica.prep_bolle_righe`. | Bronze Righe Bolle |
| 4.1.5 | **Notebook `bronze_timbrature`** | JDBC TIMBRATURE. Watermark su DATA_TIMBRO. Append-only `bronze_dev.logistica.timbrature`. | Bronze Timbrature |
| 4.1.6 | **Backfill + Workflow Bronze** | Backfill storico 3 anni. Workflow `logistica_bronze_prep_sped` a 04:00. | Workflow schedulato |

**Criteri di Accettazione Sprint 4.1:**
- [ ] 4 tabelle Bronze caricate con storico
- [ ] COUNT verificato vs Oracle

---

### Sprint 4.2 — Silver Prep Spedizioni: Normalizzazione & Merge Testate/Righe
**Durata:** 8 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 4.1.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 4.2.1 | **Analisi `SP_AGG_ANAG_PREP_SPED3A/4A` Oracle** | Capire la logica di join tra RIEPILOGHI e TESTATE_BOLLE. Spesso: un riepilogo copre N bolle (1:N). Identificare chiave di join. | Documento logica join |
| 4.2.2 | **Notebook `silver_prep_riepiloghi`** | Deduplica per RIEPILOGO_ID. Cast: DATA_RIEPILOGO → DATE, ORE_LAVORATE → DECIMAL(6,2). MERGE INTO `silver_dev.logistica.prep_riepilogo`. | Silver Riepiloghi |
| 4.2.3 | **Notebook `silver_prep_bolle`** | Join testate ⋈ righe bolla. Deduplica per (BOLLA_ID, ART_ID). Cast colonne numeriche. Flag: bolla_annullata se FLAG_ANNULLATO = 'S'. MERGE INTO `silver_dev.logistica.prep_bolla`. | Silver Bolle (testate + righe merged) |
| 4.2.4 | **Notebook `silver_timbrature_sessioni`** | Da TIMBRATURE: calcolare sessioni di lavoro per operatore/giorno. Logica: TIMBRO_ENTRATA → TIMBRO_USCITA = 1 sessione. Gestione doppie timbrature (prendere primo IN e ultimo OUT). Window Function: LEAD/LAG su OPERATORE_ID, DATA_TIMBRO. MERGE INTO `silver_dev.logistica.sessione_operatore`. | Silver sessioni operatore |
| 4.2.5 | **Notebook `silver_prep_sped_integrata`** | Join: riepiloghi ⋈ bolle ⋈ sessioni_operatore. Grain: 1 riga = 1 bolla per operatore nel turno. Attributi arricchiti con info operatore e sito. MERGE INTO `silver_dev.logistica.prep_sped_integrata`. | Silver integrata |
| 4.2.6 | **DQ Silver Prep Spedizioni** | % bolle annullate, % sessioni senza timbratura uscita, coerenza ORE_LAVORATE vs delta ENTRATA-USCITA. | Report DQ |

**Criteri di Accettazione Sprint 4.2:**
- [ ] Silver integrata senza duplicati su chiave bolla
- [ ] Sessioni operatore corrette (nessuna sessione con durata > 16h o < 0h)

---

### Sprint 4.3 — Gold F_PREP_SPED: Fact Table Produttività
**Durata:** 8 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 4.2 + Dimensioni.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 4.3.1 | **Analisi `SP_LOAD_F_PREP_PROD_OPER` Oracle** | Identificare grain della fact, misure (COLLI_PREPARATI, ORE_LAVORATE, PRODUTTIVITA = COLLI/ORA), regola 30 minuti attrezzaggio (i primi 30 min di ogni sessione non contano per produttività). | Documento grain + business rules |
| 4.3.2 | **Implementazione regola 30 min attrezzaggio** | In PySpark/Spark SQL: per ogni sessione operatore, sottrarre 30 min dalle ORE_LAVORATE_PRODUTTIVE. Se sessione < 30 min → ORE_PRODUTTIVE = 0. Usare Window Function per identificare prima sessione del turno. | Logica testata su dataset campione |
| 4.3.3 | **Notebook `gold_f_prep_sped`** | Join Silver prep_sped_integrata con DIM_OPERATORE, DIM_SITO, DIM_ARTICOLO, DIM_CALENDARIO, DIM_PDV (destinazione). Misure: COLLI_PREPARATI, QTA_ARTICOLI, PESO_KG, ORE_LAVORATE, ORE_PRODUTTIVE, PRODUTTIVITA_COLLI_ORA, NUM_BOLLE. replaceWhere su DATA_RIEPILOGO. | F_PREP_SPED in Gold |
| 4.3.4 | **Notebook `gold_f_turno_prep_sito`** | Aggregazione per (SITO_ID, DATA, TURNO): totale colli, operatori attivi, produttività media, ore totali lavorate. Fatto aggregato complementare. | F_TURNO_PREP_SITO in Gold |
| 4.3.5 | **Quadratura vs Oracle** | Confronto SUM(COLLI_PREPARATI), SUM(ORE_PRODUTTIVE) per SITO e MESE tra Gold e CDT_DW Oracle. | Report quadratura ≤ 0.1% |

**Criteri di Accettazione Sprint 4.3:**
- [ ] F_PREP_SPED con regola 30 min implementata e validata su casi test noti
- [ ] Quadratura vs Oracle su 3 mesi recenti

---

### Sprint 4.4 — KPI Produttività & Workflow Prep Spedizioni
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst  
**Pre-requisiti:** Sprint 4.3.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 4.4.1 | **Vista `gold_kpi_produttivita_operatore`** | Per OPERATORE_ID, SITO_ID, MESE: AVG/MAX produttività, ranking operatori (RANK() Window). | Vista KPI |
| 4.4.2 | **Vista `gold_kpi_efficienza_sito_prep`** | Per SITO_ID, MESE: produttività media, ore attrezzaggio % sul totale, numero operatori distinti. | Vista KPI |
| 4.4.3 | **Workflow `logistica_prep_sped`** | Bronze → Silver_* → Gold_F_PREP_SPED → Gold_F_TURNO → KPI. Scheduling 04:30. | Workflow end-to-end |
| 4.4.4 | **Validazione funzionale con BA** | BA verifica produttività operatori su report prototipo. Confronto con report Oracle. | Sign-off funzionale |

---

### Sprint 4.5 — Gestione Anomalie & Edge Cases Prep Spedizioni
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 4.4.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 4.5.1 | **Gestione operatori non in DIM_OPERATORE** | Operatori nuovi non ancora in anagrafica: inserire in `silver_dev.logistica._dim_missing_operatore`. OPERATORE_ID = -1 in fact. | Tabella di log missing + logica COALESCE |
| 4.5.2 | **Gestione bolle annullate** | Bolle con FLAG_ANNULLATO = 'S': escluderle da F_PREP_SPED (non contribuiscono a produttività). Contarle separatamente in KPI `gold_kpi_bolle_annullate`. | Logica implementata, vista KPI |
| 4.5.3 | **Gestione turni a cavallo di mezzanotte** | Sessioni che iniziano in giorno D e finiscono in giorno D+1: logica di attribuzione (data bolla vs data riepilogo). Regola business documentata e implementata. | Edge case gestito |
| 4.5.4 | **Stress test** | Eseguire workflow per 30 giorni consecutivi (backfill) e verificare idempotenza: rieseguire stesso giorno → stesso risultato. | Test idempotenza verde |

---

## FASE 5 — Wave D: Area Trasporti (Outbound)

> **Obiettivo:** Migrare `REPLICA_ORDINI` + `REPLICA_TRASP` + `CDT_SA.T_ORDINI/T_TRASP_*` + `CDT_DW.SP_LOAD_F_ORDINI/F_TRASPORTO`.  
> **Sorgenti Oracle:** ORDINI_TESTATE, ORDINI_RIGHE, TRASPORTI, SWAP, CONTRATTI_CORRIERI.  
> **Output Gold:** `f_ordini`, `f_trasporto`, KPI Fill Rate, Costi.  
> **Pre-requisiti:** Fase 0 + Sprint 1.x.

---

### Sprint 5.1 — Bronze Trasporti: Ordini, Trasporti, Swap
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 0.3, 1.3.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 5.1.1 | **Analisi tabelle sorgente Trasporti** | Decostruire `REPLICA_ORDINI`, `REPLICA_TRASP`, `REPLICA_SWAP`. Identificare: ORDINI_TESTATE, ORDINI_RIGHE, TRASPORTI (1 trasporto = N ordini), SWAP (sostituzioni), CONTRATTI_CORRIERI (tariffe). | Mapping sorgente |
| 5.1.2 | **Notebook `bronze_ordini_testate`** | JDBC ORDINI_TESTATE. Watermark DATA_ORDINE. Append-only `bronze_dev.logistica.ordini_testate`. | Bronze |
| 5.1.3 | **Notebook `bronze_ordini_righe`** | JDBC ORDINI_RIGHE. Watermark DATA_RIGA. Append-only `bronze_dev.logistica.ordini_righe`. | Bronze |
| 5.1.4 | **Notebook `bronze_trasporti`** | JDBC TRASPORTI. Watermark DATA_PARTENZA. Append-only `bronze_dev.logistica.trasporti`. | Bronze |
| 5.1.5 | **Notebook `bronze_swap`** | JDBC SWAP. Watermark DATA_SWAP. Append-only `bronze_dev.logistica.swap`. | Bronze |
| 5.1.6 | **Notebook `bronze_contratti_corrieri`** | JDBC CONTRATTI_CORRIERI. Full-load mensile (piccola tabella). Append-only `bronze_dev.logistica.contratti_corrieri`. | Bronze |
| 5.1.7 | **Backfill + Workflow Bronze Trasporti** | Workflow `logistica_bronze_trasporti` a 04:00. | Workflow schedulato |

---

### Sprint 5.2 — Silver Trasporti: Normalizzazione & Join Ordini-Trasporti
**Durata:** 8 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 5.1.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 5.2.1 | **Analisi `T_ORDINI`, `T_TRASP_*` Oracle** | Mappare trasformazioni SP CDT_SA per Trasporti. | Documento mapping |
| 5.2.2 | **Notebook `silver_ordini`** | Join testate ⋈ righe ordine. Deduplica (ORDINE_ID, ART_ID). Cast: QTA_ORDINATA, PESO, VOLUME → numerici. Flag: ordine_annullato, ordine_urgente. MERGE INTO `silver_dev.logistica.ordine`. | Silver Ordini |
| 5.2.3 | **Notebook `silver_trasporti`** | Deduplica per TRASPORTO_ID. Cast: DATA_PARTENZA/ARRIVO, PESO_CARICO, VOLUME_CARICO. Calcolo LEAD_TIME_CONSEGNA_GG. MERGE INTO `silver_dev.logistica.trasporto`. | Silver Trasporti |
| 5.2.4 | **Notebook `silver_swap`** | Deduplica per (ORDINE_ID, DATA_SWAP). MERGE INTO `silver_dev.logistica.swap`. | Silver Swap |
| 5.2.5 | **Notebook `silver_costo_trasporto`** | Join trasporto ⋈ contratti_corrieri per calcolo costo: COSTO = PESO_KG × TARIFFA_KG + QUOTA_FISSA. Gestione fasce peso contrattuali (CASE WHEN). | Silver Costi |
| 5.2.6 | **DQ Silver Trasporti** | % ordini senza trasporto assegnato, % trasporti senza ordini associati, LEAD_TIME_CONSEGNA negativi. | Report DQ |

**Criteri di Accettazione Sprint 5.2:**
- [ ] Silver Ordini e Trasporti senza duplicati su chiavi primarie
- [ ] LEAD_TIME_CONSEGNA ≥ 0 per ≥ 98% dei record

---

### Sprint 5.3 — Gold F_ORDINI & F_TRASPORTO: Fact Tables
**Durata:** 8 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 5.2 + Dimensioni.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 5.3.1 | **Notebook `gold_f_ordini`** | Join Silver ordine con DIM_ARTICOLO, DIM_PDV, DIM_SITO (sito spedizione), DIM_CALENDARIO. Misure: QTA_ORDINATA, QTA_CONSEGNATA, QTA_MANCANTE, PESO_KG, VOLUME_M3, VALORE_ORDINE. FILL_RATE = QTA_CONSEGNATA / QTA_ORDINATA (calcolato a riga). replaceWhere su partizione DATA_ORDINE. | F_ORDINI in Gold |
| 5.3.2 | **Notebook `gold_f_trasporto`** | Join Silver trasporto ⋈ costo_trasporto con DIM_CORRIERE, DIM_SITO, DIM_CALENDARIO. Misure: PESO_CARICO_KG, VOLUME_M3, COSTO_EUR, LEAD_TIME_GG, NUM_ORDINI, NUM_COLLI. replaceWhere su DATA_PARTENZA. | F_TRASPORTO in Gold |
| 5.3.3 | **Gestione Swap** | Ordini sostituiti da Swap: aggiornare F_ORDINI con FLAG_SWAPPED, collegare all'ordine sostituto. | Logica Swap implementata |
| 5.3.4 | **Quadratura vs Oracle** | SUM(QTA_CONSEGNATA), SUM(COSTO_EUR) per CORRIERE e MESE. | Report ≤ 0.1% |

---

### Sprint 5.4 — KPI Trasporti & Workflow
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst  
**Pre-requisiti:** Sprint 5.3.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 5.4.1 | **Vista `gold_kpi_fill_rate`** | Fill Rate mensile per CORRIERE, SITO, PDV_AREA: SUM(QTA_CONSEGNATA) / SUM(QTA_ORDINATA). Target ≥ 98%. | Vista KPI |
| 5.4.2 | **Vista `gold_kpi_costo_trasporto`** | Costo per KG, costo per M3, costo per ordine per CORRIERE, MESE. | Vista KPI |
| 5.4.3 | **Vista `gold_kpi_resa_corrieri`** | LEAD_TIME medio, % consegne in target (≤ LEAD_TIME_CONTRATTUALE), % resi per CORRIERE. | Vista KPI |
| 5.4.4 | **Workflow `logistica_trasporti`** | Bronze → Silver → Gold → KPI. Scheduling 05:00. | Workflow end-to-end |
| 5.4.5 | **Validazione funzionale** | BA verifica Fill Rate, costi corrieri su report prototipo. | Sign-off funzionale |

---

## FASE 6 — Wave E: Tracciabilità CE 178 & Movimentazione Carrellisti

> **Obiettivo:** Migrare area Tracciabilità lotti (compliance normativa CE 178/2002) e KPI movimentazione carrellisti.  
> **Sorgenti Oracle:** TRACCIACE178, DETTAGLIO_CARR, CARTELLINO, ABB_TOLTI.  
> **Output Gold:** `f_tracciabilita_lotti`, `f_movimentazione_carrellisti`, KPI conformità.  
> **Pre-requisiti:** Fase 0 + Sprint 1.x + Sprint 2.x (F_CARICO) per join lotti.

---

### Sprint 6.1 — Bronze & Silver Tracciabilità CE178
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 2.2 (Silver Carichi per join lotti).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 6.1.1 | **Analisi flusso CE178** | Capire la struttura di TRACCIACE178: registra per ogni lotto (LOT_ID) il ciclo di vita (CARICO → STOCCAGGIO → USCITA). Identificare gli eventi tracciati. | Documento flusso CE178 |
| 6.1.2 | **Bronze `traccia_ce178`** | Già realizzata in Sprint 2.1.5. Verificare completezza per dominio Tracciabilità. | (riutilizzo Bronze esistente) |
| 6.1.3 | **Silver `silver_tracciabilita_lotto`** | Join traccia_ce178 ⋈ silver carico_dettaglio (per info fornitore, data carico). Tracciare per ogni (LOT_ID, ART_ID): DATA_CARICO, DATA_SCADENZA, DATA_USCITA, QTA_CARICATA, QTA_VENDUTA, QTA_RESIDUA, FLAG_SCADUTO. MERGE INTO Silver. | Silver lotto |
| 6.1.4 | **Gold `gold_f_tracciabilita_lotti`** | Join Silver con DIM_ARTICOLO, DIM_FORNITORE, DIM_SITO, DIM_CALENDARIO. Misure: QTA_CARICATA, QTA_VENDUTA, QTA_SCARTATA, GIORNI_A_SCADENZA. | Fact lotti |
| 6.1.5 | **Vista conformità CE178** | Per audit: lista lotti con DATA_SCADENZA < SYSDATE e QTA_RESIDUA > 0 (prodotti scaduti in giacenza). | Vista compliance |

**Criteri di Accettazione Sprint 6.1:**
- [ ] F_TRACCIABILITA_LOTTI con traccia completa per ogni lotto
- [ ] Nessun lotto senza DATA_SCADENZA (campo obbligatorio CE178)

---

### Sprint 6.2 — Bronze, Silver & Gold Movimentazione Carrellisti
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** Sprint 1.3 (DIM_OPERATORE).

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 6.2.1 | **Analisi tabelle sorgente carrellisti** | Decostruire procedure Oracle per DETTAGLIO_CARR, CARTELLINO, ABB_TOLTI (abbonamenti tolti/sanzioni). Identificare: missioni (MISSIONE_ID), tipologie (TRASLOCO, PICKING, REINTEGRO, INVENTARIO), tempi non produttivi. | Mapping sorgente |
| 6.2.2 | **Bronze `bronze_missioni_carr`** | JDBC DETTAGLIO_CARR. Watermark DATA_MISSIONE. Append-only. | Bronze |
| 6.2.3 | **Bronze `bronze_cartellino`** | JDBC CARTELLINO (badge/presenze). Watermark DATA_PRESENZA. Append-only. | Bronze |
| 6.2.4 | **Silver `silver_missione_carrellista`** | Deduplica per MISSIONE_ID. Calcolo DURATA_MISSIONE_MIN. Classificazione tipologia. MERGE INTO Silver. | Silver missioni |
| 6.2.5 | **Silver `silver_sessione_carrellista`** | Da CARTELLINO: sessioni presenze per operatore/giorno. Calcolo ORE_PRESENZA. Sottrazione tempi non produttivi (pause, riunioni da ABB_TOLTI). | Silver sessioni |
| 6.2.6 | **Gold `gold_f_movimentazione_carrellisti`** | Join missioni ⋈ sessioni ⋈ DIM_OPERATORE ⋈ DIM_SITO ⋈ DIM_CALENDARIO. Misure: NUM_MISSIONI, KM_PERCORSI (se disponibili), ORE_PRODUTTIVE, TIPOLOGIA_PRINCIPALE. | Fact carrellisti |
| 6.2.7 | **Vista KPI carrellisti** | Per OPERATORE, SITO, MESE: missioni/ora, % tempo produttivo, tipologia missioni. | Vista KPI |

---

### Sprint 6.3 — Workflow Wave E & Validazione
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst  
**Pre-requisiti:** Sprint 6.1, 6.2.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 6.3.1 | **Workflow `logistica_wave_e`** | Tracciabilità + Carrellisti in parallelo. Scheduling 05:30. | Workflow schedulato |
| 6.3.2 | **Validazione funzionale** | BA verifica: conformità CE178, KPI carrellisti. | Sign-off |
| 6.3.3 | **Documentazione Wave E** | README area Tracciabilità e Carrellisti. | Docs committate |

---

## FASE 7 — KPI Aggregati & Layer Reporting

> **Obiettivo:** Costruire il layer di aggregati MicroStrategy (tabelle A_* e viste materializzate). Consolidare tutti i KPI in un unico layer Gold ottimizzato per query BI.  
> **Pre-requisiti:** Tutte le Fact Table delle Wave A–E completate.

---

### Sprint 7.1 — Aggregati Mensili e Tabelle A_*
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer  
**Pre-requisiti:** F_CARICO, F_GIACENZE, F_PREP_SPED, F_ORDINI, F_TRASPORTO caricate.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 7.1.1 | **Analisi aggregati Oracle CDT_DW** | Elencare tutte le tabelle A_* (A_ORD_SOCI_MESE, A_BOLLE_CONSOLIDATE, etc.). Per ognuna: grain, misure, dimensioni. Classificare in: aggregati di reporting (→ Gold), aggregati intermedi (→ Silver o eliminabili). | Documento classificazione aggregati |
| 7.1.2 | **Notebook `gold_a_inbound_mensile`** | Aggregazione mensile F_CARICO: per FORNITORE, SITO, MESE → SUM peso/QTA, AVG lead time, COUNT carichi. | Tabella aggregato |
| 7.1.3 | **Notebook `gold_a_stock_mensile`** | Aggregazione mensile F_GIACENZE_MONTHLY: per ARTICOLO, SITO, MESE → media giacenza, valore, giorni copertura. | Tabella aggregato |
| 7.1.4 | **Notebook `gold_a_outbound_mensile`** | Aggregazione mensile F_ORDINI + F_TRASPORTO: per CORRIERE, PDV_AREA, MESE → Fill Rate, costo, volume. | Tabella aggregato |
| 7.1.5 | **Notebook `gold_a_produttivita_mensile`** | Aggregazione mensile F_PREP_SPED: per SITO, MESE → produttività media, colli totali, ore totali. | Tabella aggregato |
| 7.1.6 | **Workflow `logistica_aggregati`** | Eseguire tutti i notebook aggregati in parallelo (fan-out dopo Gold). Scheduling 06:00. | Workflow schedulato |

---

### Sprint 7.2 — Dashboard Prototipo MicroStrategy & Ottimizzazione Query
**Durata:** 7 giorni lavorativi  
**Team:** Data Engineer + BI Developer  
**Pre-requisiti:** Sprint 7.1.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 7.2.1 | **Configurazione connettore MicroStrategy → Databricks** | Configurare ODBC/JDBC da MicroStrategy a Databricks SQL Warehouse. Verificare performance query su tabelle Gold. | Connessione MicroStrategy attiva |
| 7.2.2 | **Ottimizzazione tabelle Gold per query BI** | Aggiungere Z-ORDER su colonne filtro frequenti (DATA, SITO_ID, FORNITORE_ID). Verificare partizioni Delta ottimali. Aggiungere statistiche Delta (`ANALYZE TABLE ... COMPUTE STATISTICS`). | Query BI su 1 anno di dati < 30 secondi |
| 7.2.3 | **Prototipo dashboard Logistica** | Creare report MicroStrategy prototipo con: KPI Inbound (lead time, qualità), KPI Stock (saturazione, aging), KPI Outbound (fill rate, costi), KPI Picking (produttività). | Dashboard prototipo condiviso con BA |
| 7.2.4 | **Tuning Databricks SQL Warehouse** | Configurare cluster size SQL Warehouse appropriato per carico BI. Auto-suspend dopo 30 min inattività. | SQL Warehouse configurato |

---

### Sprint 7.3 — Validazione KPI End-to-End
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + Business Analyst + Key User  
**Pre-requisiti:** Sprint 7.2.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 7.3.1 | **Sessione di validazione KPI** | Workshop con BA e Key User: confronto KPI Oracle vs Databricks su 3 mesi recenti per ogni area. Documentare delta e motivazioni (se accettabili). | Report validazione firmato |
| 7.3.2 | **Correzioni post-validazione** | Implementare eventuali correzioni emerse dalla validazione (business rules mancanti, errori di mapping). | Fix committati e deployati |
| 7.3.3 | **Performance baseline** | Misurare e documentare tempo di esecuzione end-to-end workflow su finestra 24h. Confrontare con finestra batch Oracle (6-17h). | Report performance: Oracle vs Databricks |

---

## FASE 8 — Shadow Mode, Validazione & Cut-Over

> **Obiettivo:** Eseguire Oracle e Databricks in parallelo per almeno 10 giorni lavorativi, validare quadrature, poi eseguire il cut-over definitivo con rollback plan.

---

### Sprint 8.1 — Shadow Mode Setup & Monitoring
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + DBA Oracle  
**Pre-requisiti:** Tutte le Wave A–E e Fase 7 completate e validate.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 8.1.1 | **Attivare tutti i workflow in produzione** | Deploy su `bronze_prod`, `silver_prod`, `gold_prod`. Eseguire backfill storico completo in PROD. | Tutti i workflow attivi in PROD |
| 8.1.2 | **Notebook di quadratura automatica giornaliera** | Per ogni area: confronto automatico delle metriche chiave Oracle vs Databricks. Output in tabella `gold_prod.logistica._quadratura_shadow`. Alert automatico se delta > soglia configurabile. | Quadratura automatica giornaliera |
| 8.1.3 | **Dashboard Shadow Mode** | Report semplice (notebook o dashboard) che mostra: data, area, metrica, valore Oracle, valore Databricks, delta%, status (OK/KO). | Dashboard shadow mode |
| 8.1.4 | **Runbook operativo** | Documentare: come interpretare alert, chi contattare, procedura di escalation, come sospendere un workflow. | Runbook PDF/Confluence |

**Criteri di Accettazione Sprint 8.1:**
- [ ] Shadow mode attivo su tutte le aree in PROD
- [ ] Nessun alert critico nelle prime 48h

---

### Sprint 8.2 — Shadow Mode Run (10+ giorni lavorativi)
**Durata:** 10 giorni lavorativi  
**Team:** Data Engineer (monitoraggio)  
**Pre-requisiti:** Sprint 8.1.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 8.2.1 | **Monitoraggio giornaliero quadrature** | Ogni giorno: leggere dashboard shadow, verificare delta per area. Documentare anomalie. | Log giornaliero |
| 8.2.2 | **Risoluzione anomalie** | Per ogni delta > soglia: investigare causa, correggere notebook o configurazione. Redeploy via CI/CD. | Fix progressivi committati |
| 8.2.3 | **Stress test finestra batch** | Simulare scenario di ritardo sorgente (Oracle tarda), verificare che i workflow Databricks gestiscano correttamente dati mancanti (graceful degradation). | Test superato |
| 8.2.4 | **Report finale Shadow Mode** | Tabella con: per ogni area, % giorni con delta ≤ 0.1%, data ultima anomalia, status finale. | Report per sign-off |

**Criteri di Accettazione Sprint 8.2:**
- [ ] ≥ 95% delle quadrature giornaliere con delta ≤ 0.1% su tutte le aree
- [ ] Nessuna anomalia non risolta negli ultimi 5 giorni del periodo

---

### Sprint 8.3 — Preparazione Cut-Over
**Durata:** 5 giorni lavorativi  
**Team:** Data Engineer + DBA Oracle + Project Manager  
**Pre-requisiti:** Sprint 8.2 completato con successo.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 8.3.1 | **Rollback Plan** | Documentare: procedura per tornare a Oracle in caso di problemi post-cut-over. Tempi di rollback stimati. Responsabili. | Rollback Plan approvato |
| 8.3.2 | **Cut-Over Plan dettagliato** | Definire sequenza esatta di cut-over: 1) Bloccare aggiornamenti report Oracle, 2) Eseguire ultimo ciclo Oracle, 3) Verificare Databricks allineato, 4) Redirigere MicroStrategy a Databricks, 5) Comunicare agli utenti. | Cut-Over Plan approvato da PM e BA |
| 8.3.3 | **Comunicazione utenti** | Preparare comunicazione agli utenti finali: data cut-over, eventuale finestra di indisponibilità (stimata < 2h), chi contattare. | Comunicazione bozza approvata |
| 8.3.4 | **Verifica finale permessi PROD** | Assicurarsi che gli utenti MicroStrategy abbiano accesso ai cataloghi Gold PROD. Verificare con query di test. | Accessi verificati |
| 8.3.5 | **Tag release GitLab** | Creare tag `v1.0.0-cutover` su main. Congelare branch main pre-cut-over. | Tag creato, branch protetto |

---

### Sprint 8.4 — Cut-Over & Post-Live Support
**Durata:** 7 giorni lavorativi (2 go-live + 5 stabilizzazione)  
**Team:** Data Engineer + DBA Oracle + BA + PM  
**Pre-requisiti:** Sprint 8.3 completato, approvazione formale.

#### Attività

| # | Attività | Dettaglio tecnico | Output atteso |
|---|----------|-------------------|---------------|
| 8.4.1 | **Esecuzione Cut-Over** | Seguire cut-over plan passo per passo. Ogni step documentato con timestamp e responsabile. | Oracle → Databricks live |
| 8.4.2 | **Verifica post-cut-over (D+0, D+1)** | Prime 48h: monitoring intensivo ogni 4h. Verificare tutti i workflow eseguiti correttamente. KPI MicroStrategy accessibili e corretti. | Report post-cutover D+0 e D+1 |
| 8.4.3 | **Supporto utenti (D+1 → D+5)** | Presidio per domande e anomalie segnalate dagli utenti finali. Bug fixing prioritario se necessario. | Log bug e fix applicati |
| 8.4.4 | **Spegnimento flusso Oracle** | Dopo 5 giorni di stabilità: disattivare job ODI Oracle, documentare data di dismissione. Non eliminare oggetti Oracle (freeze, non drop). | Job Oracle disabilitati (non eliminati) |
| 8.4.5 | **Retrospettiva e documentazione finale** | Meeting di retrospettiva. Aggiornamento documentazione tecnica finale. Lessons learned. | Documento lessons learned |

**Criteri di Accettazione Sprint 8.4:**
- [ ] Tutti i report MicroStrategy funzionanti su Databricks
- [ ] Nessuna anomalia critica nei 5 giorni post-cut-over
- [ ] Job Oracle disabilitati e documentati

---

## Matrice Dipendenze Inter-Sprint

```
FASE 0 ────────────────────────────────────────────────────────────────────
  0.1 → 0.2 → 0.3

FASE 1 (richiede 0.x completo) ────────────────────────────────────────────
  1.1 ──┬──→ 1.2
        └──→ 1.3

FASE 2 (richiede 0.x + 1.x) [in parallelo con 3,4,5,6] ─────────────────
  2.1 → 2.2 → 2.3 → 2.4

FASE 3 (richiede 0.x + 1.x) ───────────────────────────────────────────────
  3.1 → 3.2 → 3.3 → 3.4

FASE 4 (richiede 0.x + 1.x) ───────────────────────────────────────────────
  4.1 → 4.2 → 4.3 → 4.4 → 4.5

FASE 5 (richiede 0.x + 1.x) ───────────────────────────────────────────────
  5.1 → 5.2 → 5.3 → 5.4

FASE 6 (richiede 0.x + 1.x + 2.2 per CE178) ─────────────────────────────
  6.1 ──┬──→ 6.3
  6.2 ──┘

FASE 7 (richiede 2.x + 3.x + 4.x + 5.x + 6.x completi) ─────────────────
  7.1 → 7.2 → 7.3

FASE 8 (richiede 7.x completo) ─────────────────────────────────────────────
  8.1 → 8.2 → 8.3 → 8.4
```

---

## Riepilogo Sprint e Stime

| Sprint | Area | Durata (gg lav.) | Team Min | Pre-requisiti critici |
|--------|------|------------------|----------|----------------------|
| 0.1 | Infrastruttura Unity Catalog | 7 | Infra + DE | — |
| 0.2 | CI/CD & Asset Bundles | 5 | DevOps + DE | 0.1 |
| 0.3 | Connettività & Template | 7 | DE + DBA | 0.1, 0.2 |
| 1.1 | DIM Calendario & Merceologie | 5 | DE | 0.x |
| 1.2 | DIM Articoli, Fornitori, PDV | 7 | DE | 1.1 |
| 1.3 | DIM Siti, Operatori, Corrieri | 7 | DE | 1.1 |
| 2.1 | Bronze Carichi | 7 | DE | 0.3, 1.3 |
| 2.2 | Silver Carichi | 7 | DE | 2.1 |
| 2.3 | Gold F_CARICO | 7 | DE | 2.2, 1.2, 1.3 |
| 2.4 | KPI Carichi & Validazione | 5 | DE + BA | 2.3 |
| 3.1 | Bronze Giacenze | 7 | DE | 0.3, 1.3 |
| 3.2 | Silver Giacenze | 7 | DE | 3.1 |
| 3.3 | Gold F_GIACENZE | 7 | DE | 3.2, 1.2, 1.3 |
| 3.4 | Workflow & Validazione Giacenze | 5 | DE + BA | 3.3 |
| 4.1 | Bronze Prep Spedizioni | 7 | DE | 0.3, 1.3 |
| 4.2 | Silver Prep Spedizioni | 8 | DE | 4.1 |
| 4.3 | Gold F_PREP_SPED | 8 | DE | 4.2, 1.2, 1.3 |
| 4.4 | KPI Picking & Workflow | 5 | DE + BA | 4.3 |
| 4.5 | Edge Cases Prep Spedizioni | 5 | DE | 4.4 |
| 5.1 | Bronze Trasporti | 7 | DE | 0.3, 1.3 |
| 5.2 | Silver Trasporti | 8 | DE | 5.1 |
| 5.3 | Gold F_ORDINI & F_TRASPORTO | 8 | DE | 5.2, 1.2, 1.3 |
| 5.4 | KPI Trasporti & Workflow | 5 | DE + BA | 5.3 |
| 6.1 | CE178 Silver & Gold | 7 | DE | 2.2 |
| 6.2 | Carrellisti Bronze-Silver-Gold | 7 | DE | 1.3 |
| 6.3 | Workflow Wave E & Validazione | 5 | DE + BA | 6.1, 6.2 |
| 7.1 | Aggregati Mensili | 7 | DE | 2.x–6.x |
| 7.2 | MicroStrategy & Ottimizzazione | 7 | DE + BI | 7.1 |
| 7.3 | Validazione KPI End-to-End | 5 | DE + BA + KU | 7.2 |
| 8.1 | Shadow Mode Setup | 5 | DE + DBA | 7.x |
| 8.2 | Shadow Mode Run | 10 | DE | 8.1 |
| 8.3 | Preparazione Cut-Over | 5 | DE + DBA + PM | 8.2 |
| 8.4 | Cut-Over & Stabilizzazione | 7 | Team completo | 8.3 |

**Totale sprint sequenziali critici (critical path):** 0.1→0.3→1.x→2.x→7.x→8.x ≈ **~100 giorni lavorativi** (critical path)  
**Con parallelizzazione Fasi 2–6:** scenario ottimale con 3–4 DE in parallelo ≈ **~60 giorni lavorativi** dalla fine Fase 1

---

## Rischi e Mitigazioni

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---------|-------------|---------|-------------|
| R1 | Performance JDBC peggiore del previsto su tabelle grandi | Media | Alto | Sprint 0.3: benchmark preventivo + configurazione numPartitions ottimale |
| R2 | Anagrafiche Oracle incomplete (Late-Arriving Dimensions) | Alta | Medio | Surrogate key -1 + tabelle di log missing + refresh più frequente dimensioni |
| R3 | Business rules non documentate in PL/SQL legacy | Alta | Alto | Sessioni di code reading con DBA Oracle + validazione con BA su ogni area |
| R4 | Accesso di rete Oracle → Databricks non disponibile | Bassa | Critico | Verificare in Sprint 0.3, alternativa: export CSV via SFTP su ADLS |
| R5 | Regola 30 min attrezzaggio mal implementata | Media | Alto | Test su dataset storico con casi noti, validazione BA prima del go-live |
| R6 | Storico Oracle non disponibile per backfill completo | Media | Medio | Documentare periodo disponibile, caricare da data disponibile, avvisare BA |
| R7 | Quadrature shadow mode non convergenti | Media | Alto | Finestra shadow mode estesa (>10 gg), soglie configurabili per area |
| R8 | MicroStrategy non supporta funzionalità avanzate Databricks | Bassa | Medio | Test prototipo in Sprint 7.2 prima del cut-over |
| R9 | Ritardi deployment Terraform per approvazioni aziendali | Media | Medio | Avviare processo Terraform in anticipo, usare DEV già disponibile |
| R10 | Package Python `logistica_utils` non stabile | Bassa | Medio | Libreria minimale in Sprint 0.2, solo funzioni comprovate |

---

*Piano generato il 2026-05-29 — Versione 1.0*  
*Revisione raccomandata dopo completamento Sprint 0.3 (benchmark reali disponibili)*
