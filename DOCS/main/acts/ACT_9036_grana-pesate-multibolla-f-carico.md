# ACT_9036 · Grana pesate multi-bolla F_CARICO: il bronze collassa etichette con 2+ bolle fornitore

**Status**: done (indagine chiusa — fix in [[ACT_9037]], residuo in [[ACT_9038]])
**Type**: fix (correttezza / grana)
**Origin**: follow-up [[ACT_9035]] — indagine sul residuo quadratura ottobre ("al SAL vogliono 100%")
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-28   **Owner**: team
**OP collegati**: Q-01   **Dipende da / interagisce con**: [[LL-034]] (chiave silver pesate anti fan-out)

## Contesto / sintomo
Quadratura F_CARICO gold vs CDT_DW ottobre 1–27: copertura 99,998%, misure chiave ≤0,011%. Il residuo
0,007% è tutto su **45 etichette** "divergenti". Richiesta: capire e, se risolvibile, azzerare.

## Diagnosi (verificata sul dato, 2026-10-28)
Seguendo 45 etichette fino alla sorgente viva (PESATE@LOG_xxx) e a CDT_DW.F_CARICO:
- **44/45 hanno 2 (o 3) pesate** nella sorgente, con **tutto identico tranne `PSP_NUMBOL`** (= la **bolla
  fornitore**, `NUM_BOLLA_FORN`). Non sono ripesature: sono **più bolle fornitore sotto la stessa etichetta**.
- **CDT_DW.F_CARICO tiene 2 righe** (grana = etichetta × bolla). **Il nostro gold ne tiene 1** → perde una bolla.
  In 42/45 vale `gold + odi = somma pesate sorgente` (si spartiscono le righe).
- **Dove si perde**: `bronze_pesate` fa MERGE con chiave **`[MAG_SITO_COD, PSP_NUMETIC, PSP_DATABOLLA]`**;
  due bolle con stessa etichetta e stessa data-bolla hanno la **stessa chiave** → la MERGE le collassa
  (la seconda sovrascrive). `PSP_NUMBOL` NON è in chiave. Confermato: `bronze.pesate` ha 1 riga dove la
  sorgente ne ha 2.
- La **quadratura** confronta su sola `NUM_ETICH` (senza `NUM_BOLLA_FORN`) → dedup che tiene una riga a caso
  per lato → il delta misurato è in parte artefatto di grana, ma il **dato gold è realmente incompleto**.

→ Non è dato storico, non è "gold più aggiornato", non è errore di calcolo: è **perdita di riga per chiave di
merge troppo corta** sulle (poche) etichette multi-bolla.

## Analisi d'impatto (ODI set+ott, 57 giorni, 1.287.801 righe)
- **Etichette multi-bolla: 204** su 1.287.589 distinte = **0,0158%** (set 116, ott 88).
- **Chiavi bronze che collassano** `(SITO,NETI,DATA_BOLLA)`: **179** → **183 righe perse** dal bronze.
- Impatto misura UF stimato: **~23.776 UF su 348,1M = 0,0068%**.
- Le ~25 etichette multi-bolla con bolle su **date diverse** sopravvivono al bronze (data-bolla in chiave) ma
  verrebbero comunque collassate a valle dal silver (chiave `(SITO,CARICO,ETICHET)`, senza bolla).

## Obiettivo ("fatto" =)
Gold F_CARICO con **1 riga per (etichetta × bolla fornitore)** come CDT_DW → quadratura ottobre **100%** su
copertura e 4 misure, **senza reintrodurre il fan-out** risolto da [[LL-034]].

## Soluzione (design — DA APPROVARE)
1. **`bronze_pesate`**: aggiungere **`PSP_NUMBOL`** a `MERGE_KEYS` → `[MAG_SITO_COD, PSP_NUMETIC,
   PSP_DATABOLLA, PSP_NUMBOL]`. Le bolle distinte sopravvivono.
2. **Grana silver** (`silver_pesate` / `silver_prep_carico`): includere la bolla nell'identità pesata
   (candidata `(SITO, CARICO, ETICHET, NUMBOL/BOLLA)`) così il silver non ricollassa.
3. **Quadratura** (`quadratura_f_carico_misure`): aggiungere `NUM_BOLLA_FORN` alla chiave di confronto.

## ⚠️ Insidia (LL-034)
La chiave silver `(SITO, CARICO, ETICHET)` fu scelta da [[LL-034]] **apposta** per eliminare un fan-out ×2
delle pesate (chiave `(SITO,ETICHET,DATA_BOLLA)` instabile). Aggiungere la bolla deve **distinguere la doppia
bolla legittima dal duplicato spurio** che LL-034 risolse. Il fix va validato che: (a) recuperi le 204
multi-bolla, (b) NON reintroduca fan-out sulle etichette a bolla singola. Serve un conteggio pre/post su tutto
lo storico (righe gold per etichetta) prima del rilascio.

