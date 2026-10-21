# ACT_9029 · Estrattore row-level CDT_DW.F_CARICO + confronto schema/chiavi (quadratura a gradi)

**Status**: in-progress
**Type**: tooling / quadratura
**Origin**: richiesta quadratura F_CARICO gold vs CDT_DW (Q-01)
**Sprint**: 2.4 (KPI & Validazione Carichi) / trasversale quadratura
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Created**: 2026-09-23   **Closed**: —   **Owner**: team (workflows)
**Dipende da**: accesso Oracle CDT_DW (VPN, .env), gold F_CARICO (locale o cloud)
**ADR collegate**: —   **OP collegati**: **Q-01** (quadratura F_CARICO), OP-QDR-1 (finestra vs copertura)

## Contesto
La quadratura F_CARICO (Q-01) è il gate aperto della Fase 2. Gli strumenti esistenti
(`quadratura_fact.py` / `quadratura_f_carico.py`) fanno confronto **KPI aggregati** (COUNT + SUM
misure per `sito×giorno`) tra `CDT_DW.F_CARICO` e il **gold locale** (parquet warehouse). Serve però,
per una quadratura **a gradi**, un passo prima e uno strumento in più:
1. **Fase 1 — struttura**: capire se F_CARICO (CDT_DW) e il nostro Gold hanno **stesse chiavi** e
   **stesso numero di colonne** (grain e copertura campi), non ancora i valori.
2. **Fase 2 — bontà del dato**: confronto **row-level** (non solo aggregati) per key, misure, tipi.

Per la fase 2 serve **estrarre i dati grezzi** di `CDT_DW.F_CARICO` per i giorni disponibili — cosa che
gli strumenti attuali (solo aggregazione in-SQL) non fanno.

## Obiettivo
Uno strumento `scripts/quadratura/extract_f_carico.py` (READ-ONLY, riusa la connessione Oracle di
`quadratura_f_carico.py`) che:
- `--discover`: elenca **colonne + tipi + numero** di `CDT_DW.F_CARICO` e le **chiavi** (PK/unique da
  `ALL_CONSTRAINTS`); se non c'è PK dichiarata, riporta il grain noto (etichetta: SITO+NUM_DOC+NUM_ETICH,
  [[ACT_9001]]).
- `--gold-schema`: elenca **colonne + numero** del Gold F_CARICO (parquet locale) per il confronto fase 1.
- estrazione **row-level per giorni** (`--da/--a`, opz. `--siti`): `SELECT f.*, g.GIORNO_DT` con join
  `CDT_DW.L_GIORNO` (semantica data già validata dai tool di quadratura) → **parquet per-giorno** in
  `LOGISTICO_DATA/quadratura/f_carico/cdtdw/AAAA/MM/GG/`. Parametrizzazione **per giorni** come richiesto.

## Come farla (fasi)
1. **Estrattore** (`extract_f_carico.py`): connessione riusata, SELECT * + GIORNO_DT, loop per-giorno,
   scrittura parquet, `--discover`/`--gold-schema`. READ-ONLY assoluto.
2. **Confronto fase 1 (schema/chiavi)**: `--discover` (Oracle) + `--gold-schema` (Gold) → numero colonne
   per lato, chiavi/grain per lato. Analisi del mapping colonne (semantica: MAG_SITO_COD↔SITO_COD,
   QTA_CARICO↔QTA_UF_RILEVATA, PES_CARICO↔PESO_LORDO, GIORNO_CARICO_ID↔DATA_CARICO) come da
   `quadratura_f_carico.py`.
3. **Confronto fase 2 (bontà dato)**: row-level per key (da valutare: contro gold **locale** o **cloud**
   Databricks — decisione aperta, vedi sotto).

## Punti aperti
- **Target Gold per la fase 2**: gold **locale** (warehouse parquet, presente) o **cloud** (Databricks
  `gold_dev`)? Il locale può essere stantìo; il cloud richiede accesso Databricks. Da decidere.
- Volume: `SELECT *` per-giorno è ok per pochi giorni ("andremo per gradi"); per finestre ampie valutare
  chunking/proiezione.
- OP-QDR-1: quadrare solo sulla **finestra effettivamente coperta** dal Gold, altrimenti falsi "solo in ODI".

