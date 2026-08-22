# Analisi AS-IS della logica di estrazione — Package CDT_ESTR

**Data:** 2026-06-08
**Autore:** Cloud Data Architect
**Fonte analizzata:** `DOCS/99. SCRIPT/CDT_ESTR.sql` (5,2 MB, 151.322 righe) + Excel `Tabelle Sorgenti - Logistico 2.0.xlsx`
**Scopo:** verificare, per ciascuna tabella sorgente, se l'estrazione AS-IS è **FULL** o **DELTA**, individuare il meccanismo reale di incrementalità e far emergere i casi particolari (JOIN / trasformazioni in estrazione) che impattano la modellazione di **Landing** e **Bronze**.

> Questa analisi risponde al punto **2.5** del documento *Linee Guida v2.1* (contraddizione FULL vs DELTA sollevata da Reply).

---

## 1. Sintesi esecutiva

Dall'analisi del codice reale emergono **due soli pattern di estrazione**:

| Pattern | Meccanismo verificato | Tabelle |
|---------|----------------------|---------|
| **A — DELTA incrementale a flag** | La sorgente espone su ogni record un flag `<prefisso>_DATA_ESTRAZIONE_DWH`. L'estrazione legge `WHERE <prefisso>_DATA_ESTRAZIONE_DWH = 0` (oppure `IS NULL`); dopo l'estrazione i record vengono marcati. Una procedura di reset rimette il flag a `NULL` per ri-estrarre una finestra (`BETWEEN :DatIni AND :DatFin`). Gli **aggiornamenti** resettano il flag e vengono ri-inviati. | Tutte le tabelle **transazionali / di movimento** Logistix e prep-spedizioni (STAT) |
| **B — FULL** | Nessun flag di estrazione. Lettura completa della tabella (spesso `TRUNCATE` staging + `INSERT … SELECT` senza `WHERE`, o con filtro **statico** di business). | Tutte le **anagrafiche** Logistix e le **giacenze** CND (snapshot giornaliero) |

**Conclusione per il punto 2.5:**
- **DELTA** per le tabelle transazionali (carichi, pesate, tracciabilità, movimenti carrellisti, cartellino, riepiloghi/bolle). → in Bronze: **MERGE INTO** su chiave naturale (gli update vengono ri-inviati nel delta).
- **FULL** per le anagrafiche e per le giacenze CND. → in Bronze: **overwrite/snapshot** (per le giacenze `replaceWhere` su data foto).

La regola pratica è netta: **se la tabella sorgente ha il flag `*_DATA_ESTRAZIONE_DWH` → DELTA; se non lo ha → FULL.** La verifica sul codice mostra **0 occorrenze** del flag sui prefissi delle anagrafiche (STRM_, PREP_, RICV_, SPE_, CORSI_, TGEN_, ARM_, CLPAL_, CRLLS_).

---

## 2. Verifica del meccanismo DELTA a flag

Conteggio delle occorrenze del filtro `<prefisso>_DATA_ESTRAZIONE_DWH = 0` nel package (riga di codice reale):

| Flag (prefisso) | Tabella sorgente | Occorrenze |
|-----------------|------------------|-----------:|
| `DTCRL_DATA_ESTRAZIONE_DWH = 0` | DETTAGLIO_CARR | 62 |
| `CARTE_DATA_ESTRAZIONE_DWH = 0` | CARTELLINO | 62 |
| `ABT_DATA_ESTRAZIONE_DWH = 0` | ABB_TOLTI | 62 |
| `STCAR_DATA_ESTRAZIONE_DWH = 0` | STO_TES_CARICHI | 26 |
| `PSP_DATA_ESTRAZIONE_DWH = 0` | PESATE | 21 |
| `TEBO_DATA_ESTRAZIONE_DWH = 0` | TESTATE_BOLLE | 14 |
| `RPLPR_DATA_ESTRAZIONE_DWH = 0` | STORICO_RIEPILOGHI | 11 |
| `LSO_DATA_ESTRAZIONE_DWH = 0` | STORICO_LISTE | 11 |
| `IMF_DATA_ESTRAZIONE_DWH = 0` | IMBFMOVIM | 9 |
| `CE178_DATA_ESTRAZIONE_DWH = 0` | TRACCIACE178 | 9 |
| `BOL_DATA_ESTRAZIONE_DWH = 0` | STORICO_BOLLE | 3 |

