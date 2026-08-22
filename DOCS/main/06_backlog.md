# Backlog — Logistico 2.0

> ## ⚠️ DOCUMENTO ARCHIVIATO (deprecato 2026-08-01)
> Questo backlog è **sostituito** da [`15_backlog_master.md`](15_backlog_master.md), l'indice unico (SSOT)
> di tutte le attività (**ACT** in [`acts/`](acts/)) e decisioni (**ADR** in [`adr/`](adr/)).
> - Le attività di questo file sono ora ACT: sprint → `ACT_N.N.N`; backlog non-sprint (L/W/G/DBR/ST/DQ/RS/MNT)
>   → §2 del master; emergenti → `ACT_9000+`.
> - **Non aggiornare più questo file.** Lavorare sui singoli file ACT e aggiornare il master alla chiusura.
> - Conservato solo come **storico** della pianificazione pre-riorganizzazione.

---

<details>
<summary>Contenuto storico (pre-2026-08-01) — clic per espandere</summary>

**Ultimo aggiornamento:** 2026-07-02  
**Owner:** Cloud Data Architect — Team Logistico 2.0

> Questo file raccoglie tutte le attività da fare, organizzate per priorità e area.  
> È il punto di partenza per la pianificazione sprint-by-sprint una volta che l'infrastruttura cloud sarà disponibile.  
> Per il dettaglio di ogni attività (gg stimati, sprint, risorsa) fare riferimento a `04_piano_sviluppo.md`.  
> Per i punti in attesa di risposta esterna fare riferimento a `05_open_points.md`.

---

## Legenda priorità

| Simbolo | Significato |
|---------|------------|
| 🔴 | Bloccante / critico — sblocca fasi successive |
| 🟡 | Alta priorità — da fare nel prossimo sprint |
| 🟢 | Media priorità — pianificabile |
| ⚪ | Bassa priorità / rinviabile |

---

## 1. Infrastruttura Cloud (FASE 0 — prerequisito assoluto)

Tutte le attività sottostanti sono **bloccate** finché non viene fatto il provisioning Azure/Databricks.

> **Nota (agg. 2026-07-03):** decisioni D1-D5 chiuse; solo ambiente **DEV** configurato ora. Dettaglio prerequisiti e mail al cliente in `12_checklist_infra_setup.md`.

| # | Attività | Priorità | Rif. OP | Note |
|---|----------|----------|---------|------|
| I-01 | Utenza Azure (navigazione + terraform) da Francesco Giambona | 🔴 | — | Mail §F.3 checklist. Prerequisito di `terraform init` |
| I-02 | `terraform apply` overlay brownfield DEV (schemi + Volume + grants + cluster policy) | 🔴 | — | `brownfield/` pronto; backend DEV compilato; review plan con Ippazio |
| I-03 | ~~Storage Credential + External Location~~ → **UC Volume** `landing_dev` | ✅ | — | D3 confermato: Volume MANAGED, no external location |
| I-04 | ~~Azure Key Vault + Secret Scope~~ → **soppresso** | ✅ | — | 0.1.4 ridisegnata: no segreti Oracle (D5), auth via GitLab CI/CD |
| I-05 | ~~Cluster Policy VM~~ → **job cluster serverless** | ✅ | OP-19 | Policy `logistico-serverless-job-policy` in `brownfield/main.tf` |
| I-06 | Validazione accessi least-privilege (grants) | 🟡 | OP-18 | Writer `Engineering-dev` ✅; reader condizionale (gruppo non ancora creato) |
| I-07 | Subgroup GitLab `logistico` + 3 repo (infrastructure/workflows/lib) | 🔴 | Gap #4 | Mail a Extrared §F.1; multi-repo, non mono-repo |
| I-08 | Secret CI/CD (solo auth `ARM_*` + `DATABRICKS_TOKEN`) | ⏸️ | — | Meccanismo (cert vs secret manager) in def. con Technology |
| I-09 | GitLab Runner assegnati al subgroup | 🟡 | Gap #4 | Verifica: senza runner le pipeline non eseguono |

