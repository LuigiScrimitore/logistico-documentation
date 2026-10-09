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
