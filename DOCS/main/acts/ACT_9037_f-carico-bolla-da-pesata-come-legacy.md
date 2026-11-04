# ACT_9037 · F_CARICO: portare `NUM_BOLLA_FORN` dalla pesata (come il legacy), grana etichetta×bolla

**Status**: done (codice validato; rilascio insieme ad ACT_9038)
**Type**: fix (correttezza / grana)
**Origin**: emerged — follow-up [[ACT_9036]] (il fix grana-pesate non basta: serve riallineare la semantica della bolla)
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Fase / Wave**: FASE 2 — Wave A Carichi
**Gg (stima)**: ~0,5–1 gg DEV (vedi stima sotto)
**Blocco**: nessuno (DEV); release multi-repo a parte
**Created**: 2026-10-29   **Closed**: 2026-10-29   **Owner**: team
**Dipende da**: [[ACT_9036]] (grana pesate validata a secco), [[LL-034]] (chiave anti fan-out)
**Interagisce con**: [[ACT_9035]] (riconciliazione bolla↔dettaglio da condizionare)   **OP collegati**: Q-01

## Contesto e motivazione
La quadratura F_CARICO gold vs CDT_DW (ottobre) è **99,998% copertura, misure chiave ≤0,01%**. Il residuo
0,007% è su ~204 etichette **multi-bolla** (pesata splittata su 2 bolle fornitore). [[ACT_9036]] ha provato a
risolverlo correggendo solo la **grana delle pesate** (bronze +`PSP_NUMBOL`, silver_pesate identità+bolla): la
logica pesate è corretta e validata a secco, ma end-to-end ha **peggiorato** (fan-out, copertura 99,998%→98,1%).

**Causa profonda (decisione di stasera, 2026-10-29):** la `NUM_BOLLA_FORN` del **gold** NON è la bolla della
pesata — è la bolla del **dettaglio** (`r.BOLLA_FORN_NRO`), **riconciliata** da [[ACT_9035]]. Nel **legacy**
CDT_DW invece `NUM_BOLLA_FORN = PSP_NUMBOL`, cioè la bolla **della pesata**. Sono campi diversi. Con 2 pesate
stessa etichetta/ordine/MSI, la riconciliazione ACT_9035 assegna a entrambe la **stessa** bolla dettaglio → 2
righe identiche = fan-out.

→ **La logica corretta è quella del legacy: la bolla del fatto è quella della pesata.** Il nostro modello
dettaglio-centrico la ricostruisce dal dettaglio; va riallineato all'origine-pesata.

## Obiettivo
Gold F_CARICO con **1 riga per (etichetta × bolla fornitore della pesata)** come CDT_DW:
- quadratura ottobre → **copertura e 4 misure chiave al 100%** (azzerare le ~204 multi-bolla divergenti);
- **0 fan-out** sulle etichette a bolla singola (guardia [[LL-034]]);
- **nessuna regressione** della copertura recuperata da [[ACT_9035]] (il ~2% riconciliato non deve tornare a cadere).

"Fatto" = i tre criteri sopra verdi su un mese test (ottobre) + guardia unicità gold a 0.

## Analisi tecnica (soluzione adottata, v2.3.0)
1. **`bronze_pesate.py`** — chiave **invariata** `[MAG_SITO_COD, PSP_NUMETIC, PSP_DATABOLLA]`; solo commento sul perché
   `PSP_NUMBOL` non va in chiave (provato: stati intermedi → bolle fantasma, +0,009% UF).
2. **`silver_pesate.py`** — dedup e MERGE su `(SITO, CARICO_LOG_NRO, ETICHET_NRO, BOLLA_NRO)`, ultima versione per
   `_bronze_insert_ts`. Nessun filtro placeholder a lista fissa.
3. **`silver_prep_carico.py`** v2.3.0 — `NUM_BOLLA_FORN = PSP_NUMBOL` (bolla originale della pesata, prima della
   riconciliazione [[ACT_9035]], che resta invariata per la join); filtro degli snapshot: per `(sito, carico, etichetta)`
   si tengono le bolle presenti nel dettaglio dello stesso carico, altrimenti l'ultimo snapshot.
