# Quadratura F_CARICO — Mappa colonne CDT_DW → Gold (fase 1)

**Data**: 2026-09-25 · **ACT**: [[ACT_9029]] · **OP**: Q-01
**Fonti**: `CDT_DW.F_CARICO` (63 col, `--discover`) vs `gold_dev.logistica.f_carico` (49 col, cloud).

## Sintesi
| | Valore |
|---|---|
| Colonne ODI (`CDT_DW.F_CARICO`) | **63** |
| Colonne Gold (`gold_dev.logistica.f_carico`) | **49** |
| ODI **presenti** in gold (stesso nome) | 26 |
| ODI **rinominate** in gold | 13 |
| ODI **non portate** in gold | 24 |
| Colonne **solo-gold** (tecniche/derivate/NAT) | 10 |

- **Chiavi (grain etichetta)**: `MAG_SITO_COD`+`NUM_DOC_CARICO`+`NUM_ETICH` (ODI) ↔ `SITO_COD`+`NUM_DOC_CARICO`+`NUM_ETICH` (gold) → **corrispondono**.
- **Tutte le misure** sono nel gold (QTA_CARICO, QTA_UF_CARICO, QTA_ORD_FORN, PES_CARICO, VOL_CARICO, VAL_COSTO_CARICO, + NUM_*).
- Il gap 63→49 è fisiologico: l'ODI porta **surrogate ID** e diagnostici `GG_*` non replicati; il gold aggiunge **tecniche/NAT**.