---

## 2. Deploy Pipeline su Cloud (FASE 8 — shadow mode)

Dipendono da I-01/I-02/I-03.

| # | Attività | Priorità | Note |
|---|----------|----------|------|
| D-01 | DAB bundle deploy `--target prod` (tutti i workflow) | 🔴 | Dopo terraform apply |
| D-02 | Backfill storico completo (22 siti, da data go-live) | 🔴 | Script pronti in locale |
| D-03 | Attivazione scheduling giornaliero tutti i workflow | 🔴 | YML pronti |
| D-04 | Notebook quadratura automatica Oracle vs Databricks | 🟡 | Logica scritta; da deployare |
| D-05 | Runbook operativo finalizzato per PROD | 🟡 | Bozza in `DOCS/runbook.md` |
| D-06 | Shadow mode run ≥ 10 giorni (monitoring + anomalie) | 🔴 | Target: delta ≤ 0.1% su ≥ 95% giorni |
| D-07 | Report finale shadow mode per sign-off | 🟡 | Template pronto |

---

## 3. Validazioni con BA (bloccate da FASE 8)

| # | Attività | Priorità | Wave | Note |
|---|----------|----------|------|------|
| V-01 | Validazione funzionale Carichi con BA (3 mesi vs Oracle) | 🔴 | Wave A | Non avviabile offline |
| V-02 | Validazione funzionale Giacenze con BA | 🔴 | Wave B | Non avviabile offline |
| V-03 | Validazione KPI Picking con BA | 🔴 | Wave C | Non avviabile offline |
| V-04 | Stress test idempotenza (30 gg backfill + re-run stesso giorno) | 🟡 | Wave C | Richiede PROD |
| V-05 | Validazione funzionale Trasporti con BA | 🔴 | Wave D | Non avviabile offline |
| V-06 | Validazione compliance CE178 su dati reali | 🔴 | Wave E | Richiede PROD |
| V-07 | Sessione validazione KPI E2E con BA/Key User | 🔴 | FASE 7 | Blocca approvazione finale |
| V-08 | Approvazione KPI da business (sign-off formale) | 🔴 | FASE 7 | Dipende da V-07 |
| V-09 | Performance baseline run E2E vs finestra batch Oracle | 🟡 | FASE 7 | Dati parziali da run locale |

---

## 4. Quadrature Oracle vs Databricks (eseguibili solo su cloud)

| # | Attività | Priorità | Tabella target | Note |
|---|----------|----------|----------------|------|
| Q-01 | Quadratura F_CARICO (SUM PESO_NETTO, QTA_RICEVUTA) | 🔴 | F_CARICO | SQL pronto |
| Q-02 | Quadratura F_GIACENZE (QTA_DISPONIBILE per data_foto) | 🔴 | F_GIACENZE_DAILY | SQL pronto |
| Q-03 | Quadratura F_PREP_SPED (SUM COLLI_PREPARATI, ORE_PRODUTTIVE) | 🔴 | F_PREP_SPED | SQL pronto |
| Q-04 | Quadratura F_TRASPORTO (QTA_CONSEGNATA, COSTO_EUR) | 🔴 | F_TRASPORTO | SQL pronto |

---

## 5. Sviluppo tecnico pendente (eseguibile offline)

Attività realizzabili in locale anche prima del provisioning cloud.

### 5a. OP-32 — LAD ri-risoluzione orphan (🔴 BLOCCANTE)

Design e implementazione del job generico per ri-risolvere le FK che sono andate a −1 per Late-Arriving Dimensions.

