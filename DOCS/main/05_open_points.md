# Open Points — Logistico 2.0

**Ultimo aggiornamento:** 2026-08-27  
**Owner documento:** Cloud Data Architect — Team Logistico 2.0  
**Scopo:** registro dei punti **ancora aperti** che richiedono conferme esterne (Reply o sistemi sorgente) o che sono stati messi in stand-by per fase successiva.

> **Fonte:** aggiornamento del file `DOCS/Open Points - Logistico 2.0.md` (originale 2026-06-10).  
> Questo file in `docs/main/` è la **SSOT** — il file DOCS è conservato in `docs/Archive/`.

## Legenda stato

| Stato | Significato |
|-------|-------------|
| 🔴 Aperto | Da risolvere prima/insieme alla revisione del codice |
| 🟡 Da confermare (Reply) | In attesa di conferma dal team Reply / Data Platform |
| 🟠 Da confermare (Sorgente) | In attesa di conferma dai sistemi sorgente (Logistix / CND / STAT) |
| 🔵 In stand-by / Fisiologico | Rimandato a fase successiva, o comportamento atteso e documentato |
| 🟢 Risolto | Chiuso con soluzione validata in produzione / su dati reali |

> Gli OP risolti dalla revisione end-to-end (OP-06, OP-12/13/15, OP-14/16, OP-27) sono rimossi dal registro e tracciati nei documenti di spec dei rispettivi layer (sezione "OP risolti" in fondo).

---

## A0. Naming / Governance (trasversale)

### OP-NAMING — Validazione naming oggetti (tabelle e colonne) 🔵 (per ogni fase)
Ogni fase chiude con un OP di **validazione della naming** degli oggetti prodotti (tabelle e colonne):
coerenza, leggibilità, allineamento agli standard e **unità di misura** esplicite dove utile.
La naming legacy (ereditata da **CDT_DW/ODI**) è mantenuta per **fedeltà e quadratura-per-nome** vs Oracle
e per la **migrazione MSTR**; una revisione (rename fisici) è probabile in una **fase successiva**.

*Esempio (carichi, F_CARICO):* `QTA_ORD_FORN` è in **colli**, `QTA_CARICO` in **pezzi**. I nomi ODI
restano; l'unità è nei **commenti colonna** e i nomi espliciti (in pezzi) vivono nel layer aggregato
(`A_INBOUND`). Un rename fisico (es. `QTA_ORD_FORN_COLLI`/`QTA_CARICO_PZ`) impatterebbe la quadratura
per-nome e la migrazione MSTR → **rinviato**. Il tracking rename per MSTR è in `13_registro_rename_gold_microstrategy.md`.

---

## A. Anagrafiche, Lookup e Schemi condivisi

### OP-01 — Schema `condiviso` non previsto da Reply 🟡
**Descrizione:** Reply non prevede uno schema `gold_prod.condiviso`. Le dimensioni master sono prodotte dal flusso **Master Data Master** con naming `LU_*`.  
**Soluzione D2 (✅ 2026-07-02):** per il primo rilascio le `LU_*` da CDT_DW vivono nel nostro schema proprio **`bronze_<env>.condiviso`** (isolamento totale, popolato dal push cdt_dw). Le fact Gold portano le chiavi naturali; la join master è opzionale (commentata) tramite `retail_master_schema` (placeholder `gold_prod.condiviso`, dormiente).  
**Azione residua:** quando le anagrafiche saranno su Gold Retail (OP-02), agganciarle lì e ripuntare `retail_master_schema`.

### OP-02 — Nomi/percorsi esatti delle lookup condivise (Retail Master Data) 🟡
**Descrizione:** servono i nomi esatti delle lookup master Retail da leggere in sola lettura:
- `LU_ART_RADICE` (articolo, ex `L_ART`)
- `LU_FORNITORE` (fornitore, ex `L_FORN`)
- `LU_PDV` (punto vendita)
- `LU_GIORNO`, `LU_MESE` (calendario)

**Azione:** ricevere da Reply schema e nomi esatti (es. `gold_prod.<schema_master>.LU_ART_RADICE`) e permessi di lettura; abilitare le join master attualmente commentate nei notebook Gold.

### OP-03 — Lookup derivate `NCD_*` (categoria merceologica) 🔵 IN STAND-BY
**Descrizione:** `NCD_L_CAT_MERCL`, `NCD_L_CATEG_MERCEOLOGICA`, `NCD_L_CATEGORIA_MERCEOLOGICA`, `NCD_L_MAG_SITO_CAT_MERCL` sono lookup derivate dal logistico, oggi non sostituibili né ricostruibili.  
**Decisione provvisoria:** mantenere il riferimento alle tabelle `NCD_*` esistenti. Da ridiscutere in fase successiva.

### OP-04 — Confine merceologica logistica vs Retail 🟡
**Descrizione:** coesistono lookup merceologiche logistiche `LU_AREA_MERCL_LOGIS` / `LU_MACRO_AGG_MERCL` (da creare in gold logistico) e le `NCD_*` Retail (OP-03). Va definito il confine tra gerarchia master Retail e attributi merceologici logistici.  
**Azione:** allineamento con Reply (collegato a OP-03).

### OP-05 — Arricchimenti logistici su anagrafiche master 🟡
**Descrizione:** se servono attributi logistici aggiuntivi su entità master (es. info logistiche di un articolo), come gestirli senza duplicare il master.  
**Proposta:** dimensione di dominio logistico separata (es. `gold_prod.logistica.LU_ARTICOLO_LOGISTICA`, chiave `ART_RADICE`) in JOIN con `LU_ART_RADICE`.  
**Azione:** confermare con Reply.

---

## B. Landing Zone e modalità di ingestion

