# Certifica Gold vs CDT_DW — Piano di quadratura per tabella

**Progetto:** Logistico 2.0  
**Data:** 2026-06-25  
**Versione:** 1.0  
**Scopo:** Per ogni tabella del layer Gold (Spark/Delta) documentare la controparte CDT_DW (Oracle/ODI),
le colonne da confrontare, la procedura di quadratura e le criticità note.

---

## Legenda stati

| Stato | Significato |
|---|---|
| `TODO` | Procedura non ancora eseguita |
| `IN CORSO` | Script in sviluppo o primo run in corso |
| `BLOCCATO` | Dipende da un prerequisito non risolto |
| `OK` | Prima quadratura eseguita con esito positivo |
| `KO` | Differenze rilevate, analisi in corso |
| `N/A` | Nessuna controparte diretta in CDT_DW |

---

## 1. Fact table — logistica

### 1.1 F_CARICO

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_carico` |
| **CDT_DW** | `CDT_DW.F_CARICO` |
| **Grain** | 1 riga = riga dettaglio carico (testata × articolo × sito) |
| **Partizione** | `ANNO_MESE` (YYYYMM) |
| **Stato** | `IN CORSO` |

**Mapping colonne chiave**

| Gold | CDT_DW | Note |
|---|---|---|
| `SITO_COD` | `MAG_SITO_COD` | **RISOLTO (2026-07-01)**: mapping via `CDT_ESTR.S_LOGISTIX`. Il codice canonico Gold = `int(cifre di MAG_SITO_COD)` zero-padded a 2 (`0005C`→`05`, `0035A`→`35`). Lo script legge S_LOGISTIX (siti attivi) e rimappa le chiavi CDT_DW prima del confronto. |
| `DATA_CARICO` | join `L_GIORNO.GIORNO_DT` via `GIORNO_CARICO_ID` | In CDT_DW la data è una FK surrogate; bisogna fare JOIN con `CDT_DW.L_GIORNO`. |
| `QTA_UF_RILEVATA` | `QTA_CARICO` | Quantità in unità fornitore rilevata al carico. |
| `PESO_LORDO` | `PES_CARICO` | Peso lordo. CDT_DW non espone PESO_NETTO separato. |
| `ART_RADICE_COD` (→`ART_RADICE_ID`) | `ART_RADICE_ID` | Codice/ID articolo radice. |
| `ART_VARIANTE_LOGIS_COD` (→`ART_VARIANTE_LOGISTICA_ID`) | `ART_VAR_LOGIS_ID` | Variante **logistica** (chiave dimensionale esposta), da `LU_ART_VARIANTE_LOGISTICA`. |
| `FORNITORE_COD` | `FORN_COD` | Codice fornitore. |

**Decisione modello dimensione articolo (2026-07-01)**: il nostro F_CARICO **semplifica** la dimensione articolo rispetto a CDT_DW. Eliminati:
- `ART_COD`/`ART_ID` — **obsoleti**, sostituiti da `ART_RADICE_ID`.
- `ART_ST_RADICE_ID`, `ART_ST_VAR_LOGIS_ID` — FK a lookup **storicizzate**: superate.

Esposti solo **`ART_RADICE_ID`** + **`ART_VARIANTE_LOGISTICA_ID`** (variante logistica, lookup `LU_ART_VARIANTE_LOGISTICA`). È lo stesso asse su cui pesata↔dettaglio si agganciano nel grain ODI, quindi nessuna risoluzione aggiuntiva: `ART_VARIANTE_LOGISTICA_ID` è già nell'anagrafica `LU_ART_UNITA_LOGISTICA` estratta (mappa `ART_RADICE_COD`+`ART_VARIANTE_LOGIS_COD` → `ART_VARIANTE_LOGISTICA_ID`). Coerente con [[gold-natural-key-vs-surrogate]]: natural key ora (`_COD`), ID surrogati in futuro.
| `OPERATORE_COD` | `OPER_VALID_COD` (+`OPER_VALID_ID`) | Natural key operatore **validante**. Agganciata a `LU_OPERATORE`. |
| `RICEVITORE_COD` | `OPER_RICEV_COD` (+`OPER_RICEV_ID`) | Natural key operatore **ricevente**. **Cablata 2026-07-01** a `LU_OPERATORE` (prima non agganciata). |
| `CORRIERE_COD` | `VETTORE_CARICO_COD` | Vettore carico inbound. **Reintrodotta 2026-07-01** (← `STCAR_COD_CORRIERE`), agganciata a `LU_CORRIERE`. |
| `NUM_PZ_IMB_SITO`, `NUM_PZ_IMB_EFF_FORN`, `NUM_PZ_IMB_ORD_FORN`, `NUM_IMB_STRATO_PLT_SITO`, `NUM_STRATO_PLT_SITO`, `NUM_IMB_ULT_STRATO_SITO`, `NUM_IMB_STRATO_PLT_FORN`, `NUM_STRATO_PLT_FORN`, `NUM_IMB_ULT_STRATO_FORN` | omonime | Struttura imballo/pallet. **Aggiunte 2026-07-01** (← `SRCAR_*` già in Bronze). |
| `VAL_COSTO_CARICO` | `VAL_COSTO_CARICO` | **Aggiunta 2026-07-01** = `NRO_PZ_CARICATI × PREZZO_ACQUISTO` (formula ODI da confermare). |

**Decisione modello chiavi (2026-07-01)**: il Gold adotta **natural key validate** contro le lookup (`surrogate_key_fallback`: match | `-1` orfano | `ND` NULL legittimo), NON ID surrogati interi. CDT_DW espone anche gli `_ID` numerici (`OPER_VALID_ID`, `OPER_RICEV_ID`): l'introduzione di ID surrogati nel nostro Gold è rimandata a una fase futura (richiede colonna ID nelle dim + modifica `surrogate_key_fallback` + propagazione a tutte le fact).

**Procedura**

```
scripts/quadratura/quadratura_f_carico.py --da YYYY-MM-DD --a YYYY-MM-DD
```

1. Connessione Oracle READ-ONLY a `CDT_DW.F_CARICO` (stesso utente del cdtdw extractor).
2. JOIN con `CDT_DW.L_GIORNO` per ottenere la data dal surrogate `GIORNO_CARICO_ID`.
3. Aggregazione per `(SITO_COD, DATA)`: COUNT, SUM QTA_CARICO, SUM PES_CARICO.
4. Lettura Gold parquet locale con pandas/pyarrow (no JVM — Spark non compatibile con Python 3.13 su Windows).
5. Confronto con soglia default 1%.

**Criticità note**

- **SITO_COD [RISOLTO 2026-07-01]**: mapping via `CDT_ESTR.S_LOGISTIX` (tabella statica dei siti attivi). Il codice canonico Gold = `int(cifre di MAG_SITO_COD)` zero-padded a 2. Dopo il fix, le chiavi sito CDT_DW e Gold si sovrappongono correttamente.
- **Intervallo**: la landing parte dal 2026-06-09; confrontare solo la finestra disponibile. **In locale la landing risulta completa solo per il 2026-06-17**; gli altri giorni (15,16,18-21) hanno ingestion parziale → volumi Gold inferiori (non è un difetto pipeline).
- **PESO_LORDO ≈ 0 in Gold [DA INVESTIGARE]**: dopo il fix sito, il confronto mostra `PESO_LORDO` quasi sempre 0 in Gold mentre CDT_DW lo valorizza. Il LEFT JOIN con `pesata` in `silver_prep_carico` non produce pesi in locale. Verificare se la sorgente `pesata` è popolata e se la chiave di join `(SITO_COD, CARICO_LOG_NRO)` è corretta.
- **Differenza di grain [DA CHIARIRE]**: sul 2026-06-17 (giorno completo) la **QTA totale combacia** (delta <5% per molti siti, sito 57 esatto) ma il **numero righe è molto diverso** (es. sito 57: ODI 227 vs Gold 9). `CDT_DW.F_CARICO` ha grain più fine — probabilmente **per etichetta** (`NUM_ETICH`), mentre il nostro Gold è a grain riga-dettaglio. Il confronto sui volumi/misure resta valido; il confronto sui COUNT righe NON è comparabile senza normalizzare il grain.

**Esito prima quadratura post-fix sito (2026-07-01, 15-21 giugno, soglia 5%)**

- Codici sito ora allineati (fix S_LOGISTIX confermato).
- Il **17 giugno** (unico giorno con landing completa) mostra QTA allineata sotto soglia per i siti principali → **il flusso di calcolo QTA è coerente con ODI**.
- Restano da chiudere: (1) PESO_LORDO=0, (2) grain per-etichetta vs riga-dettaglio, (3) completare la landing locale sugli altri giorni per una quadratura piena.

#### Colonne mancanti — analisi di recuperabilità (2026-07-01)

Gold F_CARICO ha 31 colonne, CDT_DW.F_CARICO ne ha 63. Analisi incrociata delle 63 colonne CDT_DW contro le sorgenti raw (`STO_RIGHE_CARICO`/`SRCAR_`, `STO_TES_CARICHI`/`STCAR_`, `PESATE`/`PSP_`) e verifica popolamento su CDT_DW (17/6, 28.062 righe).

**A. Nel Bronze ma scartate in Silver — [IMPLEMENTATO 2026-07-01]**

Tutta la struttura imballo/pallet è già in `bronze.sto_righe_carico` (SOURCE_COLS). Rinominata in `silver_carichi_dettagli`, portata da `silver_prep_carico` e propagata a `gold_f_carico` (+ `gold_late_arriving_handler`):

| CDT_DW | pop. | Colonna raw (SRCAR_) |
|---|---|---|
| `NUM_PZ_IMB_SITO` | | `SRCAR_PZ_CARTONE` |
| `NUM_PZ_IMB_EFF_FORN` | | `SRCAR_PZ_CART_FOR` |
| `NUM_PZ_IMB_ORD_FORN` | | `SRCAR_PZ_CARTONE_ORD` |
| `NUM_IMB_STRATO_PLT_SITO` | | `SRCAR_CART_X_STRATO` |
| `NUM_STRATO_PLT_SITO` | | `SRCAR_STRATI_PALLET` |
| `NUM_IMB_ULT_STRATO_SITO` | | `SRCAR_CART_X_ULT_ST` |
| `NUM_IMB_STRATO_PLT_FORN` | | `SRCAR_CART_X_ST_FOR` |
| `NUM_STRATO_PLT_FORN` | | `SRCAR_STRATI_PA_FOR` |
| `NUM_IMB_ULT_STRATO_FORN` | | `SRCAR_CART_X_UL_FOR` |

**B. In Silver ma non portate a Gold — recupero banale (aggiungere alla select di `silver_prep_carico` + `gold_f_carico`)**

| CDT_DW | Colonna Silver esistente |
|---|---|
| `ORA_CARICO` | `ORA_CARICO` (dettaglio) |
| `NUM_BOLLA_FORN` | `BOLLA_FORN_NRO` (dettaglio) |
| `GIORNO_BOLLA_FORN_ID` (→data) | `DATA_BOLLA_FORN` (dettaglio) |
| `GIORNO_SCAD_CARICO_ID` (→data) | `DATA_SCADENZA` (dettaglio) |
| `GIORNO_EMIS_ORD_FORN_ID` (→data) | `DATA_EMISSIONE_ORD` (testata) |
| `GIORNO_PREV_CONS_FORN_ID` (→data) | `DATA_CONFERMA_ORD` (testata, da confermare semantica) |

**C. Calcolabili da colonne disponibili**

| CDT_DW | pop. | Formula | Stato |
|---|---|---|---|
| `VAL_COSTO_CARICO` | 24% | `NRO_PZ_CARICATI × PREZZO_ACQUISTO` | **IMPLEMENTATO 2026-07-01** (formula ODI esatta da confermare) |
| `NUM_IMB_CARICO` / `NUM_PLT_CARICO` | 100% | derivati da pezzi caricati + struttura imballo (gruppo A) | TODO — formula ODI non nota, NON inventare |
| `FASCIA_ORA_ID` / `FASCIA_LAV_SITO_ID` | | da `ORA_CARICO` + dimensione fascia | TODO — serve dimensione fascia |
| `QTA_UF_CARICO` | ≠QTA 17% | misura distinta — regola ODI da capire | TODO |

**D. NON recuperabili (calcolate da ODI su master/tabelle non in landing)**

`VOL_CARICO` (74%, serve volume unitario articolo), `GG_VITA_RESID_ART_CARICO` (77%), `GG_DIFF_SCAD_*` (anagrafica scadenza), `AFFID_TEMPI_FORN_COD/ID` (lookup affidabilità), `ART_MODL_PES_COD/ID` (modello peso), `LOAD_ID` (tecnica ODI), flag ODI (`STESSO_IMB_CARICO_FLAG`, `CARICO_INCOMPLETO_FLAG`, `DATI_STO_CARICO_FLAG`). `GG_RITARDO_CONS` popolata solo su 33 righe → trascurabile.

**E. Grain — `NUM_ETICH` (← `PESATE.PSP_NUMETIC`) [DECISO: allineare a ODI — grain etichetta]**

`CDT_DW.F_CARICO` è a grain **per etichetta**: chiave ≈ `(MAG_SITO_COD, NUM_DOC_CARICO, NUM_ETICH)` (28.062 righe, 27.742 NUM_ETICH distinti sul 17/6; `ART_COD` costante, l'articolo al grain è `ART_RADICE_COD`+`ART_VAR_LOGIS_COD`). Il nostro Gold è a grain riga-dettaglio.

**Logica ODI reale (fonte autoritativa: `DOCS/99. SCRIPT/CDT_ESTR.sql` + `CDT_SA.sql`)** — NB: `mapping_carichi.md` è speculativo/pre-schema, da NON usare.

Catena worklist: `PESATE/STO_*` → `WL2_CARICO_ORDINARIO` → `WL3_CARICO` → `WL4_CARICO` → `T_CARICO` → `CDT_DW.F_CARICO`. Caratteristiche chiave:
- Grain **etichetta** stabilito dalle PESATE; articolo risolto via **EAN** (`PSP_ARTEAN13` → anagrafica articoli), non dal dettaglio carico.
- `T_CARICO` (SP_INS_T_CARICO): dedup su ROWID + **distribuzione della qta ordinata residua sulla prima riga**.
- **`PES_CARICO`/`VOL_CARICO` da anagrafica articolo** (`CDT_DWH_EDW.LU_ART_UNITA_LOGISTICA`, `ART_UNITA_LOGISTICA_COD=1`), NON dalla pesata fisica:
  `PES_CARICO = CASE WHEN ART_MODL_PES_COD>1 THEN QTA_UF_CARICO ELSE ART_UNITA_LOGISTICA_PESO_LORDO × QTA_UF_CARICO END`;
  `VOL_CARICO = QTA_CARICO × ALT_PZ × LAR_PZ × PRO_PZ / 1000`. Il peso fisico pesato va nel fact separato `F_PESATE`.

**Scope reale**: questa catena **non esiste** nei nostri notebook (l'area carichi usa il `testata⋈dettaglio` semplificato). Allineare a ODI (B) = **ricostruire la pipeline worklist WL_CARICO** (~2000 righe PL/SQL da portare), non un ritocco di `silver_prep_carico`. Il fix "PESO_LORDO da pesata" è concettualmente errato e va sostituito con la formula anagrafica (C).

**Prerequisito C — RISOLTO parzialmente (2026-07-01)**: `LU_ART_UNITA_LOGISTICA` aggiunta al cdtdw extractor (READ-ONLY, filtro `ART_UNITA_LOGISTICA_COD=1`, join `LU_ART_RADICE` per `ART_MODL_PES_COD` + variante logistica), estrazione validata. Resta il full extract nel re-run.

**OPEN POINT OP-CAR-1 — VAL_COSTO_CARICO non calcolabile**: ODI lo deriva da `STKULTSTOCK` di `CNDSTOSTOCK`, sorgente Logistix **dismessa** (la replica `wl1_cndstostock` è ferma al 2020). Non ha senso agganciare la tabella morta. In CDT_DW stesso è popolato solo al 24%. → lasciare `VAL_COSTO_CARICO` NULL, documentato come open point. Da valutare se dismettere del tutto la colonna.

**OP-CAR-2 — risoluzione articolo pesata — RISOLTO (2026-07-02)**: la colonna `pesata.PSP_ARTEAN13` (silver `ART_EAN13`) **non è un EAN ma un codice MSI** — coerente con la logica ODI reale (`SP_INS_F_PESATE`: `psp_artean13 = wl1_articoli_foce.ARFC_COD_MSI`, un match su MSI). Verificato: overlap `pesata.ART_EAN13` ↔ `dettaglio.MSI_COD` = **100%** (12.559/12.559); join `(SITO_COD, CARICO, MSI)` risolve l'articolo per il **100%** delle righe pesata. → **nessuna anagrafica EAN necessaria, nessuna sorgente morta**: la pesata aggancia direttamente `carico_dettaglio` su MSI (che porta già `ART_RADICE`/`ART_VAR` via OP-12). Grain etichetta (B) sbloccato con le sole sorgenti vive.

**F. `VETTORE_CARICO_COD` (100% popolato in CDT_DW) — [IMPLEMENTATO 2026-07-01]**

Il corriere era stato **rimosso** da `gold_f_carico` (task #30) sull'assunzione "0 occorrenze in CDT_DW", **errata** (verifica: popolato al 100%). Reintrodotto: `CORRIERE_COD` (← raw `STCAR_COD_CORRIERE`, Silver testata) ora fluisce da `silver_prep_carico` a `gold_f_carico`, con `CORRIERE_COD_NAT` + aggancio a `LU_CORRIERE` (surrogate_key_fallback) + entry nel `gold_lad_resolver`.

**Nota — divergenza `gold_late_arriving_handler` [DA RIFATTORIZZARE]**: questo handler (schedulato, gestisce il late-arriving del *fatto*) ricostruisce F_CARICO leggendo direttamente i Silver clean invece di `silver_logistica_curated.carico`, e ha una select esplicita già disallineata dal fact principale: mancano `ART_RADICE_COD`/`ART_VAR_COD`, non esegue i `surrogate_key_fallback` né scrive le colonne `_NAT`. Le colonne imballo + `VAL_COSTO_CARICO` + corriere sono state aggiunte anche qui per non peggiorare, ma andrebbe rifattorizzato per leggere da `silver_prep_carico` come `gold_f_carico`.

---

### 1.2 F_PREP_SPED

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_prep_sped` (48 colonne) |
| **CDT_DW** | `CDT_DW.F_PREP_SPED` (**204 colonne**) |
| **Grain** | 1 riga = riga di prelievo/preparazione (riepilogo × articolo × step); chiavi candidate: `NUM_RIEP`, `SEQ_PREL_PREP`, `NUM_BOLLA_SPED`, `RIGA_BOLLA`, `NUM_ETICH` — da confermare con query univocità |
| **Partizione** | `ANNO_MESE` |
| **Stato** | `IN CORSO` (P1-P4, P7-P8 fatti 2026-07-02; resta P9 quadratura) |

