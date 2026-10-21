# Quadratura F_CARICO — Mappa colonne CDT_DW → Gold (fase 1)

**Data**: 2026-09-25 · **ACT**: [[ACT_9029]] · **OP**: Q-01
**Fonti**: `CDT_DW.F_CARICO` (63 col, `--discover`) vs `gold_dev.logistica.f_carico` (49 col, cloud).

## Sintesi
| | Valore |
|---|---|
| Colonne ODI (`CDT_DW.F_CARICO`) | **63** |
| Colonne Gold (`gold_dev.logistica.f_carico`) | **49** |
| ODI **presenti** in gold (stesso nome) | 26 |
| ODI **rinominate** in gold | 12 |
| ODI **non portate** in gold | 25 |
| Colonne **solo-gold** (tecniche/derivate/NAT) | 10 |

> **Correzione 2026-10-11** (verifica codice, [[ACT_9029]]): `ART_COD` (riga 12) è **non portata** (obsoleta), non rinominata. La radice/variante del gold derivano da `ART_RADICE_ID` (riga 62) e `ART_VAR_LOGIS_ID` (riga 60), non da `ART_COD`.

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
| 12 | ART_COD | ⛔ non portata | — | **obsoleto** (header silver: "NIENTE ART_COD"); radice/variante da ART_RADICE_ID/ART_VAR_LOGIS_ID |
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
| 60 | ART_VAR_LOGIS_ID | 🔁 rinominata | ART_VAR_LOGIS_COD (+ART_VARIANTE_LOGISTICA_ID) | **sorgente reale** di ART_VAR_LOGIS_COD (= r.ART_VAR) |
| 61 | ART_ST_VAR_LOGIS_ID | ⛔ non portata | — | surrogate id (variante storica) |
| 62 | ART_RADICE_ID | 🔁 rinominata | ART_RADICE_COD | **sorgente reale** di ART_RADICE_COD (= r.ART_RADICE), non ART_COD |
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