### OP-07 — Struttura path landing zone 🟡
**Descrizione:** pattern `<nome_sorgente>-landing` con struttura concordata per i flussi ODI.  
**Stato (call 2026-07-03):** push via **SFTP** (server `stdevdataplatformweudata.blob.core.windows.net:22`, modello G5/PJ — username/container per sorgente). Cartelle **`YYYY/MM/DD`** (3 livelli, confermato). Formato **CSV** (Parquet da abilitare in futuro). Landing = UC Volume `landing_dev` (D3). Convenzione `<source>-landing/{tabella}/YYYY/MM/DD/` già nei Bronze.  
**Azione residua:** ricevere credenziali SFTP specifiche Logistico (§F.2 di `12_checklist_infra_setup.md`); confermare con Foconi i nomi sorgente esatti (`logistix-landing`, `cdtdw-landing`, `stat-landing`).

### OP-08 — FULL vs DELTA e naming file 🟠
**Stato implementativo:** modalità Bronze definite per ciascuna tabella secondo l'analisi AS-IS verificata (DELTA_MERGE / FULL_OVERWRITE / SNAPSHOT). Il separatore CSV è hardcoded `;` (template).  
**Da confermare con i sistemi sorgente:**
- file giornaliero = delta per le transazionali? full per anagrafiche/giacenze?
- naming/partizionamento: un file/giorno (YYYY/MM/DD) o più file intra-day con timestamp?
- separatore CSV per sorgente: l'AS-IS CND usava `,`, oggi Bronze usa `;` — valutare widget.

### OP-09 — SLA di completamento push e ri-schedulazione workflow 🟡
**SLA confermato (call 2026-07-03):** file disponibili sulla landing entro le **04:00** (rivedibile al go-live).  
**Azione:** ri-fasare lo scheduling Databricks Workflows dopo le 04:00 (es. landing check 04:30, primo processing 05:00) quando i Workflows saranno creati (DBR-06). Schedule attuale (bozza locale) da spostare.

### OP-10 — Filtro statico AREE_MERCEOLOGICHE 🟠
**Descrizione:** l'AS-IS estrae con filtro `WHERE ARM_TIPO_AREA = 1`.  
**Azione:** concordare con la sorgente se il filtro è applicato a monte o se Bronze deve mantenerlo.

### OP-11 — Carichi trasferiti via SWAP 🟠
**Descrizione:** alcune query AS-IS considerano `STCAR_TRASFERITO_SWAP` (carichi trasferiti tra siti).  
**Azione:** definire con la sorgente come questi record vengono marcati nel delta (rischio doppio conteggio).

---

## C. Unity Catalog, Infrastruttura, CI/CD

### OP-18 — Granularità Service Principal ⏸️
**Stato (call 2026-07-03):** Technology sta valutando **un SP unico per tutta la data platform** (non per singolo progetto/job); la creazione passa da Technology, non da Reply.  
**Azione:** attendere comunicazione da Ippazio; recepire l'ID SP quando disponibile. Ping mensile.

### OP-19 — Cluster: job cluster serverless 🟢 RISOLTO
**Decisione (call 2026-07-03):** **job cluster SERVERLESS** dedicati ("nasce quando serve il job, killato al completamento"). Niente shared cluster, niente `node_type_id`/VM da gestire.  
**Stato implementativo (corretto 2026-08-04, ACT_9007):** i job girano su serverless **non dichiarando alcun compute** nei `workflows/*.yml` (dipendenze via blocco `environments` + `environment_key`). La precedente cluster policy `logistico-serverless-job-policy` (`runtime_engine=SERVERLESS`) è stata **rimossa**: `SERVERLESS` non è un valore valido per `runtime_engine` (solo `PHOTON`/`STANDARD`) e **le compute policy non si applicano al serverless**. Rimosse anche le variabili dead `spark_version`/`node_type_id`. Dettaglio e riferimenti doc in ADR-0009 (sezione "Aggiornamento 2026-08-04"). Attribuzione costi ex-`custom_tags` → OP H1 / ACT_9013.

---

## D. Monitoring, Data Quality, Go-live

### OP-20 — Sistema di alerting Databricks 🟡
**Stato implementativo:** notifiche email su failure come ponte.  
**Azione:** integrare quando rilasciato dal team Reply. Richiedere timeline/documentazione.

### OP-21 — Framework Data Quality condiviso 🔴 SENZA RISPOSTA — BLOCCANTE
**Descrizione:** non chiarito se esista un framework DQ standard di piattaforma.  
**Stato implementativo:** `dq_helper.py` custom in `logistica_utils`, con sopra `dq_monitor.py`
(severità/persistenza/gate) e `acceptance.py` (criteri dichiarativi). **Dal 2026-08-04 (ACT_9010) la DQ è
anche orchestrata**: task `dq_gate` in coda ai workflow Gold, esiti in `config_<env>.logistica_etl.dq_results`.
Il ponte interno è quindi completo e funzionante: se Reply indicherà uno standard, si sostituisce il motore
mantenendo i criteri già scritti (9 pipeline).  
**Azione:** **ri-sottoporre a Reply con priorità alta**. Allinearsi se adotta uno standard (Great Expectations, Lakehouse Monitoring, Soda).

### OP-22 — SLA di risposta ai failure 🟡
**Azione:** formalizzare nel `runbook.md` (es. failure Bronze critico → ripristino entro X ore) e i profili abilitati al riavvio job in prod.

### OP-23 — Dati sintetici per test E2E 🟡
**Descrizione:** servono dati sintetici rappresentativi per i test end-to-end. Ambienti riconosciuti: solo `dev` e `prod` (separati e speculari).  
**Azione:** definire con Reply un dataset di test rappresentativo per sorgente (Logistix multi-sito, CND, STAT).

### OP-24 — Criteri di accettazione parallel run 🟡
**Azione:** formalizzare nel `piani/cutover_plan.md` per ciascuna wave (durata, tolleranza numerica, responsabile validazione).