4. **`quadratura_f_carico_misure.py`** — bolla nella chiave di confronto (`norm_bolla` solo stringa: bolle tipo
   `'2550/00'`) + `UF_ODI_TOT`/`UF_GOLD_TOT` su tutte le righe ([[LL-040]]).

**Decisione semantica**: la bolla di F_CARICO è quella della pesata (`PSP_NUMBOL`), come CDT_DW.

## Sviluppo (diario)
- 2026-10-29 · ACT aperta. Logica bersaglio decisa = legacy (bolla da pesata). Punti 1-2 già validati a secco in
  ACT_9036; il lavoro vero è il punto 3 (condizionare ACT_9035) + non-regressione.
- 2026-10-29 bis · **Primo tentativo FALLITO (over-split).** `NUM_BOLLA_FORN = _ORIG_BOLLA_NRO` + filtro
  placeholder `{'1','ONE'}` in silver_pesate. La guardia aveva dato "verde" (copertura 99,984%, 4 misure delta
  0,0%) ma era un **falso positivo**: il confronto misure gira solo sul **sottoinsieme comune**, mentre il gold
  aveva **bolle fantasma solo-gold** che gonfiavano i totali. Diagnosi `diag_oversplit.py`: gold 1004 etichette
  multi-bolla vs ODI 88; **991 etichette con più bolle nel gold** (over-split), UF gold 164,12M vs ODI 163,94M =
  **+0,11% sovra-conteggio**. Causa: i placeholder non sono solo `{'1','ONE'}` — es. `95429083` ODI`[10557/00]`
  gold`[10557/00, 2]`, `95569011` ODI`[4347/26]` gold`[4347/26, ROYAL]`, `95799934` ODI`[4534]` gold`[4534, ALMA]`.
  Resuscitando la bolla originale della pesata, ogni snapshot placeholder riconciliato diventava una riga.
- 2026-10-29 ter · **Redesign (fix robusto).** Via la lista fissa: output = `r.BOLLA_FORN_NRO` (bolla reale del
  dettaglio) + dedup in prep su `(sito,carico,etichetta,bolla-reale)` con preferenza allo snapshot nativo. La
  "bolla reale" la definisce il dettaglio, non una lista. Aggiunto alla verifica il **controllo totale-UF**
  (gold totale = ODI totale, NON solo sul comune) per intercettare over/under-count nascosti. Rebuild ottobre in
  corso.

- 2026-10-29 quater · Variante "output = bolla del dettaglio": copertura crollata a 98,10% (per il ~4,8% riconciliato
  la bolla del dettaglio ≠ quella ODI) → scartata. Versione finale = output `PSP_NUMBOL` + filtro snapshot via dettaglio.

## Verifica
Rebuild su un mese test (ottobre) — `bronze_pesate` → `silver_pesate` full_refresh → `silver_prep_carico` →
`gold_f_carico` → `quadratura` — poi controlli SQL:
- **Guardia fan-out**: gruppi duplicati su `(SITO_COD, NUM_DOC_CARICO, NUM_ETICH, NUM_BOLLA_FORN)` = **0**;
- **Multi-bolla allineate**: etichette gold con `COUNT(DISTINCT NUM_BOLLA_FORN) > 1` ≈ **88** (le reali ODI), NON
  migliaia (quello era l'over-split);
- **Controllo totale-UF (NUOVO, anti falso-positivo)**: `SUM(QTA_UF) gold ≈ SUM(QTA_UF) ODI` sull'INTERO mese (non
  solo sul comune) — scarto ~0% (intercetta over/under-count che il confronto sul comune nasconde);