| # | Attività | Priorità | Effort | Note |
|---|----------|----------|--------|------|
| L-01 | Aggiungere `<dim>_COD_NAT` (chiave naturale) in tutti i fact | ✅ Done 2026-06-20 | — | 5 fact modificati: F_CARICO (4 NAT), F_PREP_SPED (4 NAT), F_TURNO_PREP_SITO (4 NAT), F_TRASPORTO (2 NAT), F_ORDINI (2 NAT). Colonne scritte prima del surrogate_key_fallback; per PDV_COD_NAT preservato il codice naturale sorgente (SOCIO_COD / NEGOZIO_COD). |
| L-02 | Implementare job `gold_lad_resolver` generico (parametrico su fact/fk/dim/nat_key) | ✅ Done 2026-06-20 | — | `notebooks/gold/maintenance/gold_lad_resolver.py` — widget: env/fact_table/retail_master_schema/dry_run; config pre-cablata per F_CARICO/F_PREP_SPED/F_TURNO_PREP_SITO/F_TRASPORTO/F_ORDINI; partitioning preservato da DESCRIBE DETAIL |
| L-03 | Scheduling LAD job dopo dim_refresh in tutti i workflow YML | 🟡 | 0.5 gg DE | Dopo L-02 |
| L-04 | Test idempotenza LAD (2+ run consecutivi stesso giorno) | 🟡 | 0.5 gg DE | — |

### 5b. OP-35 — Watermark rollout (✅ COMPLETATO 2026-06-19)

Pilota validato su `storico_liste_clean` (2026-06-14). Rollout completato su tutti i notebook _clean.