### OP-25 — Processo formale di go-live 🟡
**Azione:** produrre una proposta di processo e condividerla con Reply (approvazione, documenti, evidenze test, checklist, promozione dev→prod).

---

## E. Emersi dal primo run su dati reali (2026-06-10)

### OP-28 — Allineamento dimensioni: orphan-rate 🟢 RISOLTO (2026-06-17)
**Descrizione originale:** sui fact reali gli agganci dimensionali andavano in orphan elevato in modo sistematico (MAG_SITO_COD ~85-86%, CORRIERE_COD 100%, PREPARATORE/OPERATORE_COD 10-36%, AREA_MERCEOLOGICA_COD 51%).

**Risoluzione (2026-06-17 — validato su run completo 22 siti):**
- **OPERATORE_COD / PREPARATORE_COD** → 0.0% orphan su tutti i fact. Pattern `surrogate_key_fallback(null_val="ND")` per i NULL del sorgente (aggancio al membro `dim_operatore.ND` — TIPO=NON_RILEVATO). I NULL fisiologici di `PREPARATORE_COD` in `F_PREP_SPED` non erano orphan veri, ma NULL sorgente → gestiti con `null_val` invece di `default_val="-1"`.
- **OPERATORE_COD in F_TURNO/F_CARICO** → 0.0% tramite recovery `dim_operatore` da `storico_liste` (pattern OP-28 self-healing, memoria `op28-self-healing-operatori.md`). I codici operatore nei sistemi legacy 3A/4A vengono risolti tramite lo storico anagrafiche.
- **CORRIERE_COD su F_CARICO** → rimosso da F_CARICO (non è attributo rilevante del carico).
- **MAG_SITO_COD** → allineato via `normalize_sito` + alias_map da TABGEN nro_tab=7.

**Stato finale:** tutti i fact con orphan-rate 0.0% al run del 2026-06-17 (Silver 45/45 OK, Gold 26/26 OK).