**Allineamento silver+gold (P7-P8, 2026-07-02)**

Applicato alle pipeline esistenti (non riscrittura — la catena WL era già presente):
- **`silver_prep_prep_sped` v4.0**: articolo = `ART_RADICE_COD` + `ART_VAR_LOGIS_COD` (da MSI via OP-12, **niente `ART_COD`**); droppate `ORA_PREL_*`/`ORA_RIEP_*` (regola triple tempo); droppati `VETTORE/AUTISTA/AUTOM_SPED_COD` (costanti/dismessi); **grain-prelievo completo** con `SEQ_PREL_PREP` nei MERGE_KEYS (prima ometteva → ~30k righe collassate).
- **`gold_f_prep_sped`**: aggiunto aggancio `LU_ART_RADICE` (+ `ART_RADICE_COD_NAT`) accanto a PDV/SITO/OPERATORE/CORRIERE.
- **Nota re-run**: schema silver/gold cambiato → droppare `silver.logistica_curated.prep_sped` e `gold.logistica.F_PREP_SPED` prima del re-run (CTAS pulito).

**Quadratura (P9)** — script parametrico pronto: `scripts/quadratura/quadratura_fact.py --fact PREP_SPED --da ... --a ...`. Confronta su `(SITO, data)` con COUNT + SUM(`QTA_PREP`,`VAL_PREP_CES`,`VAL_PREP_VEN`). Data: CDT_DW `GIORNO_BOLLA_SPED_ID` (YYYYMMDD) vs Gold `DATA_BOLLA_SPED` (stessa semantica bolla). Colonne validate via `--discover`. **Esecuzione dopo il re-run del Gold.**

