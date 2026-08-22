# Revisione AS-IS → TO-BE — Migrazione CDT_ESTR/CDT_SA verso Databricks Medallion

> **Documento di revisione — FASE 0 (propedeutica agli sviluppi)**
> Stato: bozza per revisione di team. NON ancora tradotto in codice.
> Scopo: capire l'AS-IS del flusso legacy Oracle e definire come ricollocarlo nel
> modello Medallion, applicando le regole di layer concordate.

## 1. Team e metodo

| Ruolo | Responsabilità in questa revisione |
|---|---|
| **Data Architect** | Supervisione, sintesi, definizione regole di layer, verifica coerenza |
| **Cloud Developer Senior** | Pattern di esecuzione (db-link, parametrizzazione sorgente, orchestrazione) |
| **Data Engineer — Carichi** | Analisi catena F_CARICO |
| **Data Engineer — Spedizioni** | Analisi catena T_PREP_SPED |
| **Data Engineer — Trasporti** | Analisi catena T_TRASP_MTV / T_VETTORI |
| **Data Engineer — Stock** | Analisi catena T_STOCK |
| **Functional Expert (CDT_ESTR/CDT_SA)** | Chiarimenti su semantica di business; risponde ai *punti aperti* in coda |

Metodo: analisi statica mirata (grep/sed) degli script `CDT_ESTR.sql`, `CDT_ESTR_VISTE.sql`, `CDT_SA.sql`, `CDT_DW.sql` in `DOCS/99. SCRIPT/`. Tutte le evidenze citano i numeri di riga.

## 2. Regole di layer TO-BE (vincolanti)

| Layer | Regola | Implicazione |
|---|---|---|
| **Bronze** | **1:1 col sorgente** (stesse colonne, stessi record). Solo metadati `_bronze_*` | Nessuna trasformazione, nessun join, nessuna aggregazione |
| **Silver** | Bronze **dopo cleansing**: date Julian→standard, trim, NVL, cast tipi, normalizzazione codici (sito), dedup tecnica | Solo pulizia. **No business logic** |
| **Gold (F_\*)** | Tutte le **logiche di business** (join, aggregazioni, derivazioni) + **aggancio lookup** per recuperare gli ID delle dimensioni | Le fact sono il punto in cui si applicano le regole e si agganciano le dimensioni |
| **Gold_dm (A_\*)** | Tabelle **aggregate** mensili/periodiche dai fact Gold | Solo aggregazione su fact già pronte |

> **Nota architetturale chiave (Data Architect):** il flusso TO-BE **NON segue la stessa sequenza** dell'AS-IS. Nel legacy le fasi di cleansing e di business logic sono **mescolate o invertite** (vedi §4 e §8). La migrazione deve **ri-sequenziare**: estrarre il raw (Bronze), pulire (Silver), poi applicare TUTTA la logica e agganciare le dimensioni (Gold). Questo è il cuore del ridisegno.

## 3. Scoperta trasversale n.1 — Le WL1 NON sono "raw"

Contrariamente all'ipotesi iniziale, le tabelle `WL1_*` **non sono copie 1:1** del sorgente: già al livello di replica contengono business logic. Esempi:

- **`WL1_PESATE`** (CDT_ESTR.sql:68611): nello stesso INSERT di "replica" fa **join + `MAX(...) GROUP BY`** su WL1_STO_RIGHE_CARICO e deriva `DATA_CARICO_RIGHE`. Non è raw.
- **`WL1_CATENA` / `WL1_CATENA_ESTERNI`** (CDT_ESTR.sql:95380/95516): chiamano `fn_get_radice('LOGISTIX',...)` e `fn_get_variante_logistica(...)` — derivazione anagrafica G5 a livello staging.
- **`WL1_STORICO_BOLLE`**: calcola `BOL_DATA_BOLLA_DATE = TO_DATE(TRUNC(BOL_DATA_BOLLA),'J')` (cleansing Julian) già nel base.

**Conseguenza per la migrazione:** il nostro **Bronze** deve leggere le **vere sorgenti raw** a monte delle WL1 (`STO_TES_CARICHI`, `STO_RIGHE_CARICO`, `PESATE`, `CATENA`, `STORICO_LISTE`, ecc.), **non** le WL1. Le elaborazioni che oggi sono nelle WL1 vanno ricollocate: cleansing→Silver, business→Gold.

## 4. Scoperta trasversale n.2 — Cleansing e business mescolati/invertiti

Pattern sistematico in tutte le aree:

1. **Business logic applicata sul sistema sorgente** (Carichi): UPDATE su `STO_TES_CARICHI@link`/`PESATE@link` per escludere incongruenze (CDT_ESTR.sql:68040-68160). In Medallion **non si scrive sul sorgente** → va riprogettato come quarantena DQ in Bronze/Silver.
2. **Cleansing prodotto ma non usato** (Carichi): `DATA_BOLLA_DAT` pulita ma il join pesate↔righe su quella data è **disabilitato** "per incongruenza" (CDT_ESTR.sql:68716, VISTE:880).
3. **Cleansing + business fusi nella stessa espressione**: `fascia_ora_id = SUBSTR(LPAD(NVL(ora,0),4,'0'),1,2)` (VISTE:791); `SEC_PREP_PREL` mescola parsing data e calcolo durata (VISTE:2620-2637).
4. **Conversioni Julian ripetute su 3+ livelli** (Spedizioni): la stessa data convertita/riconvertita in base BOLLE, viste, WL3, T. Cleansing non centralizzato.
5. **Imputazione spacciata per cleansing** (Trasporti): il fill-down del vettore mancante (`UPDATE … SET VETTORE = MAX(VETTORE) … WHERE VETTORE IS NULL`, CDT_ESTR.sql:~11620) è commentato come "valorizzazione nulli" ma è **business logic** (assunzione "una gita = un vettore").
6. **Derivazione anagrafica anticipata nello staging** (Stock): `fn_get_radice`/`fn_get_variante_logistica` in WL1; doppia normalizzazione sito (TABGEN in WL1 + `FN_GET_MAG_SITO_COD` in T_STOCK).

## 5. Scoperta trasversale n.3 — Aspetti tecnici di esecuzione (Cloud Developer)

