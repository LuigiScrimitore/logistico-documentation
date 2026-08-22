---
id: LL-005
titolo: Un delta costante accusa una colonna, un delta correlato al conteggio accusa la copertura
sintomi:
  - "quadratura: una colonna di delta è esattamente 100,0% su ogni sito e ogni data"
  - "quadratura KO su tutte le chiavi sito×giorno"
  - "una misura di business è NULL su tutte le righe del fact"
tag: [quadratura, dq, gold, dati, diagnostica]
stadio: guardrail-automatico
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_9015]
---

## Sintomo
Report di quadratura con tutte le chiavi in anomalia. Nel rumore generale, una colonna si comporta
diversamente dalle altre: `PES_d%` era **esattamente 100,0%** su ogni sito e ogni data, mentre `CNT_d%` e
`QTA_d%` variavano fra 16% e 100%.

## Strada sbagliata
Leggere "KO su tutte le chiavi" come un unico problema e concludere che la quadratura sia inaffidabile o che i
dati siano sbagliati in blocco. Sotto quel KO c'erano **due fenomeni distinti** con cause opposte, e uno dei
due era un difetto reale che nessun altro controllo aveva visto.

## Regola
Nei report di quadratura, **leggere la forma del delta, non solo il suo valore**:

- **delta costante** (identico su ogni chiave) → una **colonna** è vuota o rotta. Non è un problema di dati, è
  un problema di calcolo o di configurazione.
- **delta variabile e correlato al delta di conteggio** → è **copertura**: il target ha meno righe della
  sorgente. Non è un errore di calcolo.

Controprova: dopo aver corretto la causa, il delta della colonna deve **muoversi insieme** a quello dei
conteggi. Nel caso reale `PES_d%` è passato da 100,0% costante a 68–98% allineato a `CNT_d%` — doppia conferma
che la formula era giusta e che il residuo aveva una sola causa.

**Diventata guardrail** (2026-08-21, OP-CAR-6): `PES_CARICO` e `VOL_CARICO` sono ora in `not_null`
(BLOCKING) nei criteri di `gold_f_carico` in `lib/logistica_utils/acceptance.py`, e il fallback
anagrafiche emette un `dq_result` con `passed=false` invece di un solo warning.

Nota su **perche** il check mancava: `PES_CARICO` era gia in `measures_nonneg`, ma un NULL non e un
valore negativo — il check passava con 0 negativi su una colonna interamente vuota. Un criterio che
sembra coprire una colonna puo non coprirla affatto: verificare quale **classe** di anomalia intercetta.

Nel caso concreto `F_CARICO` aveva le due misure NULL su **59.621 righe su 59.621** e `dq_gate` dava
**13/13 PASS**. Dopo il fix: con schema errato 2 check BLOCKING falliti e `DQBlockingError`.

## Perché
La causa era un `try/except` che degrada silenziosamente: `attach_carico_peso_volume` legge
`{retail_master_schema}.LU_ART_UNITA_LOGISTICA` e, se lo schema non è raggiungibile, mette NULL con un solo
`logger.warning` e **la pipeline chiude in successo**. Il default del widget puntava a `bronze_dev.condiviso`
(scelta D2) mentre in locale le LU stavano in `cdtdw_condiviso` — divergenza poi sanata ripubblicando
le LU nella sede D2, così il default funziona in entrambi gli ambienti.

Il punto generale, valido anche in cloud: **un fallback silenzioso trasforma un errore di configurazione in un
dato mancante**, e un dato mancante che nessun check copre è indistinguibile da un dato corretto. Un fact che
supera tutti i controlli con due misure di business vuote è più pericoloso di una pipeline che fallisce.

Corollario: la quadratura locale **non è un test di correttezza** finché il backfill dello storico non è
completo — CDT_DW ha la storia di produzione, il Gold locale solo i giorni ingeriti. Va eseguita sulla copertura
effettiva del Gold, altrimenti il rumore da copertura nasconde i segnali veri (→ OP-QDR-1).

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · applicando la regola su una finestra di un solo giorno, i delta residui
  (CNT 78,3% / QTA 74,7% / PES 68,4% sul sito 20) sono risultati tutti correlati: nessun'altra colonna rotta
  oltre a peso e volume.
- 2026-08-21 · luigi.scrimitore · promossa a guardrail: verificata end-to-end iniettando uno schema
  anagrafiche inesistente. Il notebook degrada (per scelta) ma emette l'allarme, e il gate blocca con
  `DQBlockingError`. Ripristinato il default: 16/16 PASS.