Eventuali colonne business aggiuntive di CDT_DW non ancora portate (promo, tipo_prep/prel/riep, mappa completa, `PES_PREP`, `VAL_INEVASO_PREP_CES`) da valutare dopo la prima quadratura.

> **Script quadratura**: `quadratura_fact.py` (parametrico) sostituisce `quadratura_f_carico.py`. Riusa il
> mapping sito S_LOGISTIX e la lettura Gold via pandas/pyarrow; gestisce sia le date-FK→L_GIORNO (carico) sia
> YYYYMMDD dirette (prep_sped).
> **Aggiornamento ACT_9009 (2026-08-04)** — copre **6 fact**: `CARICO`, `PREP_SPED`, `GIACENZE`, `TRASPORTO`,
> `TURNO_PREP_SITO`, `TRACCIABILITA`. Supporta fact **senza dimensione sito** (GIACENZE) e **senza misure
> comuni** (TRASPORTO, solo COUNT); reidrata le colonne di **partizione** dal path (senza questo fix
> GIACENZE/TURNO davano quadratura vuota); valida la config contro `ALL_TAB_COLUMNS` fermandosi con un
> messaggio chiaro. Per i 4 fact nuovi i nomi colonna **CDT_DW sono ipotesi** (`oracle_confirmed: False`) da
> confermare con `--discover` al primo accesso Oracle.

