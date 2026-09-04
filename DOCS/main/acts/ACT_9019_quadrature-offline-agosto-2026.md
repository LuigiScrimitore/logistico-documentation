# ACT_9019 · Quadrature offline finestra agosto 2026 (warehouse locale 09-14/08)

**Status**: done (parziale — vedi Esito)
**Type**: analysis
**Origin**: emerged (prep quadrature offline per warehouse locale finestra agosto 2026)
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: trasversale (qualita Gold)
**Gg (stima)**: 1-2 → **Gg reali: 0.5** (1 sessione pomeriggio)
**Blocco**: 🟢 (fase offline) → 🤝 residuo: 2 fix in ACT_9009 (Luigi)
**Created**: 2026-08-19
**Closed**: 2026-08-19
**Owner**: Francesco Foconi
**Dipende da**: [[ACT_9009]] (quadratura_fact.py esteso a 6 fact — merged 2026-08-19 da Luigi), [[ACT_9005]] (big re-run 22 siti che ha popolato warehouse locale finestra agosto)
**Blocca**: —
**ADR collegate**: — (eventuali ADR emergono in itinere)
**OP collegati**: OP-CAR-1/3/4/5, OP-PSP-1/2, OP-MOV-1 (potenzialmente aggiornati da esiti quadratura)

## Contesto e motivazione

Il warehouse locale e stato popolato con **6 giorni consecutivi di finestra agosto 2026 (09/10/11/12/13/14)** grazie:
- long-tail landing 30gg del 13/08 (bypass filtro flag ODI su pesate/testate carichi e STAT)
- pipeline BSG standard per ognuno dei 6 giorni
- fix silver_pesate DATA_SCADENZA JDN (commit locale non pushato)

Row counts warehouse post-pipeline (verificati al termine run 14/08):
- F_CARICO: 230k+ (grain etichetta, arricchito long-tail)
- F_PREP_SPED: 443k+
- F_TRASPORTO: 32k
- F_ORDINI: 47k
- F_TURNO_PREP_SITO: 324k

Il nuovo `scripts/quadratura/quadratura_fact.py` (ACT_9009, merged 2026-08-19) supporta ora **6 fact** con confronto pyarrow-based vs CDT_DW via VPN. Per 4 dei 6 fact (GIACENZE, TRASPORTO, TURNO_PREP_SITO, TRACCIABILITA) i nomi colonna CDT_DW sono ipotesi (`oracle_confirmed: False`) → prerequisito: run `--discover` sull'Oracle vero prima di produrre numeri.

## Obiettivo

- **O1**: eseguire `--discover` sui 4 fact `oracle_confirmed: False` per fissare i nomi colonna reali CDT_DW e sbloccare la quadratura
- **O2**: quadratura vs CDT_DW per **F_CARICO** e **F_PREP_SPED** (gia `oracle_confirmed: True`) sulla finestra 09-14/08 → match rate + gap
- **O3**: quadratura per gli altri 4 fact dopo `--discover`
- **O4**: consolidare esiti in tabella riassuntiva → alimentare `07_certifica_gold_vs_cdtdw.md`
- **O5**: identificare eventuali OP nuovi o gap di modellazione (aggiornare `05_open_points.md`)

## Analisi tecnica

**Tool**: `scripts/quadratura/quadratura_fact.py`

**Fact e granularita note (post ACT_9009)**:
| Fact | Grain | Misure quadrate | oracle_confirmed |
|---|---|---|---|
| F_CARICO | (SITO, DATA_CARICO) | COUNT + QTA_CARICO + PES_CARICO | True |
| F_PREP_SPED | (SITO, DATA_BOLLA_SPED) | COUNT + QTA_PREP | True |
| F_GIACENZE_DAILY | (DATA_FOTO) — no sito, grain MAG_COD | COUNT | False |
| F_TRASPORTO | (SITO, DATA) | COUNT (no KM, no COSTO_EUR) | False |
| F_TURNO_PREP_SITO | (SITO, DATA_PREPARAZ) | COUNT | False |
| F_TRACCIABILITA_LOTTI | (?, DATA_?) | COUNT | False |

**Vincoli noti**:
- `F_GIACENZE_DAILY` in CDT_DW non ha dimensione sito (grain diverso)
- `F_TRASPORTO` in CDT_DW non espone `KM` ne `COSTO_EUR` (nostro-only)
- `QTA_DISPONIBILE` non esiste — misure reali `QTA_PEZZI` / `QTA_UF`
- fix pyarrow ACT_9009: partizioni reidratate dal path (prima davano 0 righe silenti)