Esempi di codice reale (estratti da CDT_ESTR.sql):

```sql
-- PESATE (delta a flag)
... ' FROM PESATE@' || link || ' WHERE PSP_DATA_ESTRAZIONE_DWH = 0' ...

-- TRACCIACE178 (delta a flag)
... ' FROM TRACCIACE178@' || link || ' WHERE CE178_DATA_ESTRAZIONE_DWH = 0' ...

-- IMBFMOVIM (delta a flag)
... ' FROM IMBFMOVIM@' || link || ' WHERE IMF_DATA_ESTRAZIONE_DWH = 0' ...

-- CARTELLINO (delta a flag)
... ' FROM CARTELLINO@' || link || ' WHERE CARTE_DATA_ESTRAZIONE_DWH = 0' ...

-- Reset finestra di ri-estrazione (es. riepiloghi)
UPDATE ... SET RPLPR_DATA_ESTRAZIONE_DWH = NULL
 WHERE RPLPR_DATA_ESTRAZIONE_DWH BETWEEN :DatIni AND :DatFin
```

---

## 3. Classificazione per tabella (verificata sul codice)

### 3.1 Logistix — Transazionali → **DELTA a flag**

| Tabella sorgente | Prefisso flag | Procedura WL1 | Verdetto | Note tecniche AS-IS |
|------------------|---------------|---------------|----------|---------------------|
| STO_TES_CARICHI | `STCAR_` | SP_INS_WL1_STO_TES_CARICHI_CA | **DELTA** | Driver `WL2_CATENA` costruita da `STO_TES_CARICHI@link WHERE NVL(STCAR_DATA_ESTRAZIONE_DWH,0)=0`; poi re-read con JOIN su CATENA. → *caso particolare §4.1* |
| STO_RIGHE_CARICO | (via CATENA + `SRCAR_`) | SP_INS_WL1_STO_RIGHE_CARICO_CA | **DELTA** | JOIN con `WL2_CATENA` + funzioni `fn_get_radice/fn_get_variante_logistica`. → *caso particolare §4.1 e §4.2* |
| PESATE | `PSP_` | (in SP carichi) | **DELTA** | `WHERE PSP_DATA_ESTRAZIONE_DWH = 0`. Esiste anche una query che lega pesate ai carichi → *caso particolare §4.3* |
| TRACCIACE178 | `CE178_` | (in SP carichi) | **DELTA** | `WHERE CE178_DATA_ESTRAZIONE_DWH = 0`. Tabella critica compliance CE178 |
| IMBFMOVIM | `IMF_` | (in SP carrellisti) | **DELTA** | `WHERE IMF_DATA_ESTRAZIONE_DWH = 0` |
| DETTAGLIO_CARR | `DTCRL_` | (in SP carrellisti) | **DELTA** | `WHERE DTCRL_DATA_ESTRAZIONE_DWH = 0`. **Tabella distinta** da IMBFMOVIM (l'Excel le trattava come alias: errato → §4.4) |
| CARTELLINO | `CARTE_` | SP_INS_WL1_CARTELLINO | **DELTA** | `WHERE CARTE_DATA_ESTRAZIONE_DWH = 0` |
| ABB_TOLTI | `ABT_` | SP_INS_WL1_ABB_TOLTI | **DELTA** | `WHERE ABT_DATA_ESTRAZIONE_DWH = 0` + funzioni articolo |

### 3.2 STAT — Prep spedizioni → **DELTA a flag** (lette `@stat`)

| Tabella sorgente | Prefisso flag | Lettura | Verdetto | Note |
|------------------|---------------|---------|----------|------|
| STORICO_RIEPILOGHI | `RPLPR_` | `FROM storico_riepiloghi@stat` | **DELTA** | **Sorgente = STAT**, non Logistix (correzione → §4.5) |
| TESTATE_BOLLE | `TEBO_` | `FROM testate_bolle@stat` (+ subquery `@link`) | **DELTA** | Letta principalmente da STAT |
| STORICO_BOLLE | `BOL_` | `FROM storico_bolle@stat` | **DELTA** | Sorgente = STAT |
| STORICO_LISTE | `LSO_` | `@stat` | **DELTA** | Tabella di supporto consolidamento prep_sped |

### 3.3 Logistix — Anagrafiche → **FULL**

| Tabella sorgente | Procedura WL1 | Verdetto | Note tecniche AS-IS |
|------------------|---------------|----------|---------------------|
| CARRELLISTI | SP_INS_WL1_CARRELLISTI | **FULL** | `FROM CARRELLISTI@link` (nessun WHERE). + MERGE da PREPARATORI → *caso particolare §4.6* |
| PREPARATORI | SP_INS_WL1_PREPARATORI | **FULL** | Nessun flag delta |
| RICEVITORI | SP_INS_WL1_RICEVITORI | **FULL** | Nessun flag delta |
| SPEDIZIONIERI | SP_INS_WL1_SPEDIZIONIERI | **FULL** | Nessun flag delta |
| STRUTTURA_MAG | SP_INS_WL1_STRUTTURA_MAG | **FULL** | `FROM STRUTTURA_MAG@link` (nessun WHERE) |
| CORSIE | SP_INS_WL1_CORSIE | **FULL** | `TRUNCATE` staging + insert completo |
| TABGEN | SP_INS_WL1_TABGEN | **FULL** | `FROM TABGEN@link` (nessun WHERE) |
| AREE_MERCEOLOGICHE | SP_INS_WL1_AREE_MERCEOLOGICHE | **FULL** (subset) | `WHERE ARM_TIPO_AREA = 1` — **filtro statico di business**, non delta → §4.7 |
| CLASSE_POSTO_PALLET | SP_INS_WL1_CLASSE_POSTO_PALLET | **FULL** | Da vista `V_CLASSE_POSTO_PALLET` |
| CATENA | SP_INS_WL1_CATENA | **FULL** | Anagrafica catene/PDV |

### 3.4 CND (CDT_SOURCE) → **FULL snapshot**

| Tabella sorgente | Staging | Verdetto | Note tecniche AS-IS |
|------------------|---------|----------|---------------------|
| T_STOCK (CNDSTOSTOCK) | WL1_CNDSTOSTOCK | **FULL snapshot** | `TRUNCATE WL1_CNDSTOSTOCK` + `INSERT … FROM CNDSTOSTOCK` (nessun WHERE). Snapshot giornaliero. + funzione `fn_get_radice('GOLD4',STKCINT)` → §4.2 |
| T_PDV | (replica) | **FULL** | Anagrafica PDV (DIM_PDV) |
| T_VETTORI | WL1_VETTORI | **FULL** | Anagrafica vettori (DIM_CORRIERE) |
| T_PREP_SPED | WL1_PREP_SPED | **derivata** | Consolidamento CDT-side (JOIN di più WL1) → §4.8. Non è un'estrazione sorgente diretta |

> **Trasporti (T_VIAGGI_E, T_TRASP_MTV, T_DISTINTE_VIAGGI, ecc.):** l'area trasporti usa una catena di staging propria (`WL1_SPEDIZIONI → WL1_TRASP_MTV`, ecc.) con consolidamenti interni; non rientra nel set core del Bronze attuale. Da analizzare separatamente quando l'area entrerà in scope.

---

## 4. Casi particolari da far emergere (impatto su Landing/Bronze)

Il requisito è: **le tabelle sorgenti devono essere lette unitariamente, senza JOIN con altre tabelle.** L'AS-IS contiene invece diversi JOIN e trasformazioni *in fase di estrazione*. Tutti questi sono **tecniche CDT-side** che NON devono essere replicate nel Landing: il Landing deve contenere il dato **grezzo e unitario** della singola tabella sorgente; i JOIN e le normalizzazioni vanno spostati a valle (Silver/Gold).

### 4.1 — Carichi estratti tramite driver `WL2_CATENA`
`STO_TES_CARICHI` e `STO_RIGHE_CARICO` non vengono lette direttamente con il filtro flag, ma tramite un JOIN con la tabella driver `WL2_CATENA` (la "catena" dei carichi da estrarre), che a sua volta è costruita da `STO_TES_CARICHI@link WHERE NVL(STCAR_DATA_ESTRAZIONE_DWH,0)=0`.
**Impatto landing:** la sorgente deve esporre il **delta dei carichi (flag-based) come tabella unitaria** (testate e righe separate). Il meccanismo CATENA è un'ottimizzazione interna CDT da NON portare nel landing.

### 4.2 — Funzioni di normalizzazione articolo in estrazione
`fn_get_radice(...)` e `fn_get_variante_logistica('LOGISTIX'|'GOLD4', cod_msi)` vengono applicate **durante** l'estrazione (su STO_RIGHE_CARICO, ABB_TOLTI, CNDSTOSTOCK) per derivare `ART_RADICE_COD` / `ART_VAR_LOGIS_COD`.
**Impatto:** sono **trasformazioni**, non estrazione. Nel landing va il codice articolo grezzo (`SRCAR_COD_MSI`, `STKCINT`); la derivazione radice/variante va in **Silver**.

### 4.3 — Pesate legate ai carichi
Oltre al flag `PSP_DATA_ESTRAZIONE_DWH=0`, esiste una query che lega le pesate ai carichi:
`WHERE NVL(STCAR_DATA_ESTRAZIONE_DWH,0)=0 AND stcar_nro_carico IN (SELECT DISTINCT PSP_NRCARLOG FROM pesate@link …)`.
**Impatto:** è un JOIN di servizio per il matching carichi↔pesate. Nel landing, **PESATE** va estratta unitariamente (solo flag delta); il matching con i carichi va in Silver.

### 4.4 — DETTAGLIO_CARR ≠ IMBFMOVIM (sono due tabelle distinte)
L'Excel le trattava come alias ("DETTAGLIO_CARR (alias: IMBFMOVIM)"). In realtà sono **due tabelle sorgente separate**, con due flag distinti (`DTCRL_` e `IMF_`), entrambe DELTA. Alimentano insieme l'area carrellisti.
**Impatto:** in landing/bronze vanno gestite come **due tabelle separate**.

### 4.5 — Prep-spedizioni provengono da STAT, non da Logistix lgax
`STORICO_RIEPILOGHI`, `TESTATE_BOLLE`, `STORICO_BOLLE` sono lette `FROM …@stat`. L'ipotesi precedente ("solo su LOG_LGAX") è **errata**: la sorgente primaria è il sistema **STAT**.
**Impatto:** nel modello landing il sistema sorgente di queste tabelle è **stat**, non logistix. Aggiornare path e workflow di conseguenza.

### 4.6 — WL1_CARRELLISTI = CARRELLISTI ∪ PREPARATORI
La staging `WL1_CARRELLISTI` viene popolata con un `INSERT FROM CARRELLISTI@link` seguito da un `MERGE` da `PREPARATORI@link`.
**Impatto:** è un consolidamento CDT-side. Nel landing **CARRELLISTI e PREPARATORI restano due tabelle separate**; l'unione (per DIM_OPERATORE) avviene in Silver/Gold (già previsto).

### 4.7 — AREE_MERCEOLOGICHE con filtro statico
`WHERE ARM_TIPO_AREA = 1` è un **filtro di business costante** (non un delta). Estrae il sottoinsieme delle aree di tipo 1.
**Impatto:** è un FULL su un subset. Da valutare se replicare il filtro nel landing (la sorgente invia solo tipo 1) o landare tutto e filtrare in Silver. **Da concordare con la sorgente.**

### 4.8 — T_PREP_SPED è una tabella derivata (consolidamento)
`WL1_PREP_SPED` è costruita con un JOIN di `wl1_storico_liste, wl1_storico_riepiloghi, wl1_testate_bolle, wl1_corsie`.
**Impatto:** non è un'estrazione sorgente diretta. Le sorgenti reali sono le singole tabelle STAT (delta-by-flag), che vanno landate separatamente; la consolidazione prep_sped va ricostruita in **Silver**.

### 4.9 — Carichi trasferiti via SWAP
Alcune query di servizio considerano `STCAR_TRASFERITO_SWAP` (carichi trasferiti tra siti via swap). Edge case sui carichi che cambiano sito.
**Impatto:** da chiarire con la sorgente come questi record vengono marcati nel delta (rischio doppio conteggio / mancata cattura).

---

## 5. Implicazioni per il modello Landing / Bronze

### 5.1 Modalità di push attesa per tipo

| Tipo tabella | Modalità AS-IS | File su landing | Pattern Bronze |
|--------------|----------------|-----------------|----------------|
| Transazionali Logistix (carichi, pesate, traccia, movim, cartellino, abbassamenti) | DELTA a flag | Delta giornaliero (record con flag=0, **inclusi aggiornamenti**) | **MERGE INTO** su chiave naturale |
| Prep-spedizioni STAT (riepiloghi, bolle, liste) | DELTA a flag | Delta giornaliero | **MERGE INTO** su chiave naturale |
| Anagrafiche Logistix (carrellisti, preparatori, ricevitori, spedizionieri, struttura_mag, corsie, tabgen, aree_merc, classe_posto_pallet, catena) | FULL | Full giornaliero | **Overwrite** (o MERGE full) |
| Giacenze CND (T_STOCK) | FULL snapshot | Full snapshot giornaliero | **replaceWhere** su data foto |
| Anagrafiche CND (T_PDV, T_VETTORI) | FULL | Full giornaliero | **Overwrite** (o MERGE full) |

### 5.2 Punti da concordare con il sistema sorgente (per il nuovo modello push)

1. **Conferma modalità per tabella**: il delta a flag verrà tradotto in "file delta giornaliero" (record nuovi+modificati)? Le anagrafiche e le giacenze in "file full giornaliero"?
2. **Aggiornamenti (re-send)**: nel meccanismo a flag un record modificato viene ri-estratto. Confermare che il file delta contenga anche gli aggiornamenti → giustifica il MERGE.
3. **Naming/partizionamento file**: il delta è per giorno (YYYY/MM/DD) o possono esserci più file intra-day (con timestamp)? In tal caso Bronze deve leggere **tutti** i file del giorno in ordine di timestamp e fare MERGE. (Coerente con la nostra ipotesi in 2.5, ma da formalizzare.)
4. **Filtro statico AREE_MERCEOLOGICHE** (`ARM_TIPO_AREA=1`): applicato dalla sorgente o landato integralmente?
5. **DETTAGLIO_CARR vs IMBFMOVIM**: confermare che sono due tabelle distinte e che entrambe vengono pushate.
6. **Sorgente prep-spedizioni**: confermare che riepiloghi/bolle arrivano da **STAT** (non Logistix).
7. **Carichi swap** (`STCAR_TRASFERITO_SWAP`): definire come vengono propagati nel delta.

### 5.3 Principio di unitarietà del Landing
Tutti i JOIN e le funzioni di normalizzazione individuati (§4) sono **tecniche di consolidamento CDT-side** e **NON** devono essere replicati nel Landing. Il Landing contiene il dato **grezzo, unitario, per singola tabella sorgente**; le aggregazioni, le unioni (es. operatori) e le normalizzazioni articolo si effettuano in **Silver/Gold**.

---

## 6. Conclusione

La logica AS-IS è coerente e a due regimi:
- **DELTA a flag** (`*_DATA_ESTRAZIONE_DWH = 0`) per tutto ciò che è transazionale/movimento (Logistix + prep-spedizioni STAT);
- **FULL** per anagrafiche (Logistix e CND) e per le giacenze (snapshot CND).

Questo **risolve la contraddizione del punto 2.5**: nel nuovo modello a landing zone la sorgente dovrà pushare un **delta giornaliero** per le transazionali (con re-send degli aggiornamenti → Bronze MERGE) e un **full giornaliero** per anagrafiche e giacenze (→ Bronze overwrite/snapshot). I casi particolari del §4 vanno confermati con i sistemi sorgente prima di consolidare il modello.