**Findings P1-P2 (discover + decode)**

- **Fact enorme: 204 colonne** in CDT_DW vs 48 nel nostro Gold. Ma molte delle 204 sono: coppie `*_COD`+`*_ID` (teniamo solo COD, modello natural key), varianti **storicizzate** `*_ST_ID`, e colonne tecniche ODI (`LOAD_ID`, `FIRST_LOAD_ID`, `DATA_ESTRAZIONE_DWH`). Il gap business reale è quindi minore del 204 vs 48 nominale.
- **Costruzione**: NON una vista `V_*` hand-written (come i carichi) ma la procedura **ODI-generated `CDT_DW.SP_LOAD_F_PREP_SPED_ODI`** (in `DOCS/99. SCRIPT/CDT_DW.sql`). Il decode (P2) è quindi più pesante — SQL generato, non leggibile come una vista.
- **Dimensione articolo**: stesso pattern di F_CARICO — `ART_COD`/`ART_ID` obsoleti, `ART_RADICE_ID`/`ART_ST_RADICE_ID`, `ART_VAR_LOGIS_ID`/`ART_ST_VAR_LOGIS_ID` → esporre solo radice + var logistica, droppare obsoleti/storicizzati.
- **Dimensioni ricche**: PDV, promo, operatore prep/sped, autista/automezzo/vettore (presunto + effettivo), area merceologica, tipo prep/prel/riep, mappa (topografia: quadrante/corsia/piano/livello), tipo UDC.
- **Misure**: `QTA_DAPREP`/`QTA_PREP`/`QTA_INEVASO_PREP`, `NUM_IMB_*`, `PES_DAPREP`/`PES_PREP`, `VAL_PREP_CES`/`VAL_PREP_VEN`/`VAL_INEVASO_PREP_CES`, `SEC_PREP_PREL`, tempi (`GIORNO_*_ID` + `ORA_*`: prelievo/riepilogo/spedizione/consegna).
- **Vantaggio**: la catena WL è **già modellata** in silver (`storico_bolle/liste_clean/uniche`, `prep_riepiloghi`, `prep_bolle`, `prep_prep_sped`) → lavoro di allineamento, non ricostruzione.