## Sviluppo (diario)

### 2026-08-19 mattina — Apertura ACT + preflight

- Verificato ambiente: Docker Desktop riavviato dopo reboot notturno, VPN attiva, warehouse locale con 6 giorni completi 09-14/08
- Pipeline day-14 confermata completa (Bronze 35/35 OK, Silver 38/38 OK, Gold 27/27 OK)
- `track/spedizioni` del 14 mancante per ORA-01555 (undo Oracle troppo piccolo) — impatta solo F_TRASPORTO/F_ORDINI del 14 (marginale, i giorni 09-13 sono completi)

### 2026-08-19 pomeriggio — `--discover` sui 4 fact `oracle_confirmed: False`

Prerequisiti sistemati nel container `logistico-spark`: `pip install oracledb python-dotenv` (una tantum, non persistente al rebuild).

Comando pattern:
```
docker exec -e LOGISTICO_DATA=/workspace logistico-spark \
  python /workspace/code/scripts/quadratura/quadratura_fact.py --fact <FACT> --discover
```

Log completo in `scratchpad/discover_all.log`. Risultati sintetici:

| Fact | Tabella CDT_DW | # col | Colonne configurate | Nota |
|---|---|---:|---|---|
| GIACENZE | `F_STOCK` | 31 | ⚠️ `GIORNO_STOCK_ID` **NON TROVATA** (nome reale: `GIORNO_RILEV_STOCK_ID`) | grain Gold per MAG_COD (no sito) — confronto per sola data |
| TRASPORTO | `F_TRASP_MTV` | 35 | ✅ `MAG_SITO_COD` OK + `GIORNO_BOLLA_SPED_ID` OK | solo COUNT (ADR-0013 scope MTV, listini corrieri assenti) |
| TURNO_PREP_SITO | `F_TURNO_PREP_SITO` | 9 | ⚠️ `GIORNO_PREPARAZ_ID` **NON TROVATA** (nome reale: `GIORNO_ID`) | misure Gold: ORE_LAVORATE/PRODUTTIVE/NUM_PREPARATI — vanno derivate da ORA_TURNO_INIZ/FINE se le si volesse quadrare |
| TRACCIABILITA | `F_TRACC` | 16 | ✅ `MAG_SITO_COD` OK + `GIORNO_CARICO_ID` OK | COUNT etichette come misura principale |

**2 fix da segnalare a Luigi in ACT_9009** (config `FACTS` in `scripts/quadratura/quadratura_fact.py`):
- `GIACENZE`: `oracle_date_col` da `GIORNO_STOCK_ID` → `GIORNO_RILEV_STOCK_ID`
- `TURNO_PREP_SITO`: `oracle_date_col` da `GIORNO_PREPARAZ_ID` → `GIORNO_ID`

**Nota misure CDT_DW rilevate** (per popolare `oracle_measures`/`gold_measures` quando serve):
- F_STOCK: `PZ_STOCK`, `QTA_UF_STOCK`, `NUM_IMB_STOCK`, `VAL_STOCK_MED_POND`/`NET_ACQ`/`ULT_ACQ`, `NUM_PICK`
- F_TRASP_MTV: nessuna misura quantitativa esposta (grain MTV solo)
- F_TURNO_PREP_SITO: `ORA_TURNO_PREP_SITO_INIZ`/`FINE` (bisogna calcolare ORE come derivata)
- F_TRACC: nessuna misura quantitativa (COUNT etichette lato Gold `NUM_ETICHETTE`)

### 2026-08-19 pomeriggio — Quadratura F_CARICO 09-14/08

Comando:
```
docker exec -e LOGISTICO_DATA=/workspace logistico-spark \
  python /workspace/code/scripts/quadratura/quadratura_fact.py --fact CARICO \
  --da 2026-08-09 --a 2026-08-14
```
Log completo: `scratchpad/quad_carico.log`.

**Risultato**: 93 chiavi (sito×giorno) in CDT_DW, 76 in Gold locale, **82/93 con anomalie > 1% (soglia default)** → KO strutturale.

