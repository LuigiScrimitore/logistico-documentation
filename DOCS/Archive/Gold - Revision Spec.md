# Gold + DataMart — Revision Spec (standard di implementazione)

**Data:** 2026-06-08 · **Autore:** Cloud Data Architect · **Scope:** layer Gold (lookup, fact, aggregati) + KPI
**Riferimenti:** `Silver - Revision Spec.md`, `Lookup Logistico 2.0 - Mappatura LU.xlsx`, `Open Points` (OP-02, OP-06, OP-27)

## 0. Regole di naming (OP-06)
- **Lookup/dimensioni → `LU_*`** (NON `dim_*`).
- **Aggregati → `A_*`** (NON `dm_*`).
- **Fact → `F_*`** (invariato).
- Schemi: `gold_prod.logistica` per `LU_*` logistiche e `F_*`; `gold_prod.logistica_dm` per `A_*`. Le lookup master Retail si leggono dal loro schema (placeholder widget `retail_master_schema`, default `gold_prod.condiviso` in attesa OP-02).

## 1. Principio colonne reali (OP-27)
Il Gold va ricostruito **esclusivamente sulle colonne reali del Silver corretto**. Ogni agente DEVE leggere i notebook Silver sorgente (le loro colonne di output) e usare solo quelle. Niente colonne inventate.

## 2. Lookup master CONDIVISE → DEPRECARE (OP-02)
`gold_dim_articolo`, `gold_dim_fornitore`, `gold_dim_pdv`, `gold_dim_calendario` → **deprecati**: sostituire il corpo con header di deprecazione + `dbutils.notebook.exit("DEPRECATED_OP02")`. Le fact useranno le chiavi naturali e (dove disponibile) faranno lookup in sola lettura alle tabelle Retail `LU_ART_RADICE` / `LU_FORNITORE` / `LU_PDV` / `LU_GIORNO`/`LU_MESE` nello schema `retail_master_schema`. Finché OP-02 non è chiuso, le fact **portano le chiavi naturali** senza richiedere obbligatoriamente la join master (join opzionale/commentata).

## 3. Lookup LOGISTICHE da costruire (`LU_*`, schema gold_prod.logistica)

| Target | Da Silver | Colonne | Chiave |
|--------|-----------|---------|--------|
| `LU_SITO` | silver dim_sito | SITO_COD, (SITO_DESC null), DWH_UPDATED_AT | SITO_COD |
| `LU_OPERATORE` | silver dim_operatore | OPERATORE_COD, SITO_COD, TIPO_OPERATORE, DESCRIZIONE, FLG_ATTIVO, DWH_UPDATED_AT | OPERATORE_COD+SITO_COD+TIPO_OPERATORE |
| `LU_CORRIERE` | silver dim_corriere | CORRIERE_COD, RAGIONE_SOCIALE, INDIRIZZO, CITTA, PROVINCIA, CAP, FLG_ATTIVO, DWH_UPDATED_AT | CORRIERE_COD |
| `LU_TOPOGRAFIA` | silver dim_topografia | CELLA_COD, SITO_COD, MAG_COD, CORSIA, COLONNA, PIANO, COD_CLAS_POSPA, COD_ZONA_MAG, COD_SETTOR_MAG, STATO_POSPA, DWH_UPDATED_AT | CELLA_COD |
| `LU_AREA_MERCL_LOGIS` | bronze.logistica.aree_merceologiche (la silver è confluita nel dim_articolo deprecato) | COD_AREA_MERC=ARM_COD_AREA_MERCEOLOGICA, DES_AREA_MERC=ARM_DES_AREA_MERCEOLOGICA, TIPO_PREPARAZIONE=ARM_TIPO_PREPARAZIONE, DWH_UPDATED_AT | COD_AREA_MERC |

> Nota: `LU_MACRO_AGG_MERCL` (merceologica logistica liv. superiore) — sorgente non disponibile come tabella unitaria nello scope attuale; rinviata (collegata OP-03/04). Non creare ora.
> Naming: si adottano nomi business con prefisso `LU_`. Mapping ai nomi AS-IS (`L_MAG_SITO`, `L_VETTORE`, `L_OPER_*`, `L_MAPPA_*`) documentato nell'Excel lookup; eventuale split/rinomina fine in fase di allineamento Retail.

Pattern lookup: MERGE INTO su chiave (CTAS prima volta) oppure overwrite (sono dimensioni full dal Silver). `DWH_UPDATED_AT = current_timestamp()`.

## 4. Fact da ricostruire (`F_*`, schema gold_prod.logistica)

Widget standard: `env` (dropdown), `run_date` (text). `get_catalog("gold"/"silver", env)`; `retail_master_schema` (text). Pattern: `replaceWhere` su partizione (ANNO_MESE o data) per idempotenza.