### OP-29 — Stock: F_GIACENZE_DAILY 0 righe nel runner locale 🔵 FISIOLOGICO (ordering issue)
**Descrizione:** `silver_t_stock` produce 0 righe nel runner locale perché viene eseguito alfabeticamente prima di `silver_catena_unificata` (posizione [8] vs [20] nell'ordinamento dei notebook). `silver_t_stock` legge la `catena_unificata` del giorno precedente dal warehouse, che nella prima esecuzione del giorno non è ancora aggiornata.

**Non è un bug di pipeline:** il comportamento è fisiologico in locale. A regime su Databricks, il DAG di orchestrazione garantisce l'ordine corretto: `silver_catena_unificata` → `silver_t_stock`. Il runner locale esegue in ordine alfabetico senza DAG.

**Evidenza:** dal run 2026-06-17, `silver_t_stock` riporta "0 rows written (catena del giorno precedente)" mentre `silver_catena_unificata` dello stesso run ha scritto 23.506 righe — comportamento atteso e documentato.

**Azione:** gestita dal DAG in produzione Databricks. Nel runner locale: pre-verificare che catena_unificata del giorno precedente sia popolata prima di lanciare il run, oppure usare `--full_refresh` su `silver_t_stock` (non necessario in produzione).

### OP-30 — Incrementalità Bronze→Silver-clean e clean→prep 🟢 IMPLEMENTATO (2026-06-11)
**Risolto:** tre pilastri validati su dati reali:
1. **Bronze pruning (`_row_hash`)** su tutti i 14 bronze MERGE. Propagato solo il delta reale (22% su batch da 1.86M righe). Chiavi MERGE null-safe (`<=>`).
2. **Clean incrementale** — filtro `_bronze_load_date == run_date` + MERGE upsert null-safe + `dropDuplicates(MERGE_KEYS)`.
3. **Pattern #2 prep (chiavi-impattate)** — `storico_liste_uniche`, `storico_bolle_uniche`, `prep_sped`: ricalcolo solo dei gruppi toccati dal batch. Validato incrementale == full.

**Causa-radice risolta:** schema CSV posizionale disallineato → lettura per header (non per posizione). Vedi `bronze-csv-schema-by-name.md`.

### OP-31 — Validazioni delta sorgente da confermare sui dati reali 🟠
**Descrizione:** punti "DA VALIDARE" verificabili con dati reali:
- `ESTRAI_SPEDIZIONI` (coda CDC) come semi-join filtro: oggi leggiamo `spedizioni` a finestra piena su `SP_DATABOLLA`.
- `merge_keys`/`date_column` di `spedizioni` e `storico_liste` confermati sul primo run; da validare su più giorni.

**Azione:** decidere se replicare il semi-join ESTRAI_SPEDIZIONI; monitorare i merge_keys su delta multipli.

### OP-32 — Late-arriving dimensions: ri-risoluzione automatica degli orphan 🟢 FRAMEWORK COMPLETO + VALIDATO (2026-07-05) · residuo ART/FORN gated OP-02
**Descrizione:** quando un'anagrafica arriva **dopo** il fatto che la referenzia, la riga di fatto resta agganciata al sentinel −1 e **non si auto-corregge**. L'handler `gold_late_arriving_handler` (solo Carichi) gestisce il late-arriving del *fatto*, non della *dimensione*.

**✅ Implementato in `notebooks/gold/maintenance/gold_lad_resolver.py` (generico, config-driven):**
1. **Codice naturale preservato** nel fact in colonna `<dim>_COD_NAT` (L-01) — verificato su **5 fact core**: F_CARICO, F_PREP_SPED, F_TURNO_PREP_SITO, F_TRASPORTO, F_ORDINI.
2. **Job LAD generico** parametrico su (fact, fk, dim, nat_key): risolve righe `FK=−1 AND NAT NOT NULL` via join sulla dim; **idempotente**; full-overwrite preservando il partitioning.
3. **Retention/quarantena** (widget `retention_days`, default 30): i residui = orphan con NAT valorizzato ma **assente dal master** vengono segnalati come **candidati quarantena** (non distruttivo) → DQ.
4. **Skip corretto** degli `-1` con NAT null (assenza by-design, es. CORRIERE su F_CARICO): non falsi positivi.

**Validazione runtime (2026-07-05):** F_PREP_SPED 77 orphan `ART_RADICE_COD` rilevati → 0 risolti (77 residui = articoli non nel master `LU_ART_RADICE`) → segnalati per quarantena. F_CARICO CORRIERE_COD (59621 `-1`, NAT null) correttamente **skippato**. Fix applicati: aggiunto `ART_RADICE_COD` alla config F_PREP_SPED (mancava), rimosso `CORRIERE_COD` da F_CARICO (non-LAD), pulito calcolo `n_resolved`.

**Residuo aperto (dipende da esterni):**
- La risoluzione **ART/FORNITORE** richiede il **Retail Master** completo → **gated su OP-02**. Finché il master è parziale, i relativi residui restano candidati quarantena (fisiologico).
- **Quarantena "attiva"** (spostamento fisico righe): oggi solo *segnalazione* DQ; l'eventuale move in tabella di quarantena è sviluppo futuro se richiesto.
- **Orchestrazione:** ✅ **risolta (ACT_9014, 2026-08-04)** — il resolver è schedulato nei workflow: 5 task
  `lad_<fact>` in **testa** a `logistica_aggregati`, cioè **tra i fact e gli aggregati**, così gli `A_*`
  leggono fact con le FK già risolte. Chiude il residuo **L-03**. Resta on-demand anche il lancio manuale.

**Fuori scope LAD:** F_GIACENZE_DAILY, F_TRACCIABILITA_LOTTI, F_MOVIMENTAZIONE_CARRELLISTI (nessun `_COD_NAT`): referenziano solo dim **strutturali** (sito) a bassa frequenza → reprocess occasionale sufficiente (regime "dimensioni lente").

### OP-33 — Grana di `prep_sped`: `SEQ_PREL_PREP` nei MERGE_KEYS? 🟢 CONFERMATO (2026-07-05)
**Esito:** `SEQ_PREL_PREP` **deve** stare nei MERGE_KEYS → **già incluso** (grain a 9 chiavi in `silver_prep_prep_sped`).
**Evidenza legacy (`CDT_DW.sql`):** `INS_NEW_PREP_SPED` è un `INSERT ... SELECT ... FROM f_prep_sped` **senza GROUP BY** → porta `seq_prel_prep` a livello di riga (attributo di grana, non aggregato). La grana sorgente `silver_storico_liste_uniche` ha **8 chiavi che includono `LSPRL_SEQUE_PRELIEVO` + `LSPRL_FLAG_SCARTATO`**: ogni sequenza-prelievo è una riga distinta. Ometterla collasserebbe ~30k righe sorgente reali. Il grain a 9 chiavi attuale è corretto e allineato al legacy.

### OP-34 — Pattern #2 sui prep "piccoli" 🔵 BASSA PRIORITÀ
**Decisione (2026-06-11):** `prep_turno_prep_sito` (~52k, ~7s), `prep_ordini` (~1k), `prep_trasporto` (~23k) restano in **FULL recompute** — il costo/rischio di conversione supera il beneficio al volume attuale.  
**Azione (futura):** rivalutare quando i volumi crescono (storico pluriennale).

### OP-35 — Watermark / controllo incrementale (granularità per sorgente) 🟢 ROLLOUT COMPLETATO

**Decisione (2026-06-14):** tabella di controllo `control_<env>.etl.watermark`, chiave `(stage, sistema, tabella, sito)`. Design dettagliato in `docs/Archive/Design - Watermark ETL (OP-35).md`.

**Stato implementativo (2026-06-19): ROLLOUT COMPLETO su tutti i _clean.**
- Helper in `utils.py`: `get_control_table`, `ensure_watermark_table`, `read_watermark`, `update_watermark` (transazionale: su FAIL non avanza), `pending_landing_dates`. Layer `control` in `get_catalog`.
- Test `tests/local_bronze/test_watermark.py` (ALL_OK).
- **Pilota** `silver_storico_liste_clean` (stage `bronze_to_clean`, sistema `stat`, tabella `storico_liste`): validato 2026-06-14.
- **Rollout 2026-06-19** — tutti i notebook _clean aggiornati (pattern identico al pilota: widget `full_refresh`+`process_from`, filter `> process_from`, update OK + FAIL in except):

| Notebook | Sistema | WM_TABELLA |
|----------|---------|-----------|
| `silver_storico_bolle_clean` | stat | storico_bolle |
| `silver_carichi_testate` | logistix | sto_tes_carichi |
| `silver_carichi_dettagli` | logistix | sto_righe_carico |
| `silver_spedizioni_clean` | track | spedizioni |
| `silver_ordini` | logistix | ordini |

**Azione (residua):** W-05 `landing_to_bronze` nell'orchestratore (dipende da infra control catalog); W-06 Deploy Terraform control catalog a regime (dipende da I-02).

### OP-36 — Runner locale a sessione Spark singola → SIGKILL memoria 🔵 SOLO-LOCALE
**Workaround:** spezzare il run in fasi (`--only BRONZE / SILVER_CLEAN / SILVER_PREP / GOLD_FACT`). Idempotente grazie al MERGE upsert.  
**Non bloccante a regime:** su Databricks ogni notebook gira come task isolato.

---

## F. Certifica fact Gold vs CDT_DW — wave Carichi / Prep-Sped (2026-07-02)

Emersi durante la ri-certifica di `F_CARICO` e `F_PREP_SPED` con quadratura parametrica vs CDT_DW
(`scripts/quadratura/quadratura_fact.py`). Dettaglio operativo in `09_runbook_recert_carichi_prepsped.md`.

### OP-CAR-1 — `VAL_COSTO_CARICO` = NULL 🔵 FISIOLOGICO
Sorgente `cndstostock` dismessa (dati fermi al 2020). Il campo resta NULL. Collegato a ST-01/ST-02.

### OP-CAR-3 — `QTA_ORD_FORN` 🟢 RISOLTO + VALIDATO RUNTIME (opzione B, 2026-07-04; validato 2026-07-05)
La distribuzione della quantità ordinata fornitore (catena WL4, formula legacy) è degenere.
**Risolto con opzione B:** `silver_prep_carico` ora porta `QTA_ORDINATA` (da `carico_dettaglio`) e la
assegna alla **prima etichetta** del gruppo `(SITO_COD, ORDINE_NRO, ART_RADICE, ART_VAR)` via
`row_number` deterministico (order by `ETICHET_NRO`), 0 alle altre. `SUM(QTA_ORD_FORN)` per gruppo =
`MAX_QTA_ORD` legacy → quadra vs CDT_DW per SUM. ✅ **Validato al re-run 2026-07-05**: F_CARICO `SUM(QTA_ORD_FORN)=1.921.348` (prima 0), 38.210 gruppi.

**⚠️ Ammanco — unità (RISOLTO 2026-07-05):** `QTA_ORD_FORN` è in **COLLI**, `QTA_CARICO` in **PEZZI**
(fattore `NUM_PZ_IMB_ORD_FORN`). L'ammanco corretto è in pezzi: `A_INBOUND.QTA_ORDINATA_TOT =
SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN)` → ammanco +253.243 pz = **1.51%** (prima −14.6M per unità miste).
Rimossa la colonna morta `AMMANCO_QTA` da `carico_dettaglio` (ammanco = concetto di ordine, non di riga).

**Analisi legacy (2026-07-04, `CDT_ESTR.sql`):** la logica è in 2 stadi:
1. `SP_INS_WL4_CARICO` (righe 23669/23789): `QTA_ORD_FORN = CEIL/FLOOR( (MAX_QTA_ORD*QTA_CARICO) /
   DECODE(SUM_QTA_CAR,0,1, (MAX_QTA_ORD*QTA_CARICO)/SUM_QTA_CAR) )`. Il denominatore è
   **auto-cancellante** → l'espressione si riduce a `CEIL/FLOOR(SUM_QTA_CAR)`: **non usa la quantità
   ordinata** (bug latente ODI), mette il totale caricato del gruppo.
2. `SP_INS_T_CARICO` (righe 24129-24170): correzione "residuo sulla prima riga" —
   `RESTO_ATTRIB = MAX_QTA_ORD − SUM(QTA_ORD_FORN)` aggiunto alla prima riga (`MIN(ROWID)`).
   **Invariante netto:** `SUM(QTA_ORD_FORN)` per `(MAG_SITO, NUM_ORD_FORN, ART_RADICE, ART_VAR)` =
   `MAX_QTA_ORD` (quantità ordinata reale). Lo split per-riga è rumore; solo il totale è significativo.

**Sorgente dato:** `SRCAR_QTA_ORDINATA` (bronze `sto_righe_carico`) → aggregata in `WL2_QTA_ORDINATA.MAX_QTA_ORD`.

**Opzioni di replica (da decidere):**
- **A — bug-for-bug:** replicare stadio1+stadio2 fedelmente (identità riga con legacy, ma complesso e per-riga privo di senso).
- **B — equivalente pulito (consigliata):** assegnare `MAX_QTA_ORD` alla **prima etichetta** del gruppo (row_number deterministico), 0 alle altre → stessa `SUM` del legacy, quadra vs CDT_DW, deterministico. Richiede di portare `SRCAR_QTA_ORDINATA` nella catena silver fino a `silver_prep_carico`.
- **C — status quo:** `QTA_ORD_FORN=0` (perde la misura; blocca scarto/KPI qualità).

**Impatto downstream (FASE 5/6):** senza quantità ordinata non è calcolabile lo **scarto ricevimento**
→ `A_INBOUND_MENSILE` v4.0 non espone le misure di scarto e `kpi_qualita_ricevimento` è **bloccata**.
Scegliendo A/B si riabilitano.

### OP-CAR-4 — Quadratura CARICO: due cause 🟢/🟠
- **Causa A (RISOLTO 2026-07-02):** bug della quadratura, non della pipeline. `query_gold_kpi`
  leggeva TUTTI i parquet fisici via `rglob`, inclusi i tombstoned dei full_refresh → Gold gonfiato
  ~4× (Jun-17 mostrava 200-300%). Fix: helper `live_delta_files()` che legge il `_delta_log`
  (add−remove + checkpoint). La quadratura è ora affidabile. Vedi memoria [[delta-tombstone-pyarrow-read]].
- **Causa B → OP-CAR-5.**
- **Nota tooling (ACT_9009, 2026-08-04):** un secondo bug della **lettura Gold** è stato trovato e risolto — `pq.ParquetFile` non ricava le colonne di **partizione** dal path, quindi per `f_giacenze_daily` (`partitionBy DATA_FOTO`) e `f_turno_prep_sito` (`partitionBy DATA_PREPARAZ`) la colonna data risultava tutta NULL e la quadratura restituiva **silenziosamente 0 righe**. Ora le colonne di partizione sono reidratate dal path (`hive_partition_values`) e il reader è unico (`read_gold_frame`). Stessa famiglia di problemi del tombstone: *la quadratura sbagliava, non la pipeline*.

### OP-CAR-5 — Grain `silver_prep_carico` guidato dalla pesata (INNER JOIN) 🟢 RISOLTO (INNER confermato, 2026-07-04)
Un carico entra in Gold **solo** se la sua pesata è già arrivata e matcha sulle 5 chiavi di business.
Il dubbio era: mantenere INNER o passare a LEFT/catena WL.
**Verifica autoritativa (`CDT_ESTR_VISTE.sql`, vista `V_CARICO_ORDINARIO` righe 870-888):** nel legacy il
join alla pesata (`p`) è **INNER** — `t.mag_sito_cod = p.mag_sito_cod`, `p.psp_nrcarlog = r.srcar_nro_carico`,
`p.psp_numbol = r.srcar_nro_bolla_forn`, `p.psp_ncom = r.srcar_nro_ordine`, `P.ART_RADICE/VAR = R.ART_RADICE/VAR`
**tutti senza `(+)`**. Solo `cndstostock` (c) è outer. Quindi anche l'ODI **non emette carichi senza pesata**.
**Decisione: mantenere INNER JOIN pesata** (implementazione attuale già corretta e fedele all'ODI).
I "42 Solo in ODI" sono un artefatto di **timing/snapshot** (pesata arrivata prima del run ODI, non nel
nostro snapshot del `run_date`), non un difetto di join: si risolvono con la **finestra di ri-elaborazione**
già in pipeline (`gold_late_arriving_handler`, lookback 90g). Nessuna modifica al codice.

### OP-MOV-1 — Movimentazione carrellisti: grana per-movimento + annullamenti 🔵 SVILUPPO FUTURO
**Contesto (certifica 2026-07-05):** in CDT_DW la movimentazione è una **famiglia**: `F_MOV_CARR` (grana **per movimento**), `F_OPER_CARR_LAV` (ore lavorate), `F_MOV_ANN_CARR` (**movimenti rifiutati/annullati**). Il nostro `F_MOVIMENTAZIONE_CARRELLISTI` ha grana **giornaliera** (carrellista×giorno×sito) che fonde attività+ore.
**Fatto (2026-07-05):** colmato il gap misura aggiungendo **`NUM_PLT_MOVIMENTATI`** (pallet/giorno, 2 se `DOPPIO_MOVIM='SI'`, allineato a `NUM_PLT_MOV_CARR`) mantenendo la grana giornaliera. Sorgente `dettaglio_carr` già presente.
**Sviluppo futuro (se emergono requisiti):**
1. **Grana per-movimento**: fact dedicato a grana singolo movimento (come `F_MOV_CARR`) per analisi dettaglio pallet/percorso, oltre al riepilogo giornaliero.
2. **Movimenti annullati/rifiutati** (`F_MOV_ANN_CARR`): oggi non modellati; valutare se rilevanti per KPI qualità/efficienza carrellisti.
Nessun blocco sorgente (`dettaglio_carr` disponibile) → è una scelta di modellazione, decisione interna al flusso.

### OP-PSP-1 — Righe prep senza bolla (scartate TIPO_SCAR 09/10) 🟢 CHIUSO (comportamento atteso)
399k righe `DATA_BOLLA_SPED=NULL` sono articoli scartati prima della spedizione → mai una bolla.
Verificato su Oracle: `CDT_DW.F_PREP_SPED` ha **0 righe** con `GIORNO_BOLLA_SPED_ID=0` → CDT_DW le
esclude a monte; il nostro Gold le include (coverage aggiuntiva). Non è un gap. Aggiunto blocco
"SCARTATE" a `quadratura_fact.py` che documenta l'asimmetria (sempre 0 ODI vs N Gold).

### OP-PSP-2 — `DATA_PREL_INIZ` NULL 🟢 RISOLTO (2026-07-02)
`LSPRL_DATA_INIZIO_PRELIEVO` è NULL nella sorgente Logistix. Fix in `silver_prep_prep_sped`: costruire
il timestamp da `julian_to_date(LSPRL_DATA_PRELIEVO.cast("long")) + LSPRL_ORA_PRELIEVO` (formula
CDT_ESTR_VISTE.sql). Partizione Gold `DATA_PREL` ora distribuita su date reali (giu-04…26),
`__HIVE_DEFAULT_PARTITION__` = 0. Residuo ~0.01% NULL (594/6.9M righe di storico senza la colonna).

---

## G. Migrazione Azure Databricks (2026-07-02)

Piano completo in `10_piano_migrazione_databricks.md`. Il codice notebook è **già UC-native** (nomi
tabella a 3 livelli `catalog.schema.table` via `get_catalog()`); lo shim locale collassa a 2 livelli
solo per Hive/Derby. Decisioni bloccanti per il setup, da concordare col team DWH:

| ID | Decisione | Stato | Scelta | Implementazione |
|----|-----------|-------|--------|-----------------|
| **D1** | Catalog di controllo: `control_dev` (nostro) vs `config_dev` (DWH) | ✅ DECISO 2026-07-02 | **`config_dev`** con schema `logistica_etl` | `_CATALOG_MAP["dev"]["control"] = "config_dev"` — `utils.py` e `run_notebook.py` aggiornati (DBR-03 ✅) |
| **D2** | Anagrafiche cdt_dw: riuso `bronze_dev.prodotto/fornitore/pdv` vs `condiviso` proprio | ✅ DECISO 2026-07-02 | **Schema proprio `bronze_dev.condiviso`** (opzione B). In futuro aggancio a Gold. | `get_condiviso_schema(env)` in `utils.py`; widget default aggiornati su 7 notebook (DBR-02 ✅) |
| **D3** | Landing storage: UC Volume `landing_dev` vs ADLS esterno | ✅ DECISO 2026-07-02 | **UC Volume `landing_dev`** (al 99% confermato) | `landing_mode = "volume"` già default Terraform; path `/Volumes/landing_dev/logistica/files` |
| **D4** | Ambiente prod: `bronze`/`silver`/`gold` (senza `_dev`) sono i prod? | ✅ DECISO 2026-07-02 | **`bronze_prod` / `silver_prod` / `gold_prod`**. I catalog senza suffisso eliminati. Stage = `_stage` (non configurato). | `_CATALOG_MAP["prod"]` aggiornato in `utils.py`. PROD non deployato per ora. |
| **D5** | Lettura DWH legacy per quadratura: canale diretto vs export su landing | ✅ DECISO 2026-07-02 | **Export su landing** per ora. Futuro: connessione diretta Oracle opzionale. | `quadratura_fact.py` pyarrow locale resta; backend Spark in DBR-04 (da implementare) |

**Nota:** l'accesso Oracle in lettura NON serve più su Databricks — i dati (incluse le anagrafiche
cdt_dw) arrivano in **push** dai sorgenti. Elimina secret scope Oracle, VNet peering, `oracledb` sul cluster.

---

## Riepilogo per stato (aggiornato 2026-08-27)

| Stato | Open points |
|-------|-------------|
| 🔴 Aperto / Bloccante | **OP-21** (DQ framework — senza risposta Reply), **OP-QDR-1** (quadratura non significativa senza backfill storico) |
| 🟠 Da confermare (sorgente) | OP-08, OP-09, OP-10, OP-11, OP-31, **OP-CAR-7** (CORRIERE_COD → 'ND') |
| 🟡 Da confermare (Reply/DWH/piattaforma) | OP-01, OP-02, OP-04, OP-05, OP-07, OP-20, OP-22, OP-23, OP-24, OP-25, **OP-INF-1** (grant CREATE SCHEMA alla MI → blocca `apply` infra DEV), **OP-GIA-1** (170k righe giacenze — decisione) |
| 🔵 Stand-by / Fisiologico / Bassa priorità | OP-03, **OP-29** (ordering fisiologico locale), OP-33, OP-34, OP-36, **OP-CAR-1**, **OP-MOV-1** (grana per-movimento — futuro) |
| ⏸️ On hold (Technology) | **OP-18** (Service Principal unico data platform) |
| 🟢 Risolto | **OP-19** (serverless), **OP-28** (orphan 0.0%), **OP-30** (incrementalità), **OP-32** (LAD framework completo+validato; residuo ART/FORN gated OP-02), **OP-35** (watermark), **OP-CAR-4/A** (tombstone quadratura), **OP-CAR-6** (fallback anagrafiche non più silenzioso), **OP-PSP-1** (scartate), **OP-PSP-2** (DATA_PREL_INIZ), **OP-TST-1/2** (fixture/FQN test), **D1-D5** (migrazione Databricks) |

---

## OP risolti dalla revisione end-to-end (rimossi dal registro attivo)

- **OP-06** — Naming `dim_*`→`LU_*`, `dm_*`→`A_*` applicato a tutti i notebook Gold, KPI, optimize, workflow.
- **OP-12** — Normalizzazione articolo radice/variante spostata in Silver.
- **OP-13** — Driver `WL2_CATENA` rimossa dal Bronze.
- **OP-14** — `DETTAGLIO_CARR` e `IMBFMOVIM` gestite come tabelle distinte.
- **OP-15** — Unione carrellisti+preparatori in `silver_dim_operatore`.
- **OP-16** — Prep-spedizioni da STAT: sorgente corretta nei Bronze.
- **OP-17** — Superato dal ridisegno scelta B / standard 2-notebook (2026-06-10).
- **OP-26** — Superato dal ridisegno scelta B: trasporti da `SPEDIZIONI@TRACK` via landing.
- **OP-27** — Gold ricostruito su colonne reali del Silver corretto.
- **OP-28** — Orphan-rate 0.0% su tutti i fact (2026-06-17).

### OP-CAR-6 — Fallback anagrafiche silenzioso: `PES_CARICO`/`VOL_CARICO` NULL non intercettati 🟢 RISOLTO (2026-08-21)
**Aperto**: 2026-08-21 ([[ACT_9015]])   **Interno** (non Reply)

`attach_carico_peso_volume` legge `{retail_master_schema}.LU_ART_UNITA_LOGISTICA`; se lo schema non esiste, il
`try/except` degrada `PES_CARICO`/`VOL_CARICO` a NULL con un solo `logger.warning` e la pipeline **chiude in
successo**. Riscontro reale: 59.621/59.621 righe di `F_CARICO` con entrambe le misure NULL, e `dq_gate`
**13/13 PASS**. Nessun check DQ copre il null-rate di queste due misure.

In cloud lo stesso scenario (schema mal configurato) produce un fact "verde" e inutilizzabile.

**RISOLTO** (2026-08-21, ACT_9015):
- `PES_CARICO` e `VOL_CARICO` aggiunti a `not_null` (BLOCKING) nei criteri di `gold_f_carico`.
  `measures_nonneg` da solo non li copriva: un NULL non e un valore negativo.
- Fallback non piu silenzioso: log **ERROR** + `dq_result` strutturato
  (`check_name=anagrafica_peso_volume_disponibile`, `passed=false`) con indicazione del widget da correggere.
- Divergenza locale sanata: le 6 LU ripubblicate in `bronze_dev.condiviso` (sede D2), quindi il
  **default del widget funziona senza override** e il locale rispecchia il cloud.

**Verifica end-to-end**: con default -> `PES_CARICO` NULL 0, SUM=32.912.850, gate 16/16 PASS.
Con schema errato -> allarme ERROR + `DQBlockingError` su 2 check BLOCKING (prima: 13/13 PASS silenzioso).

### OP-CAR-7 — `CORRIERE_COD` NULL trattato come orfano invece che come 'ND' 🟠
**Aperto**: 2026-08-21 ([[ACT_9015]])   **Interno**

`silver_curated.carico.CORRIERE_COD` è NULL su tutte le righe (la sorgente non porta il vettore per i carichi),
quindi `F_CARICO.CORRIERE_COD` è sentinel `-1` al 100% e genera un allarme orphan-rate permanente. In
`attach_carico_dimensions` gli operatori NULL diventano `'ND'` (non orfani), il corriere no: trattamento
incoerente.

**Azioni**: decidere se allineare il corriere al pattern `'ND'`, oppure colmare la sorgente a monte
(`STCAR_COD_CORRIERE`). Fino ad allora l'allarme al 100% è rumore noto.

### OP-QDR-1 — Quadratura non significativa senza backfill dello storico 🔴
**Aperto**: 2026-08-21 ([[ACT_9015]])   **Interno**

La quadratura confronta il Gold locale con CDT_DW, che ha la storia di produzione completa: sulle date non
ingerite in locale tutte le chiavi risultano "solo in ODI". Sulla finestra documentata
(`--da 2026-06-09 --a 2026-06-21 --soglia 5.0`) i 4 fact quadrabili risultano KO con ~100% di chiavi anomale,
dominate dalla copertura parziale della landing e **non** da errori di calcolo. Condizione già dichiarata attesa
in `07_certifica_gold_vs_cdtdw.md` finché il backfill non è completo.

**Azioni**: (a) derivare automaticamente la finestra `--da/--a` dalla copertura effettiva del Gold, così l'esito
è interpretabile; (b) confermare con `--discover` le colonne CDT_DW di `GIACENZE` (`GIORNO_STOCK_ID` inesistente
in `CDT_DW.F_STOCK`) e `TURNO_PREP_SITO` (`GIORNO_PREPARAZ_ID` inesistente), oggi `oracle_confirmed: False`;
(c) ripetere la certificazione numerica dopo il backfill.

### OP-GIA-1 — 170k righe di `F_GIACENZE_DAILY` non ricostruibili (decisione) 🟡
**Aperto**: 2026-08-21 ([[ACT_9015]])   **Decisione utente**

`F_GIACENZE_DAILY` è un fact snapshot: `DATA_FOTO` deriva dalla data di caricamento. La landing conserva un solo
snapshot (`2026/06/09`), quindi le partizioni 13/16/19/21 giugno (~170k righe, calcolate con logica pre-fix) non
sono ricostruibili da nessun livello.

**Opzioni**: (a) tenerle — la tabella resta a logica mista e contamina quadratura e DQ; (b) rimuoverle — baseline
coerente a data singola, ma **perdita definitiva**. In cloud il problema non si ripresenta: l'initial load
costruirà la storia dal primo giorno con la logica corrente.

### OP-TST-1 — Fixture DQ: `float` in colonna `DecimalType` rifiutato da pyspark 3.5.9 🟢 RISOLTO (2026-08-22)
**Aperto**: 2026-08-22 ([[ACT_9016]])   **Chiuso**: 2026-08-22   **Interno**

I fixture di `test_dq_carichi`/`TestDQHelper` passavano `float` Python a colonne `DecimalType(18,4)`; con
`pyspark 3.5.9` (tirato da `delta-spark==3.2.0`, più recente del 3.5.0 dell'immagine base) il type-check stretto
rifiutava la coercizione → 12 test in *error* al setup, prima di testare la logica DQ.

**Risolto** con opzione (a): `sample_carichi_df` in `tests/conftest.py` usa `Decimal(...)` invece di `float(...)`.
Da `12 errors` a **0** su `test_dq_carichi`+`test_logistica_utils` (`50 passed`). Lo skew di versione pip↔SPARK_HOME
resta annotato in [[ACT_9016]] ma non è stato pinnato per non nasconderlo.

### OP-TST-2 — `merge_into` costruisce FQN con punto iniziale in locale 🟢 RISOLTO (2026-08-22)
**Aperto**: 2026-08-22 ([[ACT_9016]])   **Chiuso**: 2026-08-22   **Interno**

`delta_helper` componeva un FQN a 3 parti `{catalog}.{schema}.{table}`; in locale il catalog è vuoto →
`.test_delta_db.<tab>` che lo `spark_catalog` (2 parti) rifiutava con `ParseException` → 3 test *failed*. Su
Databricks (UC, 3 livelli) era già corretto: era l'ambiente locale l'anomalia.

**Risolto** con opzione (a): helper `_build_fqn(catalog, schema, table)` che con catalog vuoto/None restituisce
`schema.table`. Usato da `DeltaHelper._fqn` e da `get_watermark` (stesso bug latente). Suite completa **111/111
verde**, sia coi 5 file nominati sia con `pytest` bare (aggiunto `--ignore=tests/local_bronze` in `pytest.ini`).

### OP-INF-1 — Grant `CREATE SCHEMA` alla Managed Identity sui catalog DEV 🟡 (attesa Reply)
**Aperto**: 2026-08-27 ([[ACT_0.1.6]])   **Da confermare (Reply/piattaforma)**

L'`apply` Terraform DEV (via MSI — auth: [[ADR-0022]]) è autenticato ma bloccato: la MI (SP applicationId `54d17490-…`) non ha
`CREATE SCHEMA` su `bronze_dev`/`silver_dev`/`gold_dev`/`config_dev`/`landing_dev`. Il `plan` è verde
(15 add, 0 destroy); 0 risorse create (stato invariato) → [[LL-018]] (authN ≠ authZ).

**Azione**: richiesti a Francesco Giambona (Reply, fr.giambona@reply.it) i grant `USE CATALOG` + `CREATE SCHEMA`
sui 5 catalog DEV per la MI (mail 2026-08-27). Ottenuti → ri-run pipeline `infrastructure` + clic `apply`.

## Riferimenti
- `docs/Archive/Open Points - Logistico 2.0.md` — versione originale 2026-06-10
- `docs/main/03_pipeline_mapping.md` — mapping completo pipeline layer per layer
- `docs/main/04_architettura.md` — architettura, pattern tecnici, decisioni chiave
- `DOCS/analisi/Lookup Logistico 2.0 - Mappatura LU.xlsx` — mappatura lookup `LU_*` e owner
- `DOCS/analisi/Tabelle Sorgenti - Logistico 2.0.xlsx` — tipo caricamento verificato