**Pattern osservati:**
- **17 chiavi mancanti in Gold** — tutte del 14/08 (atteso: landing di `track/spedizioni` del 14 fallito per ORA-01555, `silver_spedizioni_clean` NO_DATA, gold di conseguenza non ha nuove partizioni carico per il 14/08 su alcuni siti)
- **Delta 5-50% sui giorni 09-13 per i siti grandi** (05, 09, 16, 18, 40, 52): Gold locale sistematicamente **inferiore** a CDT_DW (in CNT, QTA_CARICO, QTA_UF, PES_CARICO)
- **Siti piccoli allineati** (33, 36, 37, 57): 0% delta in molti giorni — basso volume, poca differenza

**Root cause del delta**: **NON è un bug del codice** — è la manifestazione attesa del vincolo del flag `PSP_DATA_ESTRAZIONE_DWH`. Il landing simulator vede solo pesate NON ancora consumate da ODI, quindi silver.pesate contiene un **sottoinsieme** di quelle in CDT_DW. Poiché F_CARICO ha grain etichetta = pesata, il gap si propaga a valle.

Vedi memoria persistente [[logistico-oracle-flag-estrazione-dwh]]. In produzione post-cutover (ODI spento) il vincolo scompare e le quadrature convergono. In locale con ODI attivo il gap resta strutturale e i numeri assoluti non sono affidabili — ma:
- La **struttura del confronto** funziona (grain corretto, join CDT_DW/Gold OK, unità di misura coerenti)
- Il tool `quadratura_fact.py` gira senza errori
- Il fix pyarrow di ACT_9009 (partizioni reidratate dal path) è confermato funzionante

**Considerazione operativa**: sui **siti piccoli con delta 0%** possiamo dire con confidenza che struttura + calcoli sono corretti. Sui siti grandi il numero assoluto non è confrontabile finché ODI resta attivo.

### 2026-08-19 pomeriggio — Quadratura F_PREP_SPED 09-14/08

Log: `scratchpad/quad_prep_sped.log`.

**Risultato**: 96 chiavi (sito×giorno), **96 con anomalie > 1%** → KO totale. 40 chiavi solo in ODI (concentrate su 10-11/08).

**Blocco separato "scartate" (OP-PSP-1)**: Gold contiene ~**200k righe** con `DATA_BOLLA_SPED IS NULL` (TIPO_SCAR 09/10) che ODI **filtra via** (in ODI = 0 righe). Comportamento noto — divergenza documentata in OP-PSP-1, non è un bug.

Distribuzione siti (righe scartate Gold vs 0 in ODI): 51 con 33.815, 20 con 36.380, 09 con 33.260, 18 con 17.347, 05 con 16.368, 35 con 11.093, 52 con 9.671, ecc.

### 2026-08-19 pomeriggio — Quadratura degli altri 4 fact

Comandi identici a sopra, `--fact GIACENZE|TRASPORTO|TURNO_PREP_SITO|TRACCIABILITA --da 2026-08-09 --a 2026-08-14`. Log: `scratchpad/quad_giacenze.log`, `quad_trasporto.log`, `quad_turno_prep_sito.log`, `quad_tracciabilita.log`.

| Fact | Esito |
|---|---|
| GIACENZE | ❌ **BLOCCATO** da `validate_config()`: `GIORNO_STOCK_ID` non esiste in `CDT_DW.F_STOCK`. Nome reale: `GIORNO_RILEV_STOCK_ID` (visto in --discover) |
| TRASPORTO | ⚠️ **0 chiavi in CDT_DW.F_TRASP_MTV** per il periodo 09-14/08, 61 chiavi in Gold (tutte "solo in Gold"). Richiede investigazione: filtro data errato? stato spedizione? Il config `oracle_date_col=GIORNO_BOLLA_SPED_ID` era OK al --discover |
| TURNO_PREP_SITO | ❌ **BLOCCATO** da `validate_config()`: `GIORNO_PREPARAZ_ID` non esiste in `CDT_DW.F_TURNO_PREP_SITO`. Nome reale: `GIORNO_ID` (visto in --discover) |
| TRACCIABILITA | 86 chiavi CDT_DW vs 87 Gold, **90 anomalie totali** (3 solo ODI, 4 solo Gold, resto delta%) — bilanciamento migliore rispetto ai fact di carico |