### F_CARICO (grain: riga dettaglio carico)
- Silver: `carico_testata` ⋈ `carico_dettaglio` su (SITO_COD, CARICO_NRO, MAG_COD); LEFT JOIN `pesata` su (SITO_COD, CARICO_NRO=CARICO_LOG_NRO) deduplicata.
- Colonne: SITO_COD, CARICO_NRO, MAG_COD, MSI_COD (articolo), FORNITORE_COD, DATA_CARICO, ORDINE_NRO, QTA_ORDINATA, NRO_PZ_CARICATI, QTA_UF_RILEVATA, QTA_PZ_FORNITORE, QTA_UF_FORNITORE, PREZZO_ACQUISTO, SCARTO_QTA (=QTA_ORDINATA-NRO_PZ_CARICATI), FLAG_SCARTO (SCARTO_QTA<>0), PESO_LORDO, PESO_MEDIO, NRO_COLLI (da pesata, coalesce null), ANNO_MESE (da DATA_CARICO), DWH_UPDATED_AT.
- Chiavi naturali per lookup master: MSI_COD→LU_ART_RADICE (via radice/variante), FORNITORE_COD→LU_FORNITORE (join opzionale OP-02). Partizione ANNO_MESE.

### gold_late_arriving_handler
- Allineare a F_CARICO: riprocessa partizioni ANNO_MESE passate da `carico_testata`/`dettaglio` con DATA_CARICO < inizio mese corrente e >= finestra. replaceWhere su ANNO_MESE delle date trovate. Usare colonne reali.

### F_GIACENZE_DAILY (grain: DATA_FOTO+ART_COD_INTERNO+MAG_COD)
- Silver: `giacenza_daily`. Colonne: DATA_FOTO (da _bronze_load_date), ART_COD_INTERNO, ART_RADICE, ART_VAR, MAG_COD, QTA_PEZZI, QTA_UF, QTA_IN_SCADENZA, QTA_PZ_ORD_CLIENTE, QTA_PZ_PREP_CLIENTE, PREZZO_MEDIO_PONDERATO, DATA_MIN_SCADENZA, DWH_UPDATED_AT. replaceWhere su DATA_FOTO. (NB: giacenze per MAG_COD, NON per SITO.) Rimuovere join dim_topografia/articolo non risolvibili.

### F_PREP_SPED (grain: riepilogo per operatore/giorno) — REWORK OP-27
- Silver: `prep_riepilogo` (+ opzionale `timbratura_sessione` per i tempi).
- Misure REALI: TOT_CARTONI, TOT_CARTONI_PREP, TOT_CARTONI_INEVASI, TOT_QUINTALI, TOT_QUINTALI_PREP, NUM_PREPARATI, NUM_INEVASI, NUM_REFERENZE, GABBIE_PREPARATE.
- Tempi: da `prep_riepilogo` ORA_INIZIO_PREP/ORA_FINE_PREP (e DATA_INIZIO_PREP/DATA_FINE_PREP). ORE_LAVORATE = (fine-inizio) in ore.
- **Regola 30 min attrezzaggio (rivista):** Window per (PREPARATORE_COD, DATA_PREPARAZ, SITO_COD) ordinata per ORA_INIZIO_PREP; alla prima sessione del giorno ORE_PRODUTTIVE = max(0, ORE_LAVORATE - 0.5); altrimenti = ORE_LAVORATE. Se i tempi non sono valorizzati → ORE_PRODUTTIVE/ORE_LAVORATE = null e FLAG_TEMPO_ASSENTE=true (documentare, OP-27).
- **Produttività su CARTONI** (non colli): PRODUTTIVITA_CARTONI_ORA = TOT_CARTONI_PREP / ORE_PRODUTTIVE (null se 0). (I "colli" non esistono nei dati reali.)
- Chiavi: SITO_COD, DATA_PREPARAZ, PREPARATORE_COD (→LU_OPERATORE tipo PREPARATORE), RIEPILOGO_NRO, AREA_MERCEOLOGICA_COD, ZONA_MAG_COD, REPARTO_PREP_COD. Partizione DATA_PREPARAZ.

### F_MOVIMENTAZIONE_CARRELLISTI (grain: carrellista/giorno/sito) — REWORK OP-27
- Silver: `sessione_carrellista` (presenza) + `missione_carrellista` (missioni).
- sessione: CARRELLISTA_COD, DATA_PRESENZA, SITO_COD, ORA_LOGIN, ORA_LOGOUT, ORE_PRESENZA. **ORE_PRODUTTIVE non disponibile** → non calcolarla; eventualmente derivare ORE_MISSIONI dalla durata missioni (DATA_EFFETTIVA_INIZIO/FINE) se valorizzate.
- missioni aggregate per (CARRELLISTA_COD, DATA_RICH_ABB→DATA, SITO_COD): NUM_MISSIONI=count, DURATA_TOT_MIN=sum durata (da DATA_EFFETTIVA_INIZIO/FINE). TIPOLOGIA: usare colonne reali (ENTE_RICH_COD/PICKING_NRO/GABBIA_NRO) — niente TIPO_MISSIONE inventato.
- Join sessione ⋈ missioni su (CARRELLISTA_COD, DATA, SITO_COD). Partizione DATA_PRESENZA.