## Mappa ODI → Gold (63 colonne, ordine F_CARICO)
| # | CDT_DW.F_CARICO | Stato | Gold f_carico | Nota |
|--:|---|---|---|---|
| 1 | MAG_SITO_COD | 🔁 rinominata | SITO_COD | **chiave**; MAG_SITO_COD→SITO_COD canonico |
| 2 | MAG_SITO_ID | ⛔ non portata | — | surrogate id |
| 3 | GIORNO_CARICO_ID | 🔁 rinominata | DATA_CARICO | **chiave data**; FK L_GIORNO risolta a DATE |
| 4 | NUM_ETICH | ✅ presente | NUM_ETICH | **chiave** |
| 5 | ORA_CARICO | ✅ presente | ORA_CARICO | |
| 6 | FASCIA_ORA_ID | ✅ presente | FASCIA_ORA_ID | |
| 7 | FASCIA_LAV_SITO_ID | ⛔ non portata | — | |
| 8 | AFFID_TEMPI_FORN_COD | ⛔ non portata | — | |
| 9 | AFFID_TEMPI_FORN_ID | ⛔ non portata | — | surrogate id |
| 10 | FORN_COD | 🔁 rinominata | FORNITORE_COD | |
| 11 | FORN_ID | ⛔ non portata | — | surrogate id |
| 12 | ART_COD | 🔁 rinominata | ART_RADICE_COD (+ART_VAR_LOGIS_COD) | articolo decomposto in radice+variante |
| 13 | ART_ID | ⛔ non portata | — | surrogate id |
| 14 | OPER_VALID_COD | 🔁 rinominata | OPERATORE_COD | |
| 15 | OPER_VALID_ID | ⛔ non portata | — | surrogate id |
| 16 | OPER_RICEV_COD | 🔁 rinominata | RICEVITORE_COD | |
| 17 | OPER_RICEV_ID | ⛔ non portata | — | surrogate id |
| 18 | VETTORE_CARICO_COD | 🔁 rinominata | CORRIERE_COD | |
| 19 | VETTORE_CARICO_ID | ⛔ non portata | — | surrogate id |
| 20 | GIORNO_EMIS_ORD_FORN_ID | 🔁 rinominata | DATA_EMISSIONE_ORD | FK→DATE |
| 21 | GIORNO_PREV_CONS_FORN_ID | 🔁 rinominata | DATA_PREV_CONS_FORN | FK→DATE |
| 22 | GIORNO_BOLLA_FORN_ID | 🔁 rinominata | DATA_BOLLA_FORN | FK→DATE |
| 23 | GIORNO_SCAD_CARICO_ID | 🔁 rinominata | DATA_SCAD_CARICO | FK→DATE |
| 24 | NUM_DOC_CARICO | ✅ presente | NUM_DOC_CARICO | **chiave** |
| 25 | NUM_BOLLA_FORN | ✅ presente | NUM_BOLLA_FORN | |
| 26 | NUM_ORD_FORN | ✅ presente | NUM_ORD_FORN | |
| 27 | QTA_ORD_FORN | ✅ presente | QTA_ORD_FORN | **misura** |
| 28 | NUM_PZ_IMB_ORD_FORN | ✅ presente | NUM_PZ_IMB_ORD_FORN | |
| 29 | NUM_PZ_IMB_EFF_FORN | ✅ presente | NUM_PZ_IMB_EFF_FORN | |
| 30 | NUM_PZ_IMB_SITO | ✅ presente | NUM_PZ_IMB_SITO | |
| 31 | STESSO_IMB_CARICO_FLAG | ✅ presente | STESSO_IMB_CARICO_FLAG | |
| 32 | NUM_IMB_STRATO_PLT_SITO | ✅ presente | NUM_IMB_STRATO_PLT_SITO | |
| 33 | NUM_STRATO_PLT_SITO | ✅ presente | NUM_STRATO_PLT_SITO | |
| 34 | NUM_IMB_ULT_STRATO_SITO | ✅ presente | NUM_IMB_ULT_STRATO_SITO | |
| 35 | NUM_IMB_STRATO_PLT_FORN | ✅ presente | NUM_IMB_STRATO_PLT_FORN | |
| 36 | NUM_STRATO_PLT_FORN | ✅ presente | NUM_STRATO_PLT_FORN | |
| 37 | NUM_IMB_ULT_STRATO_FORN | ✅ presente | NUM_IMB_ULT_STRATO_FORN | |
| 38 | ART_MODL_PES_COD | ✅ presente | ART_MODL_PES_COD | |
| 39 | ART_MODL_PES_ID | ⛔ non portata | — | surrogate id |
| 40 | QTA_UF_CARICO | ✅ presente | QTA_UF_CARICO | **misura** |
| 41 | QTA_CARICO | ✅ presente | QTA_CARICO | **misura** |
| 42 | NUM_IMB_CARICO | ✅ presente | NUM_IMB_CARICO | |
| 43 | NUM_IMB_FORN_CARICO | ✅ presente | NUM_IMB_FORN_CARICO | |
| 44 | NUM_PLT_CARICO | ✅ presente | NUM_PLT_CARICO | |
| 45 | PES_CARICO | ✅ presente | PES_CARICO | **misura** |
| 46 | VOL_CARICO | ✅ presente | VOL_CARICO | **misura** |
| 47 | VAL_COSTO_CARICO | ✅ presente | VAL_COSTO_CARICO | **misura** (OP-CAR-1: spesso NULL, sorgente dismessa) |
| 48 | GG_VITA_RESID_ART_CARICO | ⛔ non portata | — | diagnostico GG_* |
| 49 | GG_PREV_CONS | ⛔ non portata | — | diagnostico GG_* |
| 50 | GG_EFF_CONS | ⛔ non portata | — | diagnostico GG_* |
| 51 | GG_RITARDO_CONS | ⛔ non portata | — | diagnostico GG_* |
| 52 | CARICO_INCOMPLETO_FLAG | ⛔ non portata | — | flag ODI |
| 53 | DATI_STO_CARICO_FLAG | ⛔ non portata | — | flag ODI |
| 54 | LOAD_ID | ⛔ non portata | — | audit ODI |
| 55 | GIORNO_SCAD_STOCK_ID | ⛔ non portata | — | surrogate id |
| 56 | GIORNO_SCAD_CARICO_PREC_ID | ⛔ non portata | — | surrogate id |
| 57 | GG_DIFF_SCAD_ULT_CARICO | ⛔ non portata | — | diagnostico GG_* |
| 58 | GG_DIFF_SCAD_STOCK | ⛔ non portata | — | diagnostico GG_* |
| 59 | GG_DIFF_SCAD_ANAG | ⛔ non portata | — | diagnostico GG_* |
| 60 | ART_VAR_LOGIS_ID | 🔁 rinominata | ART_VAR_LOGIS_COD (+ART_VARIANTE_LOGISTICA_ID) | variante logistica |
| 61 | ART_ST_VAR_LOGIS_ID | ⛔ non portata | — | surrogate id (variante storica) |
| 62 | ART_RADICE_ID | 🔁 rinominata | ART_RADICE_COD | codice radice derivato |
| 63 | ART_ST_RADICE_ID | ⛔ non portata | — | surrogate id (radice storica) |

## Colonne solo-Gold (10) — tecniche / derivate / natural key
| Gold f_carico | Tipo | Nota |
|---|---|---|
| ANNO_MESE | partizione | derivata da DATA_CARICO |
| _silver_ts | tecnica | timestamp elaborazione silver |
| _silver_load_date | tecnica | data di load silver |
| DWH_UPDATED_AT | tecnica | audit gold |
| SITO_COD_NAT | natural key | chiave naturale (modello gold, [[logistico-gold-key-model]]) |
| FORNITORE_COD_NAT | natural key | |
| ART_RADICE_COD_NAT | natural key | |
| OPERATORE_COD_NAT | natural key | |
| RICEVITORE_COD_NAT | natural key | |
| CORRIERE_COD_NAT | natural key | |

## Conclusioni fase 1
- **Chiavi**: ✅ corrispondono (grain etichetta).
- **Colonne**: il gold **non ha tutte** le 63 colonne ODI (mancano 24 surrogate/diagnostici, per scelta) ma **ha tutte le chiavi e le misure**. Le 13 rinominate sono mappate 1:1 (codici canonici / FK-data risolte).
- **Prossimo (fase 3)**: confronto **valori** delle 6 misure per chiave, ODI vs gold cloud (22-24), **senza soglia** (evidenziare tutto).