**Procedura** (playbook §B, task #50-53)

1. ✅ P1: `--discover` (204 col) + gap vs Gold (48). Grain candidato identificato.
2. ▶️ P2: decode `SP_LOAD_F_PREP_SPED_ODI` (CDT_DW.sql) per grain e mapping colonne esatti.
3. P3-P4: gap analysis + classificazione colonne (A/B/C/D/E).
4. P7-P8: fix mirati silver_prep + gold; P9: quadratura parametrica.

**Regole di pruning colonne (P3, 2026-07-02)**

Data principale del fatto: **`GIORNO_BOLLA_SPED_ID`** (num YYYYMMDD). La verifica "costante/null" va fatta **filtrando sul periodo di business** (es. `GIORNO_BOLLA_SPED_ID BETWEEN 20260101 AND 20260630`), NON su un sample grezzo: le righe **dismesse logicamente su Logistix ma ancora fisicamente nel DB** inquinano i distinct (un sample `ROWNUM` le pesca e fa sembrare "popolate" colonne in realtà morte).

- **Escludere (costanti/null sul 2026 — `SELECT DISTINCT` sull'intera lista → 3 righe banali)**: `ART_AGG_MERCL_COD`, `ART_AGG_MERCL_ID`, `PROMO_ID`, `AFFID_TEMPI_CONS_SOCIO_ID`, `AUTISTA_SPED_COD`, `AUTOM_PRESU_SPED_ID`, `AUTOM_SPED_COD`, `AUTOM_SPED_ID`, `VETTORE_SPED_COD`, `VETTORE_SPED_ID`, `MAG_SITO_TRANSITO_FLAG`, `NUM_CONS_PROMO`, `NUM_RIGHE_BOLLA_SPED`, `NUM_ORD_PREP_GOLD`, `ORA_PREV_CONS_SOCIO`, `GIORNO_SPED_ID`, `ORA_SPED`, `GIORNO_CONS_SOCIO_ID`, `ORA_CONS_SOCIO`, `GIORNO_RICEZ_ORD_ID`, `ORA_RICEZ_ORD`, `AFFID_TEMPI_CONS_COD`, `AFFID_TEMPI_CONS_ID`, `NUM_MAG_SITO_TRANSITO_EFFET`, `NUM_MAG_SITO_TRANSITO_VIRT`, `NUM_LISTE_PREP`, `FIRST_LOAD_ID`, `MACRO_AGG_MERCL_COD`, `MACRO_AGG_MERCL_ID`, `NRO_PGR_ETI`, `COD_ORIGINALE`, `PRZ_ADDEBITO`, `COD_MSI_CATENA`, `VALUTA_PREZZI`, `INDI_STAT`, `TRASFERITO_STAT`, `RIGA_RIGENERATA`, `DATA_ESTRAZIONE_DWH`, `TOLL_ORD`, `ORA_INIZIO_CONS`, `ORA_FINE_CONS`, `TOLL_CONS`, `IDCALENDARIO`, `FLAG_DATACONS`, `DATA_PRELIEVO_PREVISTO`, `TIME_PRELIEVO_PREVISTO`, `COD_SOSTITUITO`, `ID_CICLO`, `DATA_LAVORAZIONE`, `DATA_MINIMO_LAVO`, `DATA_MASSIMO_LAVO`, `ECCEDENZA`. *(NB: i valori non-costanti trovati in un sample non filtrato — es. `NUM_ORD_PREP_GOLD`, `DATA_PRELIEVO_PREVISTO` — erano righe storiche dismesse; sul 2026 sono costanti/null → escluse.)*
- **Regola triple tempo**: dove esistono `GIORNO_*_ID` (num YYYYMMDD) + `ORA_*` (num hh24mi) + `DATA_*` (timestamp): **rimuovere le colonne `ORA_*`**. Tenere `GIORNO_*_ID` (+ `DATA_*` per ora; in futuro valutare di droppare il timestamp lasciando solo `GIORNO_*_ID`).
- **`DES_PRODOTTO`**: NON portare sul fatto (attributo descrittivo → dimensione articolo).
- **Articolo**: droppare `ART_COD`/`ART_ID` (obsoleti) e storicizzate `ART_ST_*`; tenere `ART_RADICE_ID` + `ART_VARIANTE_LOGISTICA_ID`.

**Criticità note**

- Grain molto più complesso e fact molto più largo dei carichi; il decode di una proc ODI-generated è oneroso.
- `SP_CHECK_PREP_SPED_NEW` confrontava `F_PREP_SPED` con `LOGISTIX.RIEPILOGHI` (delta storici accettati) → riferimento per la quadratura.
- Sorgente: `storico_bolle` + `storico_liste` (+ `riepiloghi`).

---

### 1.3 F_TRASPORTO

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_trasporto` |
| **CDT_DW** | **famiglia**: `F_TRASP_MTV` + `F_TRASP_TRATTA` + `F_TRASP_TRATTA_BOLLA` (+ `_STEP`) |
| **Grain** | gold = **1 riga per movimento automezzo (MTV)** — grana `F_TRASP_MTV` |
| **Partizione** | `GIORNO_BOLLA_SPED_ID` |
| **Stato** | 🟢 **CERTIFICATO a grana MTV (2026-07-05)** — scope MTV accettato; TRATTA/BOLLA = estensione futura (vedi sotto) |

**Decode A0-A2 (dai PL/SQL reali, 2026-07-05)**

In CDT_DW i trasporti sono una **gerarchia a 3 grane**, non una tabella:
1. **`F_TRASP_MTV`** — movimento automezzo (viaggio/veicolo). Estrazione: `S_TRASP_MTV` ← `V_MTV` (CDT_ESTR.sql ~10729-11174). **← è ciò che il nostro `gold_f_trasporto` modella.**
2. **`F_TRASP_TRATTA`** — tratta/leg di una gita (nodo origine→dest, `NUM_TRATTA`). Estrazione: `V_TRASP_TRATTA_CONS_PROGR` / `V_TRASP_TRATTA_TRANSITO` + `WL1_COSTO_GITA` (`SP_INS_T_TRASP_TRATTA`, `SP_VAL_TRATTA`, CDT_ESTR.sql ~52075-53823). Valore principale: **costo per tratta**.
3. **`F_TRASP_TRATTA_BOLLA`** — bolla per tratta (`SP_INS_T_TRASP_TRATTA_BOLLA`).

**Decisione di scope (F_TRASPORTO = solo grana MTV) — PRESA (2026-07-05):**
- La grana **MTV** copre l'analitica movimento-automezzo (il fabbisogno logistico core) ed è **completa** rispetto a ciò che estraiamo (`T_TRASP_MTV`).
- Le grane **TRATTA / TRATTA_BOLLA** NON sono attualmente sorgenti nel nostro landing (nessun `V_TRASP_TRATTA_*` / `WL1_COSTO_GITA` / nodi estratti) → richiederebbero **nuove catene di estrazione**.
- Il loro valore primario è il **costo di trasporto per tratta**, che è **già fuori scope** (listini corrieri assenti → valorizzazione trasporto rimandata al cliente, vedi fase_5 §Punti aperti).
- ⇒ Diversamente da F_CARICO/F_PREP_SPED (gold accidentalmente troppo semplice vs sorgenti disponibili), qui la semplificazione è **deliberata e coerente con lo scope sorgenti/costi**.
- **Decisione (interna al flusso, non Reply):** per ora ci si ferma alla grana **MTV**; TRATTA/BOLLA verranno aggiunte in seguito quando si importeranno le nuove sorgenti. *(NB: le decisioni sui flussi sono interne al team; Reply è coinvolta solo su anagrafiche, setup e standard condivisi.)*

**Estensione futura (quando si importano le sorgenti TRATTA/BOLLA):** estrarre `V_TRASP_TRATTA_CONS_PROGR`/`TRANSITO` + `WL1_COSTO_GITA` → bronze/silver/gold `F_TRASP_TRATTA[_BOLLA]` + dim nodo/gita; sbloccare costi con i listini corrieri.

**Quadratura MTV (cloud-gated):** `--discover` su `CDT_DW.F_TRASP_MTV`, quadratura per `(SITO, GIORNO_BOLLA_SPED)`.
⚠️ **Solo COUNT** (rilevato con ACT_9009): il nostro `F_TRASPORTO` **non espone `KM` né `COSTO_EUR`** — il Silver
`silver_prep_trasporto` produce nodi/vettore/bolla/`LEAD_TIME_GG`, nessuna quantità o costo (listini corrieri
assenti, scope MTV). `LEAD_TIME_GG` è nostro-only → non confrontabile. Config in `quadratura_fact.py` (`--fact TRASPORTO`).

---

### 1.4 F_TURNO_PREP_SITO

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_turno_prep_sito` |
| **CDT_DW** | `CDT_DW.F_TURNO_PREP_SITO` (tabella **singola**, da `T_TURNO_PREP_SITO_TMP`) |
| **Grain** | gold = (SITO, DATA_PREPARAZ, PREPARATORE, RIEPILOGO_NRO) — allineato al turno prep per sito |
| **Partizione** | — |
| **Stato** | 🟢 **DECODE A0-A2 FATTO (2026-07-05)** — **ALLINEATO** (grana coerente, tabella singola) |

**Decode A0-A2 (2026-07-05):** CDT_DW ha **una sola** `F_TURNO_PREP_SITO` (no famiglia multi-grana). Grana nostra coerente. Nessuna sovra-semplificazione strutturale. Resta la verifica **column-level** (pruning eventuali colonne CDT_DW inutili) via `--discover` live, e la nota grain giornaliero vs mensile (SP_LOAD lavora per mese) — entrambe **cloud-gated**.

**Mapping colonne chiave**

| Gold | CDT_DW | Note |
|---|---|---|
| `SITO_COD` | da verificare | |
| `DATA_TURNO` | FK → `L_GIORNO` | |
| `ORE_LAVORATE` | da verificare | |
| `OPERATORE_COD` | da verificare | |

**Procedura**

1. `--discover` su `CDT_DW.F_TURNO_PREP_SITO`.
2. Quadratura per `(SITO, DATA)`: COUNT turni + misure Gold reali `ORE_LAVORATE`, `ORE_PRODUTTIVE`,
   `NUM_PREPARATI`, `NUM_INEVASI`, `NUM_REFERENZE` (i nomi CDT_DW corrispondenti restano da confermare con
   `--discover`). Config in `quadratura_fact.py` (`--fact TURNO_PREP_SITO`); valutare anche `--per-mese`
   perché `SP_LOAD` lavora per mese.

**Criticità note**

- La procedura Oracle `SP_LOAD_F_TURNO_PREP_SITO` lavora per mese intero, non per giorno. Valutare se il confronto ha senso a grain giornaliero o mensile.
- Verificare se il Gold include i turni parziali (split mese).

---

### 1.5 F_ORDINI

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_ordini` |
| **CDT_DW** | `F_ORD_FORN` (ordini **fornitore** — nostro scope) · `F_ORD_SOCI` (ordini **cliente/socio** — dominio diverso) |
| **Grain** | gold = ordine/carico fornitore (testata) |
| **Partizione** | `ANNO_MESE` |
| **Stato** | 🟢 **DECODE A0-A2 FATTO (2026-07-05)** — scope **fornitore** deliberato |

**Decode A0-A2 (2026-07-05):** in CDT_DW gli ordini sono in **2 fact di domini diversi**: `F_ORD_FORN[_TESTATE]` (ordini a fornitore, inbound — **nostro scope**) e `F_ORD_SOCI` (ordini dei soci/clienti, outbound/commerciale — **fuori scope logistico inbound**). Il nostro `f_ordini` modella gli ordini fornitore. `F_ORD_SOCI` = dominio diverso, **fuori scope** (decisione interna al flusso). Certifica quantità **indiretta** via F_CARICO (`SUM(QTA_ORD_FORN)`), cloud-gated.

---

### 1.6 F_GIACENZE_DAILY

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_giacenze_daily` |
| **CDT_DW** | `CDT_DW.F_STOCK` (`SP_LOAD_F_STOCK`) |
| **Grain** | gold = (DATA_FOTO, ART_COD_INTERNO, MAG_COD) — giacenza giornaliera |
| **Partizione** | `ANNO_MESE` |
| **Stato** | 🟢 **DECODE A0-A2 FATTO (2026-07-05)** — **ALLINEATO** c/gap misura (VAL_STOCK) |

**Decode A0-A2 (2026-07-05):** controparte = `F_STOCK` (singola). Grana giornaliera coerente. Nessuna sovra-semplificazione strutturale. **Gap noto**: `VAL_STOCK_*` = 0 (OP ST-01/02 — sorgente stock valorizzato assente dall'as-is, da identificare). Verifica column-level + valorizzazione = cloud/sorgente-gated.

**Mapping colonne chiave**

| Gold | CDT_DW | Note |
|---|---|---|
| `SITO_COD` | da verificare | |
| `DATA_STOCK` | FK → `L_GIORNO` | |
| ~~`QTA_GIACENZA`~~ | — | **Non esiste nel nostro Gold.** Misure reali: `QTA_PEZZI`, `QTA_UF`, `PREZZO_MEDIO_PONDERATO`. |
| `ART_RADICE_COD` | da verificare | |

**Procedura**

1. `--discover` su `CDT_DW.F_STOCK`.
2. ⚠️ **Grain di confronto: solo `DATA_FOTO`** (rilevato con ACT_9009). Il nostro `F_GIACENZE_DAILY` è per
   **`MAG_COD`**, non per sito: non esiste `SITO_COD` → il confronto `(SITO, DATA, ART_RADICE)` non è
   applicabile. Si quadra per sola data (aggregato su tutti i magazzini) finché non è definita la mappatura
   `MAG_COD ↔ MAG_SITO_COD`. Config in `quadratura_fact.py` (`--fact GIACENZE`).

**Criticità note**

- Le giacenze in locale hanno un problema di ordinamento: `silver_giacenze_aggregata` dipende da `silver_catena_unificata` che in locale può essere vuota (§16 pipeline_mapping). Verificare che il Gold locale sia popolato correttamente prima di certificare.
- In CDT_DW le giacenze potrebbero essere aggregate per articolo commerciale, non per radice.

---

### 1.7 F_MOVIMENTAZIONE_CARRELLISTI

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_movimentazione_carrellisti` (12 col) |
| **CDT_DW** | **famiglia**: `F_MOV_CARR` (movimenti) + `F_OPER_CARR_LAV` (ore lav.) + `F_MOV_ANN_CARR` (rifiutati) |
| **Grain** | gold = **(CARRELLISTA_COD, DATA_PRESENZA, SITO_COD)** — riepilogo giornaliero |
| **Partizione** | — |
| **Stato** | 🟢 **REVISIONATO (2026-07-05)** — aggiunto `NUM_PLT_MOVIMENTATI`; grana per-movimento/rifiutati = OP-MOV-1 |

**Decode A0-A2 (dai PL/SQL reali, 2026-07-05)**

CDT_DW split la movimentazione in **più fact**:
1. **`F_MOV_CARR`** — "Movimentazione Carrellisti", grana **per movimento**; misura `NUM_PLT_MOV_CARR` (pallet movimentati, `dtcrl_doppio_movim=SI`→2). Sorgente: `DETTAGLIO_CARR` (`dtcrl_*`, via `SP_CHECK_F_MOV_CARR`).
2. **`F_OPER_CARR_LAV`** — "Ore Lavorate Carrellisti".
3. **`F_MOV_ANN_CARR`** — "Movimentazioni Rifiutate".

**Il nostro `f_movimentazione_carrellisti`** ha grana **giornaliera** (carrellista×giorno×sito) e **fonde** presenza+attività: `ORE_PRESENZA`, `ORA_LOGIN/LOGOUT`, `NUM_MISSIONI`, `NUM_CARICHI`, `NUM_RIEPILOGHI`, `DURATA_TOT_MIN` (da `sessione_carrellista` + `missione_carrellista`). Copre quindi, a grana più grossa, sia `F_MOV_CARR` (attività) sia `F_OPER_CARR_LAV` (ore).

**Gap vs CDT_DW:**
- **Grana**: giornaliera vs per-movimento → perso il dettaglio del singolo movimento e la misura **`NUM_PLT` (pallet movimentati)**.
- **`F_MOV_ANN_CARR`** (movimenti rifiutati): non modellato.
- ⚠️ **Sorgente DISPONIBILE**: `DETTAGLIO_CARR` è già in bronze (`dettaglio_carr`) → a differenza dei trasporti, il dettaglio è **costruibile**. Questa è quindi una **scelta di modellazione** (interna al flusso), non un blocco sorgente.

**Decisione presa (2026-07-05) — Opzione A (interna al flusso):** mantenuta la grana giornaliera + **aggiunta la misura `NUM_PLT_MOVIMENTATI`** (`gold_f_movimentazione_carrellisti` v3.1: `SUM(2 se DOPPIO_MOVIM='SI' else 1)` per carrellista×giorno×sito, allineata a `F_MOV_CARR.NUM_PLT_MOV_CARR`). Validato: 2026-06-10 → 126 righe, `SUM(NUM_PLT)=3640` ≥ `SUM(NUM_MISSIONI)=3543` (97 doppi movimenti). Sorgente `DOPPIO_MOVIM` già in `silver.missione_carrellista`.

**Sviluppo futuro (OP-MOV-1):** grana per-movimento dedicata (`F_MOV_CARR`) + movimenti annullati (`F_MOV_ANN_CARR`) se emergono requisiti — nessun blocco sorgente.

**Quadratura (cloud-gated):** `--discover` su `F_MOV_CARR`/`F_OPER_CARR_LAV`; confronto `(SITO, GIORNO)` SUM ore, SUM NUM_PLT.

---

### 1.8 F_TRACCIABILITA_LOTTI

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/f_tracciabilita_lotti` |
| **CDT_DW** | `CDT_DW.F_TRACC` (+ `_STEP`, da `T_TRACC_TMP`) |
| **Grain** | gold = (SITO_COD, CARICO_NRO, MSI_COD, DATA_CARICO) — etichetta CE178 |
| **Partizione** | `ANNO_MESE` |
| **Stato** | 🟢 **DECODE A0-A2 FATTO (2026-07-05)** — **ALLINEATO** (grana etichetta coerente) |

**Decode A0-A2 (2026-07-05):** controparte `F_TRACC` (singola + `_STEP` di staging). Grana etichetta CE178 coerente. Nessuna sovra-semplificazione strutturale. Verifica **completezza campi CE178** + column-level via `--discover`, e compliance (V-06) = **cloud/BA-gated**.

**Mapping colonne chiave**

| Gold | CDT_DW | Note |
|---|---|---|
| `SITO_COD` | da verificare | |
| `DATA_CARICO` | FK → `L_GIORNO` | |
| `NRO_ETICHETTA` | da verificare | Chiave naturale etichetta CE178. |

**Procedura**

1. `--discover` su `CDT_DW.F_TRACC`.
2. Quadratura per `(SITO, DATA)`: COUNT etichette (misure Gold disponibili: `NUM_ETICHETTE`, `NUM_SSCC`,
   `NUM_ANNULLATE`, `NUM_TRASFERITE_STAT`). Config in `quadratura_fact.py` (`--fact TRACCIABILITA`).

---

## 2. Dimensioni — logistica

Le dimensioni Gold sono lookup locali costruiti da CDT_DW (via cdtdw extractor) o da sorgenti Logistix.
La certifica per le dimensioni è più semplice: si confrontano le cardinalità e i valori chiave, non le misure.

> **Decode A0-A2 (2026-07-05):** le 5 LU_* sono **lookup 1:1** verso `CDT_DW.LU_*` (nessuna gerarchia/famiglia, nessun rischio di sovra-semplificazione strutturale come nei fact). La certifica è **column-level** (cardinalità, chiavi naturali, eventuale pruning attributi) → **cloud-gated** (confronto vs Oracle). Nessuna riscrittura strutturale attesa.

### 2.1 LU_SITO

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/lu_sito` |
| **CDT_DW** | `CDT_DW.L_SITO` (o `MAG_SITI` in Logistix) |
| **Stato** | `TODO` |

**Procedura**

```sql
-- Oracle
SELECT COUNT(*) FROM CDT_DW.L_SITO WHERE FLAG_ATTIVO = 1;

-- Gold (pandas)
len(df_lu_sito)
```

Confrontare anche i valori di `SITO_COD` / `MAG_SITO_COD` per costruire il **mapping codici** necessario a tutte le fact (punto critico comune a F_CARICO, F_PREP_SPED ecc.).

**Priorità ALTA** — il mapping SITO_COD Gold ↔ MAG_SITO_COD CDT_DW sblocca tutte le quadrature fact.

---

### 2.2 LU_OPERATORE

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/lu_operatore` |
| **CDT_DW** | `CDT_DW.L_OPER_PREP` o simile |
| **Stato** | `TODO` |

**Procedura**: confronto cardinalità + check codici presenti in Gold ma assenti in CDT_DW (= operatori aggiunti dopo il freeze storico).

---

### 2.3 LU_CORRIERE

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/lu_corriere` |
| **CDT_DW** | `CDT_DW.L_VETT` o simile |
| **Stato** | `TODO` |

**Procedura**: confronto cardinalità + valori codice.

---

### 2.4 LU_TOPOGRAFIA

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/lu_topografia` |
| **CDT_DW** | `CDT_DW.L_TOPOGRAFIA` o `TOPOGRAFIA` in Logistix |
| **Stato** | `TODO` |

---

### 2.5 LU_AREA_MERCL_LOGIS

| | |
|---|---|
| **Gold** | `gold_dev_logistica.db/lu_area_mercl_logis` |
| **CDT_DW** | `CDT_DW.L_AREA_MERCL` o simile |
| **Stato** | `TODO` |

---

## 3. Aggregati — logistica_dm

Gli aggregati sono derivati dal Gold. La certifica avviene in due passi:
1. Verificare che il Gold di base sia certificato (vedi §1).
2. Confrontare i totali aggregati con i report MicroStrategy esistenti su CDT_DW (non c'è una tabella CDT_DW diretta, ma i report consumano le stesse fact).

### 3.1 A_INBOUND_MENSILE

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_inbound_mensile` |
| **CDT_DW** | Nessuna tabella diretta — deriva da `F_CARICO` |
| **Stato** | `N/A` (certifica indiretta via F_CARICO) |

**Procedura**: se `F_CARICO` è certificata, questo aggregato è corretto per costruzione. Confrontare con i report MicroStrategy mensili come sanity check.

---

### 3.2 A_OUTBOUND_MENSILE

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_outbound_mensile` |
| **CDT_DW** | Deriva da `F_PREP_SPED` |
| **Stato** | `N/A` (certifica indiretta via F_PREP_SPED) |

---

### 3.3 A_PRODUTTIVITA_MENSILE

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_produttivita_mensile` |
| **CDT_DW** | Deriva da `F_TURNO_PREP_SITO` + `F_PREP_SPED` |
| **Stato** | `N/A` (certifica indiretta) |

---

### 3.4 A_STOCK_MENSILE

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_stock_mensile` |
| **CDT_DW** | Deriva da `F_STOCK` (vista mensile) |
| **Stato** | `N/A` (certifica indiretta via F_GIACENZE_DAILY) |

---

### 3.5 A_GIACENZE_MONTHLY

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_giacenze_monthly` |
| **CDT_DW** | Vista mensile di `F_STOCK` |
| **Stato** | `N/A` (certifica indiretta) |

---

### 3.6 A_TURNO_PREP_SITO

| | |
|---|---|
| **Gold** | `gold_dev_logistica_dm.db/a_turno_prep_sito` |
| **CDT_DW** | Deriva da `F_TURNO_PREP_SITO` |
| **Stato** | `N/A` (certifica indiretta) |

---

## 4. Prerequisiti trasversali

Prima di eseguire qualsiasi quadratura fact è necessario risolvere questi punti una volta sola:

### P-01 — Mapping SITO_COD Gold ↔ MAG_SITO_COD CDT_DW [RISOLTO 2026-07-01]

Il `SITO_COD` nel nostro Gold è il risultato di `normalize_sito` (es. `0005C` → `05`).
`CDT_DW.F_CARICO` usa `MAG_SITO_COD` nel formato originale (`0005C`).

**Soluzione adottata**: la tabella statica `CDT_ESTR.S_LOGISTIX` (colonne `DBLINK_NAME`, `MAG_SITO_COD`, `FLAG_ATTIVO`) è la fonte autoritativa dei 22 siti attivi. Il codice canonico Gold si ricava da `MAG_SITO_COD` con: estrai cifre → `int()` (rimuove zeri iniziali) → zero-pad a 2. Es. `0005C`→`05`, `0035A`→`35`, `0015B`→`15`. Tutti i 22 `MAG_SITO_COD` mappano esattamente sui codici del Gold.

`quadratura_f_carico.py` implementa `build_sito_map()` (legge S_LOGISTIX WHERE FLAG_ATTIVO=1) e rimappa le chiavi CDT_DW prima del confronto. **Pattern riusabile per tutte le altre fact.**

### P-02 — Mapping date CDT_DW (FK surrogate → DATE)

Tutte le fact CDT_DW usano `GIORNO_*_ID` (FK a `L_GIORNO`) invece di colonne DATE native.
Il join `JOIN CDT_DW.L_GIORNO g ON g.GIORNO_ID = f.GIORNO_CARICO_ID` è già implementato in `quadratura_f_carico.py` e può essere riusato come pattern.

### P-03 — Intervallo dati disponibile

La landing area parte dal **2026-06-09**. Tutte le quadrature devono essere eseguite su intervalli coperti dal nostro flusso, non su mesi interi.
Script: usare sempre `--da` / `--a` con date a partire dal 2026-06-09.

### P-04 — Soglia di accettazione

Default: **1%** su COUNT, SUM misure principali per cella `(SITO, DATA)`.
Per le prime quadrature si consiglia di usare **5%** (`--soglia 5.0`) per isolare le differenze strutturali da quelle marginali.

---

## 4-bis. Triage certificazione strutturale (Fase 0 — 2026-07-05)

Verifica se la **certificazione strutturale vs CDT_DW** (decode reale + pruning colonne + riscrittura, fatta su F_CARICO e F_PREP_SPED) sia stata estesa alle fasi successive. **Esito: NO** — i 6 fact sotto sono TODO. Triage per dimensionare il gap (conteggio colonne gold + struttura CDT_DW):

| Fact | Col gold | Struttura CDT_DW | Priorità cert. | Note |
|------|:--------:|------------------|:--------------:|------|
| **F_TRASPORTO** | 31 | **famiglia multi-grana**: F_TRASP_MTV + F_TRASP_TRATTA + F_TRASP_TRATTA_BOLLA (+_STEP) | 🔴 **ALTA** | gold modella solo grana **MTV**; da decidere se servono i livelli TRATTA/BOLLA (possibile forte semplificazione, tipo prep_sped) |
| **F_MOVIMENTAZIONE_CARRELLISTI** | 12 | **famiglia**: F_MOV_CARR + _STEP + F_MOV_ANN_CARR | 🔴 **ALTA** | molto snello (12 col) vs famiglia CDT_DW; verificare grana missione vs step |
| **F_TURNO_PREP_SITO** | 32 | F_TURNO_PREP_SITO (+_STEP) | 🟠 MEDIA | tabella singola; gap probabilmente moderato |
| **F_TRACCIABILITA_LOTTI** | 11 | F_TRACC (+_STEP) | 🟠 MEDIA | pochi campi; verificare completezza CE178 |
| **F_GIACENZE_DAILY** | 15 | giacenza daily | 🟡 BASSA-MEDIA | + ST-01/02 (VAL_STOCK a 0) |
| **F_ORDINI** | 19 | nessuna controparte diretta piena | 🟡 (bloccato) | certifica **indiretta** via F_CARICO |

> I conteggi colonna CDT_DW precisi si ottengono col `--discover` live per-fact (come i 204 di F_PREP_SPED), parte di A1 nella certificazione di ogni fact. Task tracker: #54-60.

**Esito round decode A0-A2 (2026-07-05):** completato per **tutti** i 6 fact + dimensioni.
- **Sovra-semplificazione ACCIDENTALE** (gold troppo semplice vs sorgenti disponibili, → riscrittura): trovata solo su **F_MOVIMENTAZIONE** (grana giornaliera vs per-movimento; manca `NUM_PLT`, sorgente presente) → **revisione pianificata**.
- **Scope DELIBERATO** (grana coerente con sorgenti/costi, → confermato): **F_TRASPORTO** (solo MTV), **F_ORDINI** (solo fornitore, non soci).
- **ALLINEATO** (tabella singola, grana coerente; resta solo pruning column-level cloud-gated): **F_TURNO_PREP_SITO**, **F_TRACCIABILITA_LOTTI**, **F_GIACENZE_DAILY** (+ gap noto VAL_STOCK).
- **Dimensioni LU_***: lookup 1:1, nessun rischio strutturale; certifica column-level cloud-gated.
- **Conclusione:** nessun altro caso "tipo prep_sped" oltre a F_MOVIMENTAZIONE. La verifica di pruning colonne fine e la quadratura dati sono **cloud-gated** (richiedono `--discover`/Oracle).

## 5. Piano di esecuzione suggerito

**Certificazione strutturale (offline, playbook A0-A9)** — ordine per gap decrescente (dal triage 4-bis):
| # | Azione | Task | Priorità |
|---|---|---|---|
| S1 | Cert. **F_TRASPORTO** (decide grana MTV/TRATTA/BOLLA) | #55 | 🔴 Alta |
| S2 | Cert. **F_MOVIMENTAZIONE_CARRELLISTI** | #58 | 🔴 Alta |
| S3 | Cert. **F_TURNO_PREP_SITO** | #54 | 🟠 Media |
| S4 | Cert. **F_TRACCIABILITA_LOTTI** | #59 | 🟠 Media |
| S5 | Cert. **F_GIACENZE_DAILY** | #56 | 🟡 Bassa |
| S6 | Cert. **F_ORDINI** (indiretta) + **dimensioni LU_*** | #57, #60 | 🟡 Bassa |

**Quadratura dati vs Oracle (cloud-gated)** — a valle della certificazione strutturale:
| # | Azione | Dipendenze | Priorità |
|---|---|---|---|
| 1 | Risolvere P-01 (mapping SITO_COD) | — | Alta |
| 2 | Quadratura `F_CARICO` con mapping corretto | P-01 | Alta |
| 3 | `--discover` su `F_PREP_SPED`, `F_TURNO_PREP_SITO`, `F_TRASP_MTV` | — | Media |
| 4 | Quadratura `F_PREP_SPED` | P-01, step 3 | Media |
| 5 | Quadratura `F_TURNO_PREP_SITO` | P-01, step 3 | Media |
| 6 | Quadratura `F_TRASPORTO` | P-01, step 3 | Media |
| 7 | Quadratura dimensioni (LU_SITO, LU_OPERATORE, LU_CORRIERE) | — | Bassa |
| 8 | Quadratura `F_GIACENZE_DAILY` | P-01, verifica giacenze locali | Bassa |
| 9 | Verifica aggregati DM via MicroStrategy | Step 2-6 completati | Bassa |