## Come viene popolata ogni colonna gold (49) — verifica codice 2026-10-11
**Fonti codice**: `notebooks/silver/carichi/silver_prep_carico.py` v2.0.0 → `silver.logistica_curated.carico`;
`notebooks/gold/carichi/gold_f_carico.py` v4.0.0 (FASE 3) + `lib/logistica_utils/utils.py`
(`attach_carico_dimensions`, `attach_carico_peso_volume`).
Legenda tipo: **D**=diretta/passthrough · **C**=calcolata/derivata (⚠️ non copia l'ODI) · **L**=lookup anagrafica · **K**=costante · **N**=NULL · **T**=tecnica/_NAT.

| Gold f_carico | Tipo | Come viene popolata (formula/sorgente esatta) |
|---|:--:|---|
| SITO_COD | D | `r.SITO_COD` (dettaglio, canonico) → risolto vs `LU_SITO` (orphan→-1). **chiave** |
| DATA_CARICO | D | `r.DATA_CARICO`. **chiave data** |
| NUM_ETICH | D | `p.ETICHET_NRO` (pesata, driver grain). **chiave** |
| NUM_DOC_CARICO | D | `r.CARICO_NRO`. **chiave** |
| NUM_BOLLA_FORN | D | `r.BOLLA_FORN_NRO` |
| NUM_ORD_FORN | D | `r.ORDINE_NRO` |
| ORA_CARICO | C | `lpad(coalesce(MAX(r.ORA_CARICO),'0'),4,'0')` |
| FASCIA_ORA_ID | C | `substring(ORA_CARICO,1,2)` — ⚠️ **ricalcolata dall'ora**, NON il FASCIA_ORA_ID FK ODI |
| FORNITORE_COD | D | `t.FORNITORE_COD` → risolto vs `LU_FORNITORE` (orphan→-1) |
| ART_RADICE_COD | D | `r.ART_RADICE` (sorgente ODI ART_RADICE_ID) → risolto vs `LU_ART_RADICE` |
| ART_VAR_LOGIS_COD | D | `r.ART_VAR` (sorgente ODI ART_VAR_LOGIS_ID; zero-pad 3 cifre OP-12) |
| OPERATORE_COD | D | `t.OPERATORE_COD` (validante) → `LU_OPERATORE` (NULL→'ND', orphan→-1) |
| RICEVITORE_COD | D | `MIN(r.RICEVITORE_COD)` → `LU_OPERATORE` (NULL→'ND') |
| CORRIERE_COD | D | `t.CORRIERE_COD` (vettore ← STCAR_COD_CORRIERE) → `LU_CORRIERE` |
| DATA_EMISSIONE_ORD | D | `t.DATA_EMISSIONE_ORD` |
| DATA_PREV_CONS_FORN | D | `t.DATA_CONFERMA_ORD` — ⚠️ fonte = **data conferma ordine** |
| DATA_BOLLA_FORN | D | `MAX(r.DATA_BOLLA_FORN)` |
| DATA_SCAD_CARICO | C | `p.DATA_SCADENZA` (**pesata**) — ✅ **identico al legacy** (`V_CARICO_ORDINARIO`: `giorno_scad_carico_id = p.psp_data_scadenza`) |
| NUM_PZ_IMB_ORD_FORN | D | `MAX(r.NUM_PZ_IMB_ORD_FORN)` |
| NUM_PZ_IMB_EFF_FORN | D | `MAX(r.NUM_PZ_IMB_EFF_FORN)` |
| NUM_PZ_IMB_SITO | D | `MAX(r.NUM_PZ_IMB_SITO)` |
| STESSO_IMB_CARICO_FLAG | C | `1 se NUM_PZ_IMB_EFF_FORN==NUM_PZ_IMB_SITO else 0` — ✅ **identico al legacy** (`V_CARICO_ORDINARIO`: `DECODE(eff_forn−sito,0,1,0)`) |
| NUM_IMB_STRATO_PLT_SITO | D | `MAX(r....)` |
| NUM_STRATO_PLT_SITO | D | `MAX(r....)` |
| NUM_IMB_ULT_STRATO_SITO | D | `MAX(r....)` |
| NUM_IMB_STRATO_PLT_FORN | D | `MAX(r....)` |
| NUM_STRATO_PLT_FORN | D | `MAX(r....)` |
| NUM_IMB_ULT_STRATO_FORN | D | `MAX(r....)` |
| QTA_ORD_FORN | C | OP-CAR-3 opz.B: `MAX(QTA_ORDINATA)` sulla 1ª etichetta del gruppo (sito,ordine,radice,var), 0 altrove. ⚠️ unità **COLLI** |
| QTA_UF_CARICO | D | `p.QTA_UF_RILEVATA` |
| QTA_CARICO | C | `p.NRO_COLLI × p.PZ_PER_CARTONE` (pezzi) |
| NUM_IMB_CARICO | D | `p.NRO_COLLI` |
| NUM_IMB_FORN_CARICO | C | `QTA_CARICO / NULLIF(NUM_PZ_IMB_EFF_FORN,0)` |
| NUM_PLT_CARICO | K | `lit(1)` — costante (verificato: CDT_DW sempre 1) |
| VAL_COSTO_CARICO | N | `lit(None)` — NULL (OP-CAR-1, sorgente dismessa) |
| ART_MODL_PES_COD | L | `coalesce(ul.ART_MODL_PES_COD,1)` da `LU_ART_UNITA_LOGISTICA` |
| PES_CARICO | C/L | `se ART_MODL_PES_COD>1 → QTA_UF_CARICO; else → NVL(peso_lordo,0)×QTA_UF_CARICO` (formula ODI) |
| VOL_CARICO | C/L | `QTA_CARICO × alt_pz × lar_pz × pro_pz / 1000` (formula ODI) |
| ART_VARIANTE_LOGISTICA_ID | L | `ul.ART_VARIANTE_LOGISTICA_ID` (FK dim. da anagrafica) |
| SITO_COD_NAT | T | copia grezza pre-risoluzione (LAD resolver) |
| FORNITORE_COD_NAT | T | copia grezza pre-risoluzione |
| ART_RADICE_COD_NAT | T | copia grezza pre-risoluzione |
| OPERATORE_COD_NAT | T | copia grezza pre-risoluzione |
| RICEVITORE_COD_NAT | T | copia grezza pre-risoluzione |
| CORRIERE_COD_NAT | T | copia grezza pre-risoluzione |
| ANNO_MESE | T | `date_format(DATA_CARICO,'yyyyMM')` (partizione) |
| _silver_ts | T | `current_timestamp()` (silver) |
| _silver_load_date | T | `lit(run_date)` (silver) |
| DWH_UPDATED_AT | T | `current_timestamp()` (gold) |

### Popolazione reale CDT_DW (campione giorno 22 Set 2026, 25.556 righe)
Verifica a supporto delle decisioni "da importare / escludere":

| Colonna ODI | non-null | Nota decisione |
|---|--:|---|
| VETTORE_CARICO_COD | 100% | dato pieno (→ CORRIERE_COD / eventuale rinomina VETTORE_COD) |
| STESSO_IMB_CARICO_FLAG | 100% (0:72, 1:25.484) | gold lo **ricalcola** → quadrare i conteggi |
| NUM_PLT_CARICO | 100% (min=max=avg=1) | sempre 1 → coincide con gold (costante) |
| GIORNO_SCAD_CARICO_ID | 100% | vs DATA_SCAD_CARICO da pesata → quadrare |
| GG_PREV_CONS / GG_EFF_CONS / GG_RITARDO_CONS / GG_VITA_RESID_ART_CARICO | 100% | ✅ **importabili** (dato pieno; derivabili anche dalle date gold) |
| **CARICO_INCOMPLETO_FLAG** | **0% nel campione** | ⚠️ NON è vuota per design: calcolata in **CDT_DW post-load** (=1 se la chiave è in E_CARICO/scarti, else 0, NULL se mai toccata). Nel gg 22 nessuno scarto → tutta NULL. Per replicarla serve il meccanismo scarti/DQ, non una copia da F_CARICO |
| DATI_STO_CARICO_FLAG | 100% | flag ODI (attualmente escluso) |
| GIORNO_SCAD_STOCK_ID | 100% | importabile ma è un _ID → risolvere a DATE |
| GIORNO_SCAD_CARICO_PREC_ID | 99.4% | escluso (surrogate) |
| FASCIA_LAV_SITO_ID | 100% | escluso = scelta |
| AFFID_TEMPI_FORN_COD | 100% | escluso = scelta |

## Calcolo legacy ODI — dove nasce ogni colonna (verifica sorgenti 2026-10-11)
**Fonti legacy** (fuori repo, [[logistico-legacy-odi-sources-fcarico]]): `…\F_CARICO F_PESATE\02. ESTRAI CARICHI`
(pipeline CDT_ESTR `V_CARICO_ORDINARIO`→WL2→WL3→WL4→T_CARICO), `errore f carico.txt` (mapping CDT_SA/E_CARICO),
`5. SP_CDT_SA\*SP_LOAD_F_CARICO_ODI.sql` (orchestratori CDT_SA e CDT_DW).

Catena ODI: **Logistix → CDT_ESTR (viste+WLn) → CDT_SA (T_CARICO_TMP_P2, lookup S_*, E_CARICO) → CDT_DW.F_CARICO (post-load UPDATE)**.

| Colonna | Dove è calcolata (legacy) | Formula/logica legacy reale |
|---|---|---|
| MAG_SITO_COD | CDT_ESTR | `FN_GET_MAG_SITO_COD(cod, data)` |
| GIORNO_*_ID (CARICO/EMIS/PREV_CONS/BOLLA/SCAD) | CDT_ESTR | **JDN** → `TO_CHAR(TO_DATE(TRUNC(x),'J'),'YYYYMMDD')` |
| ORA_CARICO / NUM_BOLLA_FORN / OPER_*_COD | CDT_ESTR | `NVL(x,0)` (sentinella 0) |
| FASCIA_ORA_ID | CDT_ESTR (vista) + validata CDT_SA vs `S_FASCIA_ORA` | calcolata nella vista `V_CARICO_ORDINARIO` (def. non reperita) |
| STESSO_IMB_CARICO_FLAG | CDT_ESTR (vista) | calcolata in `V_CARICO_ORDINARIO` (def. non reperita) |
| QTA_UF_CARICO | CDT_ESTR (vista) | `p.psp_qta_uf_ril`. ✅ **identico** al nostro gold |
| QTA_CARICO | CDT_ESTR (vista) | `p.psp_nrcolli * p.psp_pzxcart`. ✅ **identico** |
| NUM_IMB_CARICO / NUM_IMB_FORN_CARICO / NUM_PLT_CARICO | CDT_ESTR (vista) | `psp_nrcolli` / `qta_carico/NVL(eff_forn,0→1)` / `1`. ✅ **identici** |
| ORA_CARICO / FASCIA_ORA_ID | CDT_ESTR (vista) | `LPAD(NVL(ora,0),4,'0')` / `SUBSTR(...,1,2)`. ✅ **identici** al nostro gold |
| STESSO_IMB_CARICO_FLAG | CDT_ESTR (vista) | `DECODE(pz_eff_forn − pz_sito, 0,1, 0)`. ✅ **identico** (non "da quadrare") |
| GIORNO_SCAD_CARICO_ID → DATA_SCAD_CARICO | CDT_ESTR (vista) | `p.psp_data_scadenza` (**pesata**). ✅ **identico** al nostro gold (non "fonte diversa") |
| GIORNO_PREV_CONS_FORN_ID → DATA_PREV_CONS_FORN | CDT_ESTR (vista) | `t.stcar_data_confe_ord` (data conferma ordine). ✅ confermato |
| PES_CARICO / VOL_CARICO / ART_MODL_PES_COD | vista=NULL (G5) → **ri-valorizzati nel mapping DW** | vista: `NULL`; **ma CDT_DW.F_CARICO li ha popolati** (gg22: PES 100% nn/83% >0, VOL 100%/77%, ART_MODL_PES 1..5). Formula G4 (in vista, commentata): PES=`CASE gestione_uf>0 → qta_uf_ril ELSE NVL(pbru,0)*qta_uf_ril`; VOL=`qta_carico*alt*larg*long/1000`. Il nostro gold la **ricostruisce** da `LU_ART_UNITA_LOGISTICA` → **quadrabile** |
| VAL_COSTO_CARICO | CDT_ESTR (vista) + DW | vista: `(psp_nrcolli*psp_pzxcart) * NVL(c.stkultstock,0)` (ultimo costo stock CND). **gg22: valorizzato sul 26% delle righe** (max 16.424) → ⚠️ **OP-CAR-1 da riconsiderare**: non è del tutto dismesso |
| DATI_STO_CARICO_FLAG | CDT_ESTR (vista) | `0` (costante) |
| **QTA_ORD_FORN** | CDT_ESTR (WL4→T_CARICO) | distribuzione: `CEIL/FLOOR` degenere (≡ SUM_QTA_CAR) su ROWID del gruppo (sito,ordine,radice,var) + `RESTO_ATTRIB`=(MAX_QTA_ORD−SUM) sul MIN(ROWID) → **SUM gruppo = MAX_QTA_ORD**. Poi ri-aggiornata in CDT_DW da `sp_upd_carichi_ord_forn`. **La nostra OP-CAR-3 opz.B è l'equivalente pulito SUM-invariante** ✅ |
| **GIORNO_SCAD_STOCK_ID** | CDT_ESTR (WL4→T_CARICO) | `DECODE(FN_CLEAN_DAT_J(stock_scad),0, GIORNO_SCAD_CARICO_ID, stock_scad)` — scadenza stock se presente, else scad carico |
| GIORNO_SCAD_CARICO_PREC_ID | **CDT_DW** post-load | `sp_ins_giorno_scad_carico_prec` |
| **AFFID_TEMPI_FORN_COD** | **CDT_SA** (mapping E_CARICO) | **CASE** sul delta giorni `DATA_CARICO − DATA_PREV_CONS_FORN`: 0→'1', −1→'2', 1→'3', [−5..−2]→'4', [1..5]→'5', ≤−6→'6', ≥6→'7', else '0' (banda affidabilità consegna) |
| VETTORE_CARICO_COD | CDT_SA | presente in `CDT_SA.T_CARICO`, lookup `S_VETTORE_CARICO` |
| **CARICO_INCOMPLETO_FLAG** | **CDT_DW** post-load | `UPDATE`: =1 se chiave (sito+giorno+doc+ordine) ∈ **E_CARICO** (scarti/doppioni), =0 altrimenti, resta NULL se mai toccata |
| **GG_VITA_RESID_ART_CARICO** | mapping OWB→CDT_SA (T_CARICO_TMP_P2) | **= GIORNO_SCAD_CARICO_ID − GIORNO_CARICO_ID** (scadenza − data carico). ✅ confermato 100% sui dati gg 22 |
| **GG_PREV_CONS** | mapping OWB→CDT_SA | **= GIORNO_PREV_CONS_FORN_ID − GIORNO_EMIS_ORD_FORN_ID** (prev. consegna − emissione ord). ✅ 100% |
| **GG_EFF_CONS** | mapping OWB→CDT_SA | **= GIORNO_CARICO_ID − GIORNO_EMIS_ORD_FORN_ID** (data carico − emissione ord). ✅ 100% |
| **GG_RITARDO_CONS** | mapping OWB→CDT_SA | **= GIORNO_CARICO_ID − GIORNO_PREV_CONS_FORN_ID** (= GG_EFF_CONS − GG_PREV_CONS). ✅ 100% |
| GIORNO_SCAD_CARICO_PREC_ID / GG_DIFF_SCAD_ULT_CARICO | CDT_DW `SP_INS_GIORNO_SCAD_CARICO_PREC` | scad del carico precedente (stesso sito+forn+radice+var, giorno<corrente) e relativa differenza |
| ART_RADICE_COD / ART_VAR_LOGIS_COD | CDT_ESTR | `fn_get_radice` / `fn_get_variante_logistica('GOLD4',msi)` in estrazione |
| ART_COD | CDT_ESTR | portato nel legacy (il nostro gold lo **omette**, usa radice+variante) |

**Implicazioni quadratura**:
- `QTA_ORD_FORN`: quadra a livello **gruppo** (SUM = qta ordinata), non per singola etichetta → confrontare per gruppo.
- `AFFID_TEMPI_FORN_COD`: **derivabile** dalle date del gold (banda delta-giorni) → rivedere il "escludere".
- `GIORNO_SCAD_STOCK_ID` e `CARICO_INCOMPLETO_FLAG`: calcolati tardi (stock/scarti) → importabili solo ricostruendo stock-scad e meccanismo scarti.
- `V_CARICO_ORDINARIO` (def.) e mapping GG_* mancano sul disco → per la quadratura di FASCIA_ORA_ID/STESSO_IMB_CARICO_FLAG/GG_* serve o la vista o il confronto diretto dei valori ODI vs gold.

> **Aggiornamento 2026-10-21 ([[ACT_9031]])**: i 4 `GG_*` sono ora **esposti nel gold**
> (`gold_f_carico` v4.1.0, FASE 3c, `datediff` sulle date già presenti) — da validare con run DEV.
> Restano da decidere: rinomina `CORRIERE_COD`→`VETTORE_COD` (impatto 17 file + LAD), `CARICO_INCOMPLETO_FLAG`
> (dal DQ/scarti), `GIORNO_SCAD_STOCK_ID` (serve sorgente stock).

## Conclusioni fase 1
- **Chiavi**: ✅ corrispondono (grain etichetta).
- **Colonne**: il gold **non ha tutte** le 63 colonne ODI (mancano 24 surrogate/diagnostici, per scelta) ma **ha tutte le chiavi e le misure**. Le 13 rinominate sono mappate 1:1 (codici canonici / FK-data risolte).
- **Prossimo (fase 3)**: confronto **valori** delle 6 misure per chiave, ODI vs gold cloud (22-24), **senza soglia** (evidenziare tutto).