## Come verificarla
- `--discover` elenca colonne+chiavi reali di `CDT_DW.F_CARICO` (valida le ipotesi dei tool esistenti).
- estrazione di N giorni → N parquet con le righe attese (COUNT confrontabile coi tool aggregati).
- confronto fase 1: numero colonne e chiavi per lato, con mapping esplicito.

## Esito
- **2026-09-25 · `--discover` OK** (VPN/Oracle): `CDT_DW.F_CARICO` = **63 colonne**, **nessuna PK/Unique**
  dichiarata; grain confermato = `MAG_SITO_COD` + `NUM_DOC_CARICO` + `NUM_ETICH` (etichetta, [[ACT_9001]]).
- **Estrazione 22-23 Sett 2026**: 22 → 25.556 righe, 23 → 28.993 righe (tot **54.549**), parquet per-giorno in
  `LOGISTICO_DATA/quadratura/f_carico/cdtdw/2026/09/{22,23}/`.
- **`--gold-schema`** (parquet locale, snapshot `202608`): **48 colonne** (+ `ANNO_MESE`).
- **Confronto fase 1**: chiavi/grain **corrispondono** (SITO + NUM_DOC + NUM_ETICH); numero colonne **63 (ODI)
  vs 48 (gold)** — l'ODI porta surrogate ID extra (`*_ID`, `LOAD_ID`, `GG_*`), il gold ha colonne tecniche
  (`_silver_ts`, `_silver_load_date`, `DWH_UPDATED_AT`, `*_NAT`). Caveat: gold locale stantìo → per la **fase 2
  (bontà dato)** lo schema/valori vanno presi dal gold **cloud** (dati F_CARICO ora su Databricks).
- Dipendenze: aggiunte `pandas`/`pyarrow` a `py -3.12` (aveva già `oracledb`/`dotenv`).
- **Mappa colonne completa** (ODI 63 → gold 49): `DOCS/main/quadratura_f_carico_mappa_colonne.md`
  (26 presenti + 13 rinominate + 24 non portate; 10 solo-gold tecniche/NAT).
- **Prossimo (fase 3, misure senza soglia)**: confronto valori di QTA_CARICO, QTA_UF_CARICO, QTA_ORD_FORN,
  PES_CARICO, VOL_CARICO, VAL_COSTO_CARICO per chiave (SITO+NUM_DOC+NUM_ETICH), ODI vs gold **cloud** (22-24),
  evidenziando **tutte** le differenze (nessuna soglia). Serve export gold cloud→Volume→download.