## Come verificarla
- Post-fix: `bronze.pesate` e gold hanno 2 righe per le 44 etichette campione (es. et95568643 → 184 + 8).
- Ri-quadratura ottobre con chiave `+NUM_BOLLA_FORN`: 0 etichette divergenti, copertura e 4 misure 100%.
- Guardia anti-fan-out: righe gold = etichette×bolle distinte (no duplicati) sullo storico set+ott.

## Esito
**Indagine chiusa 2026-10-28. Firma placeholder trovata: `BOLLA_NRO ∈ {'1','ONE'}` (LL-034); 0/204 etichette
multi-bolla vere usano il placeholder.**

### Validazione a secco (guardia step A) ✅
Nuova dedup pesate applicata al bronze attuale (temp table): +1.393 righe recuperate, **0 duplicati** sulla
nuova chiave, **0 placeholder+reale insieme**, max 3 righe/etichetta. Logica pesate **corretta e safe**.

### Tentativo end-to-end (step B) ❌ — ha PEGGIORATO, revertito
Applicato il fix a 3 notebook (bronze_pesate +PSP_NUMBOL, silver_pesate identità+bolla/scarto placeholder,
quadratura +NUM_BOLLA_FORN) e ricostruito ottobre da bronze attuale:
- **gold 1.172 duplicati** su `(SITO,NUM_DOC,NUM_ETICH,NUM_BOLLA_FORN)` = **fan-out**; **0 etichette gold
  multi-bolla**; copertura **99,998% → 98,1%**.
- **CAUSA PROFONDA (nuova):** la `NUM_BOLLA_FORN` del **gold** NON è la bolla della pesata: è la bolla del
  **dettaglio** `r.BOLLA_FORN_NRO`, **riconciliata** da [[ACT_9035]] (blocco `_new_bolla`, righe ~142-159 di
  `silver_prep_carico`). In **CDT_DW** invece `NUM_BOLLA_FORN = PSP_NUMBOL` (bolla della **pesata**). Sono
  **campi diversi**. Con 2 pesate stessa etichetta/ordine/MSI, la riconciliazione `_u_ord` assegna a entrambe
  la **stessa** bolla dettaglio → 2 righe identiche = fan-out (non 2 bolle distinte).
- Modifiche sorgente **revertite** (repo pulito); **dev ottobre ripristinato** col codice vecchio.

### Il vero fix (più grande del previsto)
Non basta la grana pesate: serve **rivedere `silver_prep_carico`** perché:
1. `NUM_BOLLA_FORN` del gold va **presa dalla pesata (`PSP_NUMBOL`)**, non dal dettaglio riconciliato, per
   allinearsi a CDT_DW;
2. le 2 pesate di un'etichetta devono produrre **2 righe con la propria bolla**, bypassando/condizionando la
   riconciliazione ACT_9035 (che assume 1 pesata/etichetta) nei casi multi-bolla;
3. poi bronze (+PSP_NUMBOL) + silver_pesate (grana validata) + quadratura (+bolla da pesata).
Impatto resta **0,007%** → fix da pianificare come redesign di `silver_prep_carico`, non quick-win.

### Decisione (2026-10-29)
**La logica corretta è quella del legacy: `NUM_BOLLA_FORN` del fatto carico è la bolla della PESATA
(`PSP_NUMBOL`), non quella del dettaglio riconciliato.** Il nostro modello dettaglio-centrico va riallineato
all'origine-pesata. Il fix (redesign `silver_prep_carico` + riapplicazione grana pesate + quadratura +bolla) è
**tracciato e schedulato in [[ACT_9037]]** (stima ~0,5–1 gg DEV). Questa ACT_9036 resta la SSOT dell'**indagine**
(diagnosi, impatto, firma placeholder, perché il solo fix-grana non basta); l'esecuzione del fix vive su ACT_9037.

### Stato
`done` (2026-10-29) — fix eseguito in [[ACT_9037]] (prep v2.3.0). Nota: l'ipotesi "pesate collassate dal bronze" era
solo in parte giusta: le 2e pesate mancano già in **landing** (l'estrattore deduplica su etichetta+data-bolla) →
recupero in [[ACT_9038]].
Dati di supporto in `LOGISTICO_DATA/datarelay_compare/` (guard9036.json, rebuild_B.log, verify_45_result.json).

## Note
- Dettaglio dato: `LOGISTICO_DATA/datarelay_compare/` (quad_drill_ott.json, verify_45_result.json,
  odi_rule_result.json, impact_multibolla.json).
- Le 2 misure fuori-perimetro (QTA_ORD_FORN, VAL_COSTO_CARICO) restano punti aperti indipendenti
  (OP-CAR-3 / OP-CAR-1), non c'entrano con questa grana.