- **Quadratura** ottobre con chiave +bolla: **4 misure chiave delta 0,0%**, copertura ~99,98%;
- **Non-regressione ACT_9035**: copertura complessiva ottobre resta ~99,98% (il ~2% riconciliato non ricade);
- Residuo copertura (~97 etichette, 0,016%): pesate collassate nel **bronze storico** a parità di
  `(sito,etichetta,data-bolla)` prima del fix 4-chiavi — recuperabili solo con ri-merge bronze da landing (se la
  landing le ha entrambe) o ri-estrazione Oracle. (Il forward-fix a 4 chiavi in `bronze_pesate.py` è stato poi **scartato**: bronze resta a 3 chiavi; recupero in [[ACT_9038]].)

## Esito
**2026-10-29 — fix pulito applicato e validato a secco su ottobre (run 9037c).** Stato dev corrente:
- **0 fan-out**, **0 over-split**, **0 over-count** (prima +0,11%);
- **Totale UF gold vs ODI = −0,003%** (controllo su TUTTO il mese, non solo comune) → niente doppi conteggi nascosti;
- **4 misure chiave (QTA_CARICO, QTA_UF_CARICO, PES_CARICO, VOL_CARICO): delta 0,0%, 0 noMatch/392**;
- **Copertura (chiave + bolla): 99,983%** (N_ODI=603084, comuni=602984);
- multi-bolla gold = 18 (le genuine presenti nel dettaglio), QTA_ORD_FORN/VAL_COSTO invariate (OP-CAR-3/OP-CAR-1).

**Validazione finale v2.3.0 (set + ott, incl. ramo incrementale di silver_pesate):** settembre 0 dup, 4 misure 0,0%,
UF −0,010%, copertura 99,979%; ottobre identico a sopra (UF −0,003%, 99,983%). Log: `LOGISTICO_DATA/datarelay_compare/final_9037.log`.

**Residuo — spiegazione corretta (2026-10-29 sera).** Una prima spiegazione ("2e righe calcolate dalla vista legacy,
100% impossibile") era **sbagliata**: `V_CARICO_ORDINARIO` joina pesata↔righe INNER anche sulla bolla (OP-CAR-5), quindi
la 2a riga ODI è una **2a pesata vera** in Oracle (verificato: 97696459 ha …558/UF72 e …559/UF12). Quella pesata non
arriva in landing perché l'estrattore — e anche **DataRelay** — deduplica su `(PSP_NUMETIC, PSP_DATABOLLA)` prima di
scrivere il file. Il re-merge bronze a 4 chiavi da landing è stato comunque scartato (+0,009% UF di stati intermedi) e
il bronze riportato alla v126. Recupero, prova numerica e residuo ulteriore → [[ACT_9038]].

**Rilascio:** codice sul branch `fix/act-9037-bolla-pesata` (commit 4e3a3bb), **non rilasciato** su decisione
dell'utente (prima il 100%, ACT_9038). Dev riportato a v2.2.0 = codice dei job schedulati (v0.1.20), perché
`silver.pesata` a grana +bolla non è compatibile col codice vecchio.

## Stima tempo
- **Caso liscio: ~0,5 gg** (3–4 h): redesign punto 3 (1–2 h) + riapplico 1-2 (~15 min) + 1 rebuild (~25 min) +
  controlli (~15 min).
- **Realistico: ~1 gg** (2–3 cicli di debug sul punto 3 per la non-regressione ACT_9035, ogni giro ~25 min di run).
- Fuori stima: **release multi-repo** (push Francesco, ~mezza gg sua) e eventuale **ri-estrazione pesate** per le
  ~179 etichette già collassate nel bronze storico (solo se si vuole il 100% anche sullo storico, non solo d'ora in poi).

## Lezioni
- [[LL-040]] — la quadratura delle misure sulle sole chiavi comuni nasconde il sovra-conteggio (guardia sui totali).

## Follow-up
- Eventuale **ADR** sulla semantica bolla F_CARICO (vedi sopra).
- [[ACT_9038]] — 2e pesate multi-bolla perse in estrazione (anche DataRelay) + residuo; condizione per il rilascio.