- **2026-10-11 · Verifica "come viene popolata" per TUTTE le 49 colonne gold** (richiesta utente su tabella
  annotata DECISIONE): tracciata la derivazione esatta dal codice (`silver_prep_carico.py` v2.0.0,
  `gold_f_carico.py` v4.0.0, `attach_carico_dimensions`/`attach_carico_peso_volume` in `logistica_utils/utils.py`).
  Tabella completa in `quadratura_f_carico_mappa_colonne.md` (sez. "Come viene popolata ogni colonna gold").
  **Esiti chiave**:
  - **Correzioni mappa**: `ART_COD` (riga 12) è **non portata** (obsoleta), non rinominata; la radice/variante
    derivano da `ART_RADICE_ID` (62) / `ART_VAR_LOGIS_ID` (60). (segnalazione utente corretta)
  - **Derivate/ricalcolate (non copiano l'ODI → quadrare per prime)**: `FASCIA_ORA_ID` (da ora),
    `STESSO_IMB_CARICO_FLAG` (ricalcolato), `QTA_CARICO`, `NUM_IMB_FORN_CARICO`, `QTA_ORD_FORN` (OP-CAR-3, COLLI),
    `PES_CARICO`/`VOL_CARICO` (formula ODI da `LU_ART_UNITA_LOGISTICA`), `DATA_SCAD_CARICO` (da pesata, non FK ODI),
    `DATA_PREV_CONS_FORN` (= data conferma ordine).
  - **Popolazione CDT_DW (gg 22, 25.556 righe)**: GG_* tutti 100% → importabili; `NUM_PLT_CARICO` sempre 1
    (coincide con gold); VETTORE/STESSO_IMB/GIORNO_SCAD_* popolati 100%; CARICO_INCOMPLETO_FLAG 0% nel campione.
- **2026-10-11 · Verifica calcolo LEGACY ODI per colonna** (richiesta "come viene calcolata, su CDT_SA o CDT_ESTR"):
  trovati i sorgenti PL/SQL legacy (fuori repo, sul Desktop → memoria [[logistico-legacy-odi-sources-fcarico]]).
  Catena: Logistix → **CDT_ESTR** (`V_CARICO_ORDINARIO`→WL2→WL3→WL4→T_CARICO) → **CDT_SA** (T_CARICO_TMP_P2,
  lookup S_*, E_CARICO) → **CDT_DW** (post-load UPDATE). Dettaglio per-colonna in
  `quadratura_f_carico_mappa_colonne.md` (sez. "Calcolo legacy ODI"). **Correzioni/scoperte**:
  - `CARICO_INCOMPLETO_FLAG` NON è vuota per design → calcolata in CDT_DW da **E_CARICO** (scarti/doppioni);
  - `AFFID_TEMPI_FORN_COD` è una **banda derivata** dal delta giorni DATA_CARICO−DATA_PREV_CONS_FORN (CDT_SA);
  - `QTA_ORD_FORN` legacy = distribuzione CEIL/FLOOR degenere + residuo → **SUM gruppo = MAX_QTA_ORD**: la nostra
    OP-CAR-3 opz.B è equivalente SUM-invariante ✅;
  - `GIORNO_SCAD_STOCK_ID` = scad stock, else scad carico; `GIORNO_SCAD_CARICO_PREC_ID` via SP dedicata;
  - date = **JDN** `TO_DATE(x,'J')`;
  - **mancano sul disco**: def. vista `V_CARICO_ORDINARIO` (FASCIA_ORA_ID, STESSO_IMB_CARICO_FLAG, QTA/PES/VOL) e
    il mapping OWB che calcola i **GG_***.
- **2026-10-11 (cont.) · Estrazione da Oracle live** (VPN, `all_views`/`all_source` via `quadratura_f_carico.connect_oracle`):
  recuperati testo vista `CDT_ESTR.V_CARICO_ORDINARIO` e SP `CDT_DW.SP_INS_GIORNO_SCAD_CARICO_PREC`.
  **Conferme dalla vista** (port fedele): `ORA_CARICO`=LPAD(NVL(ora,0),4,'0'), `FASCIA_ORA_ID`=SUBSTR(..,1,2),
  `STESSO_IMB_CARICO_FLAG`=DECODE(eff_forn−sito,0,1,0), `QTA_CARICO`=nrcolli*pzxcart, `QTA_UF_CARICO`=psp_qta_uf_ril,
  `NUM_IMB_FORN_CARICO`, `NUM_PLT_CARICO`=1, **`DATA_SCAD_CARICO`=p.psp_data_scadenza (pesata)**,
  `DATA_PREV_CONS_FORN`=t.stcar_data_confe_ord → **tutti identici al nostro gold** (annullati i "da quadrare" precedenti
  su DATA_SCAD_CARICO e STESSO_IMB_CARICO_FLAG).
  **GG_\* ricavati empiricamente e confermati 100% (gg22)**: VITA_RESID=SCAD−CARICO, PREV_CONS=PREV_CONS−EMIS,
  EFF_CONS=CARICO−EMIS, RITARDO=CARICO−PREV_CONS (=EFF−PREV) → tutti derivabili dalle date già nel gold.
  **PES/VOL/ART_MODL_PES**: vista=NULL (G5) ma **CDT_DW.F_CARICO li ha valorizzati** (ri-calcolo DW) → il nostro
  ricalcolo da anagrafica è **quadrabile**. **VAL_COSTO_CARICO valorizzato sul 26% (gg22)** → **OP-CAR-1 da riconsiderare**
  (non del tutto dismesso; vista: qta_carico × c.stkultstock).
  Sorgenti estratti in scratchpad (`V_CARICO_ORDINARIO.sql`, `SP_INS_GIORNO_SCAD_CARICO_PREC.sql`).