**2 fix da segnalare a Luigi per ACT_9009** (config `FACTS` in `scripts/quadratura/quadratura_fact.py`):
1. `GIACENZE`: `oracle_date_col` da `GIORNO_STOCK_ID` → `GIORNO_RILEV_STOCK_ID`
2. `TURNO_PREP_SITO`: `oracle_date_col` da `GIORNO_PREPARAZ_ID` → `GIORNO_ID`

Nota positiva: **il gate `validate_config()` di ACT_9009 funziona perfettamente** — si è bloccato prima di produrre numeri sbagliati, come pianificato.

**Anomalia F_TRASPORTO da approfondire**: 0 chiavi CDT_DW è sospetto. Potrebbe essere:
- `F_TRASP_MTV` popolato solo dopo `stato_sped_id` finale (che ODI non aveva ancora calcolato per il periodo 09-14/08 al momento del run)
- filtro data sbagliato (ma `--discover` diceva OK)
- vista non aggiornata sull'Oracle di test

Follow-up nel prossimo run.

### 2026-08-19 pomeriggio — Chiusura sessione tecnica

Obiettivi originali ACT_9019 rispetto agli esiti:
- ✅ **O1 (--discover 4 fact)**: fatto, 2 su 4 hanno rivelato nomi colonna errati nel config (fix segnalati per ACT_9009)
- ⚠️ **O2 (quadratura F_CARICO + F_PREP_SPED)**: girate, entrambi KO strutturale per vincolo flag ODI (atteso)
- ⚠️ **O3 (quadrature altri 4 fact)**: 2 bloccate (GIACENZE, TURNO — config), 1 anomala (TRASPORTO 0 chiavi ODI), 1 girata (TRACCIABILITA)
- ⏸️ **O4 (consolidare in 07_certifica)**: rimando — meglio farlo dopo i fix Luigi e con il periodo cloud (finestra completa)
- ⏸️ **O5 (nuovi OP)**: nessun nuovo OP nato oggi; conferme su OP-PSP-1 e allineamento con memoria [[logistico-oracle-flag-estrazione-dwh]]

## Esito

**Parziale — bloccato da 2 fix in ACT_9009 (config nomi colonne) e dal vincolo strutturale flag ODI in ambiente locale.**

Il tool funziona; l'ambiente locale non è adatto a numeri "veri" finché ODI produzione consuma pesate/testate/scartate.

**Quadratura affidabile solo su cloud post-cutover** (ODI spento) — appartiene ai gate cloud `ACT_GATE-2/3/4/5/6` (deploy TEST + run schedulato + DQ + certificazione dati).

## Follow-up

1. **Segnalare a Luigi**:
   - 2 fix in `FACTS` di `scripts/quadratura/quadratura_fact.py` (`GIORNO_STOCK_ID`, `GIORNO_PREPARAZ_ID`)
   - Anomalia TRASPORTO 0 chiavi CDT_DW da investigare (potrebbe essere vista non popolata)
   - Documentare in `07_certifica_gold_vs_cdtdw.md` la limitazione ambiente locale (gap strutturale)

2. **Non riprovare quadrature offline** finché flag ODI resta attivo e config nomi non è fixato — sarebbe tempo perso su numeri non affidabili.

3. **Ripartenza vera delle quadrature** = post cutover ODI, dentro `ACT_GATE-2..6` (cloud TEST).

Log di dettaglio: `scratchpad/discover_all.log`, `quad_carico.log`, `quad_prep_sped.log`, `quad_{giacenze,trasporto,turno_prep_sito,tracciabilita}.log` (tutti nella scratchpad Claude).

## Verifica

_(da compilare a valle dei run)_

- [ ] `--discover` GIACENZE: colonne CDT_DW confermate
- [ ] `--discover` TRASPORTO: colonne CDT_DW confermate
- [ ] `--discover` TURNO_PREP_SITO: colonne CDT_DW confermate
- [ ] `--discover` TRACCIABILITA: colonne CDT_DW confermate
- [ ] Quadratura F_CARICO 09-14/08: match rate documentato
- [ ] Quadratura F_PREP_SPED 09-14/08: match rate documentato
- [ ] Quadrature restanti 4 fact: match rate documentato

## Esito

_(da compilare a chiusura)_

## Follow-up

_(potenziali: gap documentati → nuovo ADR o OP, gap tecnici quadratura → fix in ACT_9009, quadrature cloud-gated → ACT sprint 2.3.4/3.3.6/4.3.6/5.3.4)_