| # | Attività | Stato | Note |
|---|----------|-------|------|
| W-01 | Watermark su `silver_storico_bolle_clean` | ✅ Done | 2026-06-19 |
| W-02 | Watermark su `silver_carichi_testate` + `silver_carichi_dettagli` | ✅ Done | 2026-06-19 |
| W-03 | Watermark su `silver_spedizioni_clean` | ✅ Done | 2026-06-19 |
| W-04 | Watermark su `silver_ordini` | ✅ Done | 2026-06-19 |
| W-05 | Watermark su landing_to_bronze (nell'orchestratore) | 🟢 Pendente | Dipende da infra control catalog |
| W-06 | Deploy Terraform control catalog a regime | 🟢 Pendente | Dipende da I-02 |

### 5c. Gap tecnici da spec Reply (🟡)

| # | Attività | Priorità | Effort | Rif. |
|---|----------|----------|--------|------|
| G-01 | Supporto Parquet in Bronze (widget `file_format`, auto-detect) | ✅ Done 2026-06-20 | — | `detect_format` + `read_landing` centralizzate in `utils.py`; runner aggiornato con `--file-format`; 35 notebook bronze migrati |
| G-02 | Framework DQ condiviso (Great Expectations / Soda / Lakehouse Monitoring) | 🔴 | da def. | OP-21 — senza risposta Reply, ri-sottoporre |

### 5d. Rami secchi rimossi ✅ (2026-06-20)

Notebook eliminati dal codebase. Output non consumato a valle, sorgenti inesistenti o logica già sostituita.

| # | Notebook rimosso | Motivo |
|---|-----------------|--------|
| RS-01 | `notebooks/bronze/anagrafiche/bronze_pdv.py` | Leggeva `cnd-landing/t_pdv` (non estratto); PDV arriva correttamente da CDT_DW via `gold_lu_from_cdtdw.py` |
| RS-02 | `notebooks/silver/cdt_estr/silver_t_pdv.py` | Output `silver.logistica.t_pdv` non consumato dai fact gold (usano `bronze_dev.condiviso.LU_PDV`) |
| RS-03 | `notebooks/silver/trasporti/silver_swap.py` | Leggeva `bronze.logistica.t_trasp_mtv` (non estratto); output non consumato |
| RS-04 | `notebooks/silver/prep_spedizioni/silver_prep_sped_integrata.py` | Leggeva `silver.logistica.timbratura_sessione` (T_* as-is, non sorgente); sostituito da `silver_prep_prep_sped` |
| RS-05 | `notebooks/silver/prep_spedizioni/silver_timbrature_sessioni.py` | Leggeva `bronze.logistica.t_prep_sped` (CND non estratto); output non consumato |
| RS-06 | `notebooks/silver/trasporti/silver_costo_trasporto.py` | Output `silver.logistica.costo_trasporto` non consumato da nessun gold |
| RS-07 | `notebooks/silver/cdt_estr/silver_t_prep_sped.py` | Già DEPRECATED (2026-06-10); sostituito da `silver_prep_prep_sped` |
| RS-08 | `notebooks/silver/trasporti/silver_trasp_mtv_build.py` | Già DEPRECATED (2026-06-10); grana bolla sostituita da `silver_prep_trasporto` |

Rimosso anche `silver_t_pdv` da `tests/local_bronze/run_big_rerun.py` SILVER_CLEAN list.

### 5e. FASE 5 — Gold aggregati DM (✅ COMPLETATO 2026-06-20)

Tutti i 6 notebook `gold_dm_*` / `gold_a_*` sono stati verificati e girano correttamente sui dati reali (26/26 OK nel run 2026-06-19).

| Notebook | Sorgente | Output | Stato |
|----------|---------|--------|-------|
| `gold_dm_giacenze_monthly` | `F_GIACENZE_DAILY` | `A_GIACENZE_MONTHLY` | ✅ OK — graceful NO_DATA se nessuna giacenza nel mese |
| `gold_a_stock_mensile` | `A_GIACENZE_MONTHLY` | `A_STOCK_MENSILE` | ✅ OK — DM→DM passthrough, phase ordering corretto |
| `gold_a_inbound_mensile` | `F_CARICO` | `A_INBOUND_MENSILE` | ✅ OK |
| `gold_a_outbound_mensile` | `F_ORDINI` ⋈ `F_TRASPORTO` | `A_OUTBOUND_MENSILE` | ✅ OK — `QTA_TRASPORTATA_TOT` e `COSTO_STIMATO_EUR_TOT` deliberatamente NULL (F_TRASPORTO è a grana bolla, non porta quantità/costo) — da rivalutare quando disponibili listini corrieri |
| `gold_a_produttivita_mensile` | `F_TURNO_PREP_SITO` | `A_PRODUTTIVITA_MENSILE` | ✅ OK |
| `gold_dm_turno_prep_sito` | `F_TURNO_PREP_SITO` | `A_TURNO_PREP_SITO` | ✅ OK |

Doc `02_pipeline_mapping.md` aggiornato con le sorgenti corrette (erano stale: F_PREP_SPED→F_TURNO_PREP_SITO, F_GIACENZE_MONTHLY→A_GIACENZE_MONTHLY, F_MOVIMENTAZIONE_CARRELLISTI→F_TURNO_PREP_SITO).

### 5g. Fix BOM UTF-8 (✅ COMPLETATO 2026-06-23)

4 notebook Bronze (`bronze_prep_bolle_righe`, `bronze_prep_bolle_testate`, `bronze_prep_riepiloghi`, `bronze_storico_liste`) avevano BOM `U+FEFF` in testa al file introdotto dal `Set-Content` PowerShell nella sessione precedente. Rimosso con lettura/scrittura byte-level diretta.

### 5h. Manutenzione disco Docker (ricorrente)

| # | Attività | Frequenza | Note |
|---|----------|-----------|------|
| MNT-01 | VACUUM warehouse Delta (tombstone) | Dopo ogni pipeline run | `tests/local_bronze/vacuum_warehouse.py` — già eseguito nel runner |
| MNT-02 | fstrim + diskpart compact vhdx | Dopo pipeline pesante (22 siti) o quando C: < 20 GB liberi | Procedura: builder prune → fstrim via container privilegiato → Stop Docker → compact admin. Vedi memory [[wsl-vhdx-disk-reclaim]] |

**Esito 2026-06-23:** pipeline 22 siti ha consumato ~49 GB su C:. VACUUM warehouse = 0.45 GB. fstrim (971 GiB trimmed) + compact: 83.4 → 37.1 GB vhdx, C: 13.7 → 60.9 GB (+47 GB recuperati).

### 5f. Flusso stock mancante (🟢 analisi)

Il flusso `silver_t_stock` → `silver.logistica.cndstostock_clean` è assente dall'analisi as-is. I campi `VAL_STOCK_*` restano a 0. Da includere nella mappatura sorgenti come gap noto.

| # | Attività | Priorità | Note |
|---|----------|----------|------|
| ST-01 | Identificare sorgente dati stock nell'as-is (CND? Logistix?) e documentarla nel mapping | 🟢 | Prerequisito per implementare il flusso |
| ST-02 | Implementare flusso stock se sorgente disponibile | ⚪ | Dopo ST-01 e prioritizzazione con BA |

### 5f. DQ S7 — analisi chiave `silver_storico_bolle_uniche` (🟢 analisi)

Il check DQ S7 rileva che `BOL_NRO_BOLLA` stesso varia all'interno della chiave di aggregazione (8 colonne), indicando che la chiave potrebbe essere troppo larga o semanticamente errata. Il `MIN()` tecnico applicato su valori multipli potrebbe produrre dati incoerenti in downstream senza tracciabilità.

| # | Attività | Priorità | Note |
|---|----------|----------|------|
| DQ-01 | Analisi semantica chiave bolle: capire se `BOL_NRO_BOLLA` va inserito nelle KEYS o è atteso variare | ✅ Analisi chiusa 2026-06-20 | Chiave 8 colonne è CORRETTA (replica WL1 legacy). BOL_NRO_BOLLA NON è chiave: una gabbia/ordine può coprire più bolle. La varianza segnalata dal DQ S7 è un'anomalia dati upstream (Oracle), non un difetto del modello. Da confermare con BA in sessione di validazione. |
| DQ-02 | Se chiave errata: correggere KEYS in `silver_storico_bolle_uniche.py` e verificare impatto su DQ S7 | ✅ No-action 2026-06-20 | La chiave NON è errata: aggiungere BOL_NRO_BOLLA cambierebbe il grain e spezzerebbe il JOIN con storico_liste_uniche. Il DQ S7 warning rimane informativo, non bloccante. |
| DQ-03 | Aggiungere flag `_bolla_multipla` per tracciare i record con bolla non costante | ✅ Done 2026-06-20 | Implementato in `silver_storico_bolle_uniche.py`: colonna booleana True dove COUNT(DISTINCT BOL_NRO_BOLLA)>1 per la chiave di prelievo. Utile per auditing in `silver_prep_prep_sped` a valle. |

### 5e. MicroStrategy & Reporting

| # | Attività | Priorità | Effort | Note |
|---|----------|----------|--------|------|
| M-01 | Configurazione connettore MicroStrategy → Databricks SQL Warehouse | 🔴 | 2 gg DE | Richiede SQL Warehouse cloud attivo |
| M-02 | Tuning SQL Warehouse (size, auto-suspend, serverless) | 🟡 | 1 gg DE | Config scritta; apply su cloud |
| M-03 | Prototipo dashboard (4 aree KPI) su MicroStrategy | 🟡 | 1 gg DE | SQL views pronte |
| M-04 | Performance baseline run E2E vs finestra batch Oracle | 🟢 | 1 gg DE | Dati parziali da run locale |

---

## 5i. Wave certifica Carichi/Prep-Sped vs CDT_DW (2026-07-02)

Attività emerse dalla ri-certifica `F_CARICO`/`F_PREP_SPED`. Registro OP in `05_open_points.md` sez. F.

| # | Attività | Priorità | Stato | Note |
|---|----------|----------|-------|------|
| CERT-01 | Fix tombstone quadratura (`live_delta_files` via `_delta_log`) | 🟡 | ✅ Done 2026-07-02 | `scripts/quadratura/quadratura_fact.py`; elimina gonfiaggio ~4× lettura pyarrow |
| CERT-02 | Blocco "SCARTATE" quadratura PREP_SPED (OP-PSP-1) | 🟢 | ✅ Done 2026-07-02 | Confronta GIORNO_BOLLA=0 vs DATA_BOLLA_SPED NULL; documenta asimmetria |
| CERT-03 | Fix `DATA_PREL_INIZ` (OP-PSP-2) in `silver_prep_prep_sped` | 🟡 | ✅ Done 2026-07-02 | julian LSPRL_DATA_PRELIEVO + ORA; partizione DATA_PREL ora reale |
| CERT-04 | **OP-CAR-5**: decisione design grain `silver_prep_carico` (LEFT join pesata vs grain da catena WL) | 🟠 | Aperto | Sessione dedicata; 42 sito×giorno "Solo in ODI" su giorni con pesata in ritardo |
| CERT-05 | **OP-CAR-3**: validare formula ODI `QTA_ORD_FORN` (WL4) prima di replicarla | 🟠 | Aperto | Oggi forzato a 0.0 |
| CERT-06 | Ri-certifica quadratura CARICO dopo fix OP-CAR-5 | 🟢 | Bloccata da CERT-04 | — |

---

## 5j. Databricks-readiness (eseguibili in locale, retro-compatibili)

Interventi che rendono il codice pronto per Databricks **senza** dipendere dalle decisioni D1-D5 e
**senza** rompere il flusso locale. Piano completo in `10_piano_migrazione_databricks.md`.

| # | Attività | Priorità | Stato | Note |
|---|----------|----------|-------|------|
| DBR-01 | Modulo `storage.py`: `is_databricks()` + `get_landing_root()`/`get_warehouse_root()` per-ambiente | 🟡 | ✅ Done 2026-07-02 | Nuovo file, zero-risk; detection via `DATABRICKS_RUNTIME_VERSION` |
| DBR-02 | Helper centralizzato per catalog+schema anagrafiche condivise (parametrizzare `cdtdw.condiviso` hardcoded, 11 occorrenze) | 🟡 | ✅ Done 2026-07-02 | `get_condiviso_schema(env)` in `utils.py`; widget default aggiornati su 7 notebook; shim `run_notebook.py` aggiornato (D2=`bronze_dev.condiviso`) |
| DBR-03 | Riconciliare chiave `control` in `_CATALOG_MAP` (`control_dev`→`config_dev`?) | 🟡 | ✅ Done 2026-07-02 | `_CATALOG_MAP["dev"]["control"] = "config_dev"`; shim `run_notebook.py` aggiornato (`config_dev.*`) — D1 confermato |
| DBR-04 | Backend Spark per `quadratura_fact.py` (auto su Databricks: `spark.table` invece di pyarrow) | 🟢 | Da fare | D5 confermato (export su landing); quando pronto: `spark.read.csv` da Volume landing; pyarrow locale invariato |
| DBR-05 | Build wheel `logistica_utils` + `databricks.yml` (Asset Bundle) skeleton | 🟢 | Da fare | Per deploy job/lib su cluster |
| DBR-06 | Definire Databricks Workflows (bronze→silver→gold→quadratura) da `run_all_*` | 🟢 | Da fare | Widget già compatibili con job parameters |
| DBR-07 | Mono-repo: import area `logistico/` nel repo DWH (subtree o squash) + DAB target dev/prod | 🟢 | Da fare | Allineare a branch strategy DWH |

---

## 6. Cut-Over & Go-Live (FASE 8 — dopo shadow mode approvato)

| # | Attività | Priorità | Note |
|---|----------|----------|------|
| C-01 | Finalizzare Rollback Plan e farlo approvare | 🔴 | Bozza pronta |
| C-02 | Finalizzare Cut-Over Plan (sequenza, responsabili, timing) | 🔴 | Bozza pronta |
| C-03 | Comunicazione utenti finali (data, finestra < 2h) | 🟡 | Template pronto |
| C-04 | Verifica permessi PROD (utenti MicroStrategy su `gold_prod`) | 🟡 | Dipende da I-06 |
| C-05 | Esecuzione Cut-Over step by step | 🔴 | Dipende da D-06 approvato |
| C-06 | Verifica post-cut-over D+0, D+1 (monitoring ogni 4h) | 🔴 | — |
| C-07 | Spegnimento flusso Oracle ODI (disabilitare, NON eliminare) | 🟡 | — |
| C-08 | Retrospettiva + Documento di Sviluppo Finale | 🟢 | Bozza in `docs/Archive/` |

---

## 7. Dipendenze esterne (in attesa di Reply / sorgente)

Attività bloccate su risposta esterna — non pianificabili finché non arriva la conferma.

| # | Attività | In attesa di | Rif. OP |
|---|----------|-------------|---------|
| E-01 | Schema definitivo lookup Retail (`LU_ART_RADICE`, `LU_FORNITORE`, ecc.) | Reply | OP-02 |
| E-02 | Granularità Service Principal per job Databricks | Reply | OP-18 |
| E-03 | Framework DQ standard di piattaforma | Reply | OP-21 🔴 |
| E-04 | SLA scheduling (finestre batch per sorgente) | Sorgente/Reply | OP-09 |
| E-05 | Conferma path landing zone (struttura Foconi) | Reply | OP-07 |
| E-06 | Criteri accettazione parallel run (durata, tolleranza) | Reply | OP-24 |
| E-07 | Processo formale go-live (approvazione, evidenze test) | Reply | OP-25 |
| E-08 | Alerting Databricks (sistema Reply) | Reply | OP-20 |

---

## 8. Monitoraggio ricorrente (ogni run)

Questi controlli vanno effettuati ad ogni pipeline run giornaliero.

| # | Check | Soglia allarme | Rif. |
|---|-------|---------------|------|
| R-01 | Orphan rate tutti i fact | > 0.0% | Gold DQ |
| R-02 | Silver: 45/45 OK (0 FAIL) | qualsiasi FAIL | Silver report |
| R-03 | Gold: 26/26 OK (0 FAIL) | qualsiasi FAIL | Gold report |
| R-04 | `lgcx/tracciace178` dedup ratio | > 80% dedup = anomalia | Landing log |
| R-05 | F_GIACENZE_DAILY righe scritte | 0 righe consecutivi > 2 gg = indagare | Gold log |
| R-06 | Spazio libero C: | < 20 GB → eseguire MNT-02 prima del prossimo run | Disco locale |
| R-07 | `silver_storico_bolle_uniche` DQ S7 warning | nuovi attributi o conteggi in crescita anomala | Silver log |

---

## Riepilogo per area

| Area | Attività totali | Eseguibili ora (offline) | Bloccate da cloud | Bloccate da Reply/sorgente/decisioni |
|------|----------------|--------------------------|------------------|---------------------------|
| Infrastruttura | 9 | 2 (I-07, I-08) | 7 | — |
| Deploy pipeline | 7 | — | 7 | — |
| Validazioni BA | 9 | — | 9 | — |
| Quadrature Oracle | 4 | — | 4 | — |
| Sviluppo tecnico | 30 | **30** | — | — |
| Wave certifica (5i) | 6 | 3 done + CERT-04/05/06 | — | CERT-04/05 (design/sorgente) |
| Databricks-readiness (5j) | 7 | DBR-01/02/03 ✅; DBR-04/05/06/07 pending | — | D4 (prod catalog naming) |
| Cut-Over | 8 | 2 (C-01, C-02 bozze) | 6 | — |
| Dipendenze esterne | 8 | — | — | 8 |
| **TOTALE** | **77** | **~30** | **~33** | **~14** |

---

## Riferimenti

- `docs/main/04_piano_sviluppo.md` — dettaglio sprint, gg stimati, stato per attività
- `docs/main/05_open_points.md` — registro completo open points con storico
- `docs/main/02_pipeline_mapping.md` — architettura pipeline e runbook operativo
- `DOCS/piani/cutover_plan.md` — piano cut-over (bozza)
- `DOCS/piani/rollback_plan.md` — piano rollback (bozza)

</details>