- **SQL dinamico con db-link runtime**: tutte le repliche WL1 usano `EXECUTE IMMEDIATE 'INSERT … FROM tab@' || link`. Il db-link è parametrico per **sito/istanza**. In Databricks va parametrizzato esplicitamente (un'estrazione per sito).
- **Db-link multipli**: `LOG_LGAX/LGCX/...` (siti Logistix), **`TRACK`** (spedizioni/trasporti/vettori — `REPLICA_TRACK.SP_MAIN`, link chiuso dopo l'uso), `STAT` (riepiloghi), `CDT_SOURCE` (replica T_* tra schemi).
- **Funzioni utility NON presenti negli script analizzati** (package esterno, da reperire): `FN_CLEAN_DAT_D`, `FN_CLEAN_DAT_J`, `FN_CLEAN_DAT_V`, `FN_GET_MAG_SITO_COD`, `fn_get_radice`, `fn_get_variante_logistica`, `FN_GET_OFFSET_DATA_PREP`, `FN_GET_MACRO_AGGR_COD`. **Alcune già replicate** in `logistica_utils` (julian_to_date, normalize_sito); le altre vanno reperite e portate.
- **Doppioni e rami morti**: copie multiple di procedure in package diversi (es. `SP_INS_T_CARICO` a CDT_ESTR.sql:23874 e 25427), versioni `_G4`/`_OLD` commentate, `FN_GET_MAPPA_LOCZ_TIPO_COD` (CDT_ESTR) vs `_2` (CDT_SA). **Va identificata la baseline di produzione** prima di replicare.
- **Dedup non deterministica**: `WL4_CARICO` usa `MIN(ROWID)` (dipende dall'ordine fisico Oracle) → in Databricks sostituire con chiave esplicita + window.

---

## 6. Catene AS-IS per area

### 6.1 Carichi
```
Logistix raw (@LOG_xxxx)
  STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE, TRACCIACE178
   │ replica dinamica (con business già qui: WL1_PESATE join+agg)
   ▼
WL1_STO_TES_CARICHI / WL1_STO_RIGHE_CARICO / WL1_PESATE / WL1_TRACCIACE178
   │ V_CARICO_ORDINARIO (VISTE:786) / V_CARICO_STORICO (VISTE:895)  ← join 4 tab + aggregazioni + derivazioni
   ▼
WL2_CARICO_ORDINARIO ∪ WL2_CARICO_STORICO → WL3_CARICO → WL4_CARICO (dedup MIN(ROWID))
   ▼
T_CARICO (CDT_ESTR) → T_CARICO (CDT_SA, +lookup unità logistica G5, calcolo PES/VOL) → F_CARICO (OWB STEP0/1/2)
```
- **Cleansing**: FN_CLEAN_DAT_J/D, LPAD ora, NVL misure.
- **Business**: aggregazione righe, join testata-righe-pesate-stock, scarti (`stesso_imb_carico_flag`), `qta_carico=psp_nrcolli*psp_pzxcart`, `val_costo_carico`, peso/volume (in CDT_SA), scadenze con `LAG()` (OWB).
- **Chiave G5**: `ART_RADICE_COD + ART_VAR_LOGIS_COD` (sostituisce G4 `srcar_cod_msi`). Coerente con il nostro fix OP-12 (radice = MSI senza ultime 3 cifre).

### 6.2 Spedizioni (Preparazione)
```
Logistix/STAT raw
  STORICO_LISTE, STORICO_BOLLE, STORICO_RIEPILOGHI(STAT), SPEDIZIONI
   ▼
WL1_STORICO_LISTE / WL1_STORICO_BOLLE / WL1_STORICO_RIEPILOGHI / WL1_STORICO_BOLLE_SPED
   │ "UNICHE" = GROUP BY 8 chiavi con COUNT/SUM/MIN/MAX  ← business (dedup+grana)
   ▼
WL1_STORICO_LISTE_UNICHE / WL1_STORICO_BOLLE_UNICHE
   │ V_PREP_SPED_OUTER (VISTE:2690) ← outer join liste↔bolle su 8 chiavi
   ▼
WL2_PREP_SPED → WL3_PREP_SPED (+RIEPILOGHI) → T_PREP_SPED (+BOLLE_SPED, CORSIE, ARTDGENE, AREE)
```
- **Logica "UNICHE" (cuore area)**: collassa N righe-articolo in 1 riga per chiave di prelievo (8 colonne: SITO, GABBIA, ORDINE_NEG, NEGOZIO, MSI, DATA_ORDIN_NEG, SEQUE_PRELIEVO, FLAG_SCARTATO). `COUNT(*)`=num righe, `SUM` su quantità, `MIN` su anagrafici/posizionali, `MAX` su flag/date/prezzi.
- **PRESUNTO vs REALE**: vettore/autista/automezzo *presunti* (da bolle_uniche) vs *effettivi* (da SPEDIZIONI→BOLLE_SPED in T). Doppia anagrafica.
- **Conferma**: il vettore presunto è nativo in `T_PREP_SPED` — coerente con la decisione di far derivare il nostro `F_PREP_SPED` da `T_PREP_SPED` (non dai riepiloghi STAT grezzi).

### 6.3 Trasporti
```
TRACK raw (@TRACK)
  vettori, SPEDIZIONI (REPLICA_TRACK.SP_MAIN, CDT_ESTR.sql:7459)
   ▼
WL1_VETTORI_TRASPO (:143636) / WL1_SPEDIZIONI (:138884)
   ▼
WL1_TRASP_MTV (4 INSERT per AZIONE_COD C/S/RP/RT, :52138+) + WL1_AUTOMEZZI
   │ SP_INS_S_TRASP_MTV (:52473) + fill-down VETTORE/AUTOMEZZO per gita (:~11620)
   ▼
S_TRASP_MTV
   │ V_TRASP_MTV_CONS (transito IS NULL) / V_TRASP_MTV_TRANSITO (IS NOT NULL)
   ▼
T_TRASP_MTV
```
- **CONS vs TRANSITO**: CONS = consegna diretta socio/PDV (`TRASP_TIPO_ID` 2=CEDI→PDV, 3=PDV→PDV); TRANSITO = tratta CEDI→CEDI (tipo 1).
- **Fill-down vettore**: `MAX(VETTORE) … WHERE VETTORE IS NULL … per NUM_GITA` = imputazione attributo → riscrivere come `first_value(... ignore nulls) over (partition by num_gita)`.
- **CDT_SA non elabora**: `SP_INS_T_TRASP_MTV` è replica `@CDT_SOURCE`. Tutta la logica è in CDT_ESTR.

### 6.4 Stock/Giacenze
```
Logistix raw (@link)
  CATENA, CATENA_ESTERNI, STRUTTURA_MAG, CNDSTOSTOCK
   ▼
WL1_CATENA (+fn_get_radice) / WL1_CATENA_ESTERNI / WL1_STRUTTURA_MAG / WL1_CNDSTOSTOCK
   │ WL2_CATENA = WL1_CATENA_ESTERNI UNION WL1_CATENA (:95691)
   ▼
V_STOCK_PICKING (VISTE:3015) / V_STOCK_SCORTE (:3080) ← join catena+agg struttura_mag
   ▼
WL2_STOCK_* → WL3_STOCK_* (arricchimento valori da CNDSTOSTOCK, :49927) → T_STOCK
```
- **Picking vs Scorte**: discriminante `STRM_FLAG_SERVIZIO='SI'` (picking = ubicazioni di prelievo) vs `≠'SI'` (scorte = stoccaggio/riserva).
- **`fn_get_mappa_locz_tipo_cod(serv,hxlxp,numrecs)`**: classifica tipo locazione (01-05: picking/scorta mono/multi pallet/articolo) da flag servizio + capienza pallet + numerosità.
- **Valori stock** (VAL_STOCK_NET/ULT/MED): a 0 nelle viste, arricchiti in WL3 da CNDSTOSTOCK (`STKULTPRZNET/STKULTSTOCK/STKPMP × QTA_UF`).

---

## 7. Mapping TO-BE — ricollocazione nei layer Medallion

| Elaborazione AS-IS | Dove sta oggi | TO-BE (layer) |
|---|---|---|
| Replica raw da sorgente | WL1 (con business mescolata) | **Bronze** 1:1 sulle sorgenti raw vere |
| Conversione date Julian | sparsa (WL1, viste, WL3, T) | **Silver** (julian_to_date, centralizzata) |
| Normalizzazione codice sito | TABGEN in WL1 + FN_GET_MAG_SITO_COD in T | **Silver** (normalize_sito, una volta) |
| TRIM/NVL/cast/DECODE formato | sparsa | **Silver** (regole cleansing standard) |
| Dedup "UNICHE" (GROUP BY 8 chiavi) | WL1_*_UNICHE | **Silver** (elaborazione intermedia) o **Gold** se è grana fact — *da decidere* |
| Derivazione radice/variante G5 | WL1 (fn_get_radice) | **Silver** (già fatto: OP-12 troncamento) |
| Join liste-bolle-riepiloghi | viste V_PREP_SPED + WL2/WL3 | **Gold** (business) |
| Calcoli (scarti, qta, valori, secondi prelievo) | viste + T | **Gold** (business) |
| Fill-down vettore per gita | UPDATE su S_TRASP_MTV | **Silver** o **Gold** (imputazione = business) — *da decidere* |
| Split CONS/TRANSITO, picking/scorte | viste ponte | **Gold** (business) |
| Aggancio dimensioni/lookup ID | T_* + CDT_SA | **Gold** (surrogate_key_fallback + orphan-rate, già pronti) |
| Aggregati mensili A_* | OWB / procedure SA | **Gold_dm** |

**Punto di decisione architetturale (UNICHE):** la deduplica "uniche" produce la grana di prelievo che è propedeutica al join liste-bolle. Va valutato se è *cleansing/normalizzazione di grana* (→ Silver) o *business* (→ Gold). Raccomandazione preliminare del Data Architect: **Silver** (è normalizzazione di grana, deterministica), ma con `MIN/MAX` resi espliciti e validati (vedi punto aperto).

---

## 8. Inversioni di sequenza da correggere (sintesi)

L'AS-IS, per ragioni di performance Oracle, **anticipa business logic nello staging** e **rimanda cleansing/enrichment** a valle. Il TO-BE inverte:

| AS-IS (legacy) | TO-BE (Medallion) |
|---|---|
| Filtro DQ sul sorgente (UPDATE @link) | Bronze ingerisce tutto, quarantena DQ in Silver |
| Business in WL1 (join/agg pesate, radice) | Bronze raw puro; business in Gold |
| Date convertite più volte su livelli diversi | Una conversione in Silver, riusata ovunque |
| Enrichment dimensioni in T (fine catena) | Aggancio lookup in Gold con fallback -1 + orphan-rate |
| Dedup MIN(ROWID) non deterministica | Dedup esplicita per chiave + window in Silver |

---

## 9. Punti aperti per il Functional Expert (da chiarire in revisione)

**Trasversali**
1. Reperire le definizioni di `FN_CLEAN_DAT_D/J/V`, `FN_GET_MAG_SITO_COD`, `fn_get_radice`, `fn_get_variante_logistica`, `FN_GET_OFFSET_DATA_PREP`, `FN_GET_MACRO_AGGR_COD` (package utility esterno).
2. Identificare la **baseline di produzione** tra le copie multiple/`_G4`/`_OLD` delle procedure.
3. Confermare la **lista db-link** per sito e per sistema (LOG_*, TRACK, STAT) e l'accessibilità read-only.

**Carichi**
4. Dove vengono valorizzate `ART_RADICE_COD`/`ART_VAR_LOGIS_COD` in WL1 (UPDATE post-replica? RAC? trigger?).
5. Cut-off hardcoded `STCAR_DATA_CARICO >= 20061201`: parametro di business da replicare?
6. Regola corretta di matching pesate↔righe (il join su data è disabilitato).

**Spedizioni**
7. Semantica `MIN/MAX` nelle UNICHE: legittimo che attributi non-chiave divergano dentro le 8 chiavi? Quale valore deve "vincere"?
8. `SEC_PREP_PREL`: gestione cambio anno (usa DDD); è la definizione ufficiale?
9. `DATA_RIEP_INIZ/FINE = SYSDATE` in WL2: voluto o bug?
10. PRESUNTO vs REALE (vettore/autista/automezzo): quale è autoritativo per il reporting?

**Trasporti**
11. Regola "una gita = un vettore": cosa fare con più vettori non nulli nella stessa gita?
12. Semantica resi RP/RT e correlazione `SP_ID_REF`.

**Stock**
13. Semantica `STRM_FLAG_SERVIZIO` e `STRM_TIPO_STRUTTURA=0`.
14. Lo stesso pallet può comparire in picking E scorte? (UNION non deduplica tra i due flussi).
15. `WL2_CATENA` usa `UNION` (dedup) e non `UNION ALL`: comportamento voluto?
16. Lookup definitivo `ART_MODL_PES_COD` (G5 RAC vs S_ART_RADICE_L).

---

## 9-bis. Risoluzione dei punti aperti (Functional Expert + evidenze script)

> Esito della sessione col Functional Expert. Legenda: ✅ RISOLTO-DA-SCRIPT · 🟡 INTERPRETAZIONE-FUNZIONALE · 🔵 DECISIONE-BUSINESS (conferma cliente).

### Trasversali

**T1 — Funzioni utility: TUTTE trovate in `CDT_ESTR.sql`** ✅ (nessuna mancante). Da portare in `logistica_utils`:

| Funzione | Righe | Logica | Default |
|---|---|---|---|
| `FN_CLEAN_DAT_D` | 147777 | `DATE → NUMBER` YYYYMMDD | 0 |
| `FN_CLEAN_DAT_J` | 147797 | Julian→YYYYMMDD se `1..5373484` | 0 |
| `FN_CLEAN_DAT_V` | 147821 | `str(8)→NUMBER` | **19000101** |
| `FN_GET_MAG_SITO_COD` | 148996 | mappa cod_orig→cod su `WL1_MAG_SITO_STORICO` con validità `DATINI/DATFIN_VALID`; fallback record aperto (`DATFIN=99999999`); eccezione → `'-'||orig` | — |
| `FN_GET_RADICE` | 150451 | LOGISTIX/SWAP/STAT: `SUBSTR(art,0,LEN-3)`; GOLD4: lookup `cndartradice` da ARTDGENE | -1 |
| `FN_GET_VARIANTE_LOGISTICA` | 150892 | LOGISTIX/SWAP/STAT: `SUBSTR(art,LEN-2,LEN)` (ultime 3); GOLD4: `cndartvl` | -1 |
| `FN_GET_OFFSET_DATA_PREP` | 150106 | offset giorni da `WL1_OFFSET_DATA_PREP` per fascia oraria → sposta data prep oltre mezzanotte | data senza offset |
| `FN_GET_MACRO_AGGR_COD` | 148781 | macro-aggregazione: ramo CDR (`TIPO_AGG=9`) o merceologica (`TIPO_AGG=111`) | 0 |
| `FN_CLEAN_COD` | 147762 | **NO-OP** (ritorna input) | — |
| `FN_CLEAN_DES` | 147841 | **NO-OP** (ritorna input) | — |

Nota porting: attenzione ai **default divergenti** (DAT_D/J=0 vs DAT_V=19000101) e al fatto che `FN_GET_RADICE/VARIANTE` ritornano **NUMBER** (la variante "007" diventa 7 → perdita zeri). `FN_CLEAN_COD/DES` no-op: nessuna regola reale.

**T2 — Regola radice/variante CONFERMATA** ✅: il nostro fix OP-12 (`ART_RADICE = MSI[:-3]`, `ART_VAR = ultime 3`) coincide con `FN_GET_RADICE/VARIANTE` per LOGISTIX/SWAP/STAT. 🔵 Per sorgente **GOLD4** la radice NON è troncamento ma lookup su ARTDGENE — verificare se in perimetro.

**T3 — Baseline di produzione** ✅:
- `SP_INS_T_CARICO` LIVE = package **`ESTRAI_CARICO`** (riga 23874, G5, con ART_RADICE/VAR); `ESTRAI_CARICO_G4` (25427) **non chiamato** = legacy.
- `SP_INS_T_STOCK` LIVE = versione **plain** (chiamata da `SP_LOAD_T`, CDT_SA:33151); `_G4` non chiamato.
- `FN_GET_MAPPA_LOCZ_TIPO_COD` (base) usata in viste ESTR; `_2` in CDT_SA — entrambe live ma in **layer diversi**.

**T4 — Db-link** ✅: **9 siti Logistix** principali (`LOG_LCAX, LCCX, LGAX, LGCX, LOCX, LONX, LSCX, LSLX, LEXX`) + sporadici (LBVX, LSSX, LOSX, LGMX). Hub/sistemi: `CDT_BRIDGE`, `CDT_SOURCE`, `CDT_COMM`, **`TRACK`** (trasporti/spedizioni/vettori), `STAT`, `GOLD` (Gold4), `SWAP`, `ORDINI`, `FIDELITY`, `HCA92`, `VISUALCDG`. Chiusura sistematica via `CLOSE_DATABASE_LINK`.

### Carichi
**C4** ✅ `ART_RADICE_COD`/`ART_VAR_LOGIS_COD` calcolate **nell'INSERT di replica** via `fn_get_radice('LOGISTIX',SRCAR_COD_MSI)` (package attivo `REPLICA_CARICHI3`, riga 69842-69843). Non post-UPDATE. 🟡 In Bronze→Silver applicare la derivazione in cleansing.
**C5** ✅ Due soglie complementari: `V_CARICO_ORDINARIO` `>= 20061201` (riga 888, G5+pesate), `V_CARICO_STORICO` `< 20060701` (riga 984, G4 stile). 🔵 **Gap lug-dic 2006** da chiarire; decidere se consolidare storico in logica G5 unica.
**C6** ✅ Match pesate↔righe su **4 chiavi**: carico+bolla+ordine+articolo (`PSP_NRCARLOG/NUMBOL/NCOM/ARTEAN13` ↔ `SRCAR_*`); in vista G5 l'articolo è `ART_RADICE+ART_VAR`. **Data bolla esclusa** (incongruenza, rimossa 2008). 🔵 Confermare univocità chiave 4-col senza data.

### Spedizioni
**S7** ✅🟡 UNICHE = GROUP BY 8 chiavi. Anagrafici/posizionali **costanti per chiave** (MIN puramente tecnico). Date prelievo/prezzi **possono variare**: LISTE prende `MIN(inizio)`+`MIN(fine)`, BOLLE `MAX(date/prezzi)`. ⚠️ **`MIN(DATA_FINE_PRELIEVO)` sospetto bug** (dovrebbe essere MAX). → DQ check `COUNT(DISTINCT)=1` sugli attributi costanti.
**S8** ✅ `SEC_PREP_PREL` usa `DDD` (giorno anno) → **NON cross-year-safe** (durata negativa a Capodanno). → in Silver usare `unix_timestamp(fine)-unix_timestamp(inizio)` + DQ `>=0`. **Non replicare** la formula legacy.
**S9** ✅ `SYSDATE` su DATA_RIEP_INIZ/FINE in WL2 = **placeholder voluto** (righe 37222/37225), **sovrascritto in WL3** da `RPLPR_DATA_INIZ/FINE_PREP` (37864-37869). → in Silver derivare solo da RPLPR.
**S10** ✅ `T_PREP_SPED` porta **entrambe** le triplette: presunto (`*_PRESU_SPED_COD`, da bolle_uniche) e reale (`*_SPED_COD`, da BOLLE_SPED, riga 38112). 🟡 **Dimensione spedizione principale = REALE**, con fallback al presunto + flag `SPED_CONSUNTIVATA`.

### Trasporti
**TR11** ✅ Fill-down vettore/automezzo: `MAX(...) per NUM_GITA WHERE ... IS NULL` (righe 11657-11677). Regola **"una gita = un vettore"**; `MAX` arbitrario se multi-valore; tocca solo i NULL. 🔵 Se ammessi più vettori/gita → DQ `COUNT(DISTINCT)>1`. È business (imputazione), non cleansing.
**TR12** ✅ `QTA_RP` = reso **da PDV** (correlato ad azione `S`); `QTA_RT` = reso **da trasportatore/rientro CEDI** (azione `C`); `SUM` per consegna via `SP_ID_REF`. 🔵 Fallback matching senza sigillo può sovra-aggregare.

### Stock
**ST13** ✅ `STRM_FLAG_SERVIZIO='SI'` = picking (prelievo), `≠'SI'` = scorta. `STRM_TIPO_STRUTTURA=0` isola la struttura standard. 🔵 Confermare dizionario valori tipo>0 esclusi.
**ST14** ✅ T_STOCK = **2 INSERT separati** (picking + scorte) = `UNION ALL` di fatto, predicati **mutuamente esclusivi** → no doppio conteggio. → in 2.0 `UNION ALL`. DQ: una locazione non deve avere flag divergenti.
**ST15** ✅ `WL2_CATENA` = `WL1_CATENA_ESTERNI UNION WL1_CATENA` (dedup tupla intera, riga 95762). 🔵 Conflitto parziale (stessa chiave logica, attributi diversi) → entrambe le righe sopravvivono (rischio gonfiaggio); valutare dedup esplicita per chiave + precedenza.
**ST16** ✅ `ART_MODL_PES_COD` da **`CDT_GOLD5_SA.S_ART_RADICE_L`** (outer join su `ART_RADICE_COD`), default `NVL(...,1)`. 🔵 Doppia fonte storica (`LU_ART_RADICE` EDW "SOSTITUITO" da G5); confermare fonte canonica.

### Anomalie legacy da NON replicare (sintesi per il TO-BE)
1. `SEC_PREP_PREL` formula `DDD` → usare differenza timestamp.
2. `MIN(DATA_FINE_PRELIEVO)` nelle UNICHE → valutare `MAX`.
3. Dedup `MIN(ROWID)` (WL4_CARICO) → chiave esplicita + window.
4. Filtro DQ via `UPDATE` sul sorgente → quarantena DQ in Bronze/Silver.
5. `WL2_CATENA UNION` su tupla intera → dedup per chiave logica con precedenza.

---

## 10. Prossimi passi (post-revisione)

1. **Functional Expert** risponde ai punti aperti §9 (o si pianificano le verifiche su DB).
2. Si **reperiscono le funzioni utility** mancanti e si completano in `logistica_utils`.
3. Si definisce il **catalogo sorgenti raw** (tabella + db-link) per area → input alla FASE 1 (landing).
4. Si procede per area, dalla meno complessa (Trasporti/Stock) alla più complessa (Spedizioni), seguendo le fasi del piano (task #33-#42).
5. Il **Data Architect** valida ogni area su: aderenza alle regole di layer, correttezza del ri-sequenziamento, copertura DQ (orphan-rate), quadratura cardinalità vs legacy.

---

## 11. Catalogo Sorgenti RAW (input alla FASE 1 — Landing)

Le repliche WL1 leggono dalle sorgenti seguenti. **Tipo lettura**: 1:1 (copia pura) / JOIN (da disaccoppiare) / LOOKUP (lookup scalare o funzione di arricchimento). Le `@link` sono per-sito (SQL dinamico, iterare sui 9 db-link LOG_*).

### Carichi
| WL1 (legacy) | Sorgente RAW | Link | Tipo | Filtro legacy | Da ricostruire in Silver |
|---|---|---|---|---|---|
| WL1_STO_TES_CARICHI | `STO_TES_CARICHI` | @link | 1:1 | `DATA_ESTRAZIONE_DWH=0` (CDC) | — |
| WL1_STO_RIGHE_CARICO | `STO_RIGHE_CARICO` (+ semi-join testata) | @link | **JOIN** (semi-join = solo filtro) | flag testata=0 | predicato "esiste testata"; ART_RADICE/VAR via fn |
| WL1_PESATE | `PESATE` (+ join righe aggregate) | @link | **JOIN** | flag=0 | match carico+bolla+ordine+articolo; DATA_CARICO_RIGHE |
| WL1_TRACCIACE178 | `TRACCIACE178` | @link | 1:1 | `DATA_ESTRAZIONE_DWH=0` (CDC) | — |

### Trasporti
| WL1 | Sorgente RAW | Link | Tipo | Filtro | Da ricostruire in Silver |
|---|---|---|---|---|---|
| WL1_VETTORI_TRASPO | `vettori` | **@TRACK** | 1:1 | full | — |
| WL1_VETTORI | `VETTORI` | locale | 1:1 | full | (distinta da vettori@TRACK — vedi dubbio D) |
| WL1_SPEDIZIONI | `SPEDIZIONI` (+ semi-join `ESTRAI_SPEDIZIONI`) | locale | **JOIN** (semi-join coda CDC) | `ESTRAI_SP_ESTRATTO_DWH='I'` | predicato coda estrazione |
| WL1_AUTOMEZZI | `AUTOMEZZI` | locale | 1:1 | full | — (serve per join S_TRASP_MTV) |

### Stock
| WL1 | Sorgente RAW | Link | Tipo | Filtro | Da ricostruire in Silver |
|---|---|---|---|---|---|
| WL1_CATENA | `CATENA` | @link | 1:1 + LOOKUP | nessuno | mag_sito_cod (lookup TABGEN nro_tab=7); ART_RADICE/VAR via fn |
| WL1_CATENA_ESTERNI | `CATENA_ESTERNI` | @link | 1:1 + LOOKUP | nessuno | mag_sito; rimappatura CAES_*→CATE_* |
| WL1_CNDSTOSTOCK | `CNDSTOSTOCK` | locale | 1:1 + LOOKUP | full | ART_RADICE/VAR via fn('GOLD4') = lookup ARTDGENE |
| WL1_STRUTTURA_MAG | `STRUTTURA_MAG` | @link | 1:1 + LOOKUP | nessuno | mag_sito; ART_RADICE/VAR via fn |

### Ausiliarie / lookup
| WL1 | Sorgente RAW | Link | Tipo | Filtro | Note |
|---|---|---|---|---|---|
| WL1_CORSIE | `CORSIE` | @link | 1:1 | nessuno | |
| WL1_AREE_MERCEOLOGICHE | `AREE_MERCEOLOGICHE` | @link | 1:1 | **`ARM_TIPO_AREA=1`** (business) | filtro di business, da mantenere |
| WL1_ARTDGENE | `ARTDGENE` | locale | 1:1 + fn | full | anagrafica articoli |
| WL1_TABGEN | `TABGEN` | @link | 1:1 | nessuno | **chiave**: alimenta mag_sito_cod + OFFSET_DATA_PREP |
| WL1_OFFSET_DATA_PREP | `TABGEN` (nro_tab=3) | @link | 1:1 subset | `NRO_TAB=3` | derivata da TABGEN |
| WL1_MACRO_AGGREGAZIONI_CDR | `ASS_MERCEOLOGICHE`+`MACRO_AGGREGAZIONID`+`MACRO_AGGREGAZIONI`+`CNDPARDGENE` | locale | **JOIN 4 tab** | `PARCTAB=111` | join da disaccoppiare |
| WL1_MAG_SITO_STORICO | *nessuna replica* | — | CONFIG | — | tabella di **configurazione** (mapping sito storico), non raw |

### Sorgenti RAW uniche da aggiungere al Landing (21)
- **@link (per-sito):** STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE, TRACCIACE178, CATENA, CATENA_ESTERNI, STRUTTURA_MAG, CORSIE, AREE_MERCEOLOGICHE, TABGEN
- **@TRACK:** vettori
- **locali (schema CDT_ESTR):** AUTOMEZZI, SPEDIZIONI, ESTRAI_SPEDIZIONI, VETTORI, CNDSTOSTOCK, ARTDGENE, ASS_MERCEOLOGICHE, MACRO_AGGREGAZIONID, MACRO_AGGREGAZIONI, CNDPARDGENE

### Join da disaccoppiare (oggi in replica → spostare in Silver/Gold)
1. STO_RIGHE_CARICO × STO_TES_CARICHI (semi-join filtro)
2. PESATE × righe carico aggregate (match 4 chiavi)
3. SPEDIZIONI × ESTRAI_SPEDIZIONI (semi-join coda CDC)
4. MACRO_AGGREGAZIONI_CDR (join 4 tabelle)

### Casistiche di dubbio — DECISIONI PRESE (Data Architect, validate dal committente)
- **A — Filtro CDC `*_DATA_ESTRAZIONE_DWH`** → ✅ **DECISO: Full + finestra data (lookback)**. Il Bronze ignora il flag CDC (che richiederebbe UPDATE sul sorgente, vietato) e applica solo una finestra temporale sulla data di business per le transazionali. L'incrementalità vera è gestita a valle nel framework Delta (MERGE). Coerente con il landing simulator attuale.
- **B — `mag_sito_cod` + ART_RADICE/VAR non native** → ✅ **DECISO: Bronze raw puro, derivate in Silver**. Bronze = sorgente 1:1 senza colonne derivate. `mag_sito_cod` ricostruito in Silver via lookup TABGEN; ART_RADICE/VAR via troncamento (LOGISTIX) o lookup ARTDGENE (GOLD4). Il sito di estrazione resta solo come **metadato tecnico** `_sito_estrazione` (dal db-link), non come dato di business.
- **C — ART_RADICE/VAR** → assorbito in B (derivate in Silver).
- **D — `VETTORI` (locale) vs `vettori@TRACK`** → ✅ **DECISO: includere entrambe** come Bronze distinti; scelta della fonte autoritativa in Silver/Gold col functional expert.
- **E — 5 varianti INSERT WL1_SPEDIZIONI** → 🔵 da identificare la procedura attiva per sito in FASE 1 (Data Engineer Trasporti + functional expert).

---

*Documento prodotto in FASE 0. Le evidenze (numeri di riga) si riferiscono ai file in `DOCS/99. SCRIPT/`. Da rivedere collegialmente prima di procedere con le modifiche al codice.*