### F_ORDINI (grain: ordine/carico) 
- Silver: `ordini` (da sto_tes_carichi). Colonne: SITO_COD, ORDINE_NRO, CARICO_NRO, MAG_COD, FORNITORE_COD, CORRIERE_COD, DATA_CARICO, DATA_EMISS_ORDINE, DATA_CONFERMA_ORDINE, TIPO_ORDINE, TIPO_CONSEGNA, FLAG_TRASFERITO, ANNO_MESE, DWH_UPDATED_AT. (Stato "non chiuso" è proxy FLAG_TRASFERITO!='S' — documentato.) Niente quantità (non esistono in testata). Partizione su DATA_CARICO o ANNO_MESE.

### F_TRASPORTO (grain: trasporto/bolla) — area non core (flag)
- Silver: `trasporto` (+ `costo_trasporto`). Colonne reali: TRASPORTO_ID, SITO_COD, DATA_BOLLA, BOLLA_NRO, CORRIERE_COD(=VETTORE), AUTISTA_SPED_COD, AUTOMEZZO, STATO, MTV_COD, AZIONE_COD, DATA_AZIONE, DATA_CONSEGNA_PREV, QTA, COSTO_STIMATO_EUR (placeholder), LEAD_TIME_GG (proxy DATA_AZIONE-DATA_BOLLA, documentato). Partizione DATA_BOLLA.

### F_TRACCIABILITA_LOTTI (grain: lotto/articolo) 
- Silver: `tracciabilita_lotto`. Colonne: SITO_COD, CARICO_NRO, MSI_COD, DATA_CARICO, NUM_ETICHETTE, NUM_SSCC, NUM_ANNULLATE, NUM_TRASFERITE_STAT, TASSO_ANNULLAMENTO (=NUM_ANNULLATE/NUM_ETICHETTE), ANNO_MESE, DWH_UPDATED_AT. (Niente QTA_LOTTO: non esiste.) replaceWhere ANNO_MESE.

## 5. Aggregati (`A_*`, schema gold_prod.logistica_dm)
Sorgente = SEMPRE fact Gold (no Silver, no trasformazioni: solo GROUP BY + filtri + funzioni aggregate). replaceWhere su ANNO_MESE.

| Target (rinomina) | Era | Sorgente fact | Grain |
|-------------------|-----|---------------|-------|
| `A_INBOUND_MENSILE` | gold_a_inbound_mensile | F_CARICO | FORNITORE_COD+SITO_COD+ANNO_MESE |
| `A_GIACENZE_MONTHLY` | gold_dm_giacenze_monthly / gold_f_giacenze_monthly | F_GIACENZE_DAILY | ART_RADICE+MAG_COD+ANNO_MESE |
| `A_STOCK_MENSILE` | gold_a_stock_mensile | A_GIACENZE_MONTHLY | ART_RADICE+MAG_COD+ANNO_MESE |
| `A_OUTBOUND_MENSILE` | gold_a_outbound_mensile | F_ORDINI (+F_TRASPORTO) | SITO_COD+CORRIERE_COD+ANNO_MESE |
| `A_PRODUTTIVITA_MENSILE` | gold_a_produttivita_mensile | F_PREP_SPED | SITO_COD+ANNO_MESE (misure su CARTONI/QUINTALI, non colli) |
| `A_TURNO_PREP_SITO` | gold_dm_turno_prep_sito / gold_f_turno_prep_sito | F_PREP_SPED | SITO_COD+DATA_PREPARAZ |

Le misure aggregate devono usare SOLO colonne presenti nelle fact ricostruite (CARTONI/QUINTALI per prep; QTA_PEZZI/QTA_UF per stock; QTA_ORDINATA/NRO_PZ_CARICATI per inbound). `gold_f_giacenze_monthly` (in giacenze/) e `gold_f_turno_prep_sito` (in prep_spedizioni/) vanno riscritti come `A_*` nel datamart (o reindirizzati).

## 6. KPI SQL (`sql/kpi/*.sql`) — allineare al nuovo Gold
Le 10 view vanno riallineate alle colonne/tabelle reali del nuovo Gold: `LU_*` invece di `dim_*`, `A_*` invece di `dm_*`, misure reali (cartoni/quintali, QTA_PEZZI, scarto su dettaglio). Dove un KPI si basava su un dato inesistente (es. colli/ora, ORE_PRODUTTIVE carrellisti, costo trasporto reale), riformulare sul dato reale o aggiungere commento `-- PLACEHOLDER/OP` e degradare gracefully. View in `gold_prod.logistica.kpi_*`.

## 7. Note operative
- Header uniforme Versione 3.0.0 / 2026-06-08.
- Niente colonne inventate: leggere i Silver sorgente per i nomi esatti.
- Chiavi naturali string (no surrogate ID numerici).
- Dove un attributo/lookup master non è disponibile (OP-02), portare la chiave naturale e lasciare la join master opzionale/commentata.
