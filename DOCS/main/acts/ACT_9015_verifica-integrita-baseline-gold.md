# ACT_9015 · Verifica integrità baseline Gold + rebuild storico movimentazione

**Status**: done (con follow-up aperti)   **Type**: data-quality   **Origin**: follow-up ACT_9005
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (Gold + DQ)
**Gg (stima)**: 0,5   **Blocco**: 🟢 (solo-locale)
**Created**: 2026-08-21   **Closed**: 2026-08-21
**Dipende da**: [[ACT_9005]] (re-run mirato), [[ACT_9010]] (dq_gate)   **Blocca**: —
**ADR collegate**: —   **OP collegati**: OP-02 (residui articolo/fornitore); nuovi OP-CAR-6, OP-CAR-7, OP-QDR-1, OP-GIA-1

## Contesto e motivazione
ACT_9005 ha scoperto 6,7M di righe stale in `F_PREP_SPED` (partizione `DATA_PREL IS NULL`, residuo di un run
pre-fix OP-PSP-2) che gonfiavano `SUM(QTA_PREP)` del **+92%**. Il dynamic partition overwrite non tocca le
partizioni che il flusso non produce più: il difetto era invisibile e si è scoperto per caso.

Due domande aperte: **quel pattern esiste su altri fact?** E, dato che lo spazio disco era tornato disponibile
([[ACT_MNT-01]]), **serve un re-run completo a 22 siti?**

## Obiettivo
Stabilire su base di evidenza se la baseline Gold locale è coerente col codice attuale, correggere ciò che è
correggibile e documentare ciò che non lo è. Quattro step: diagnostica → rebuild mirato → ri-certificazione
(dq_gate + quadratura) → VACUUM.

## Analisi tecnica

### Step 1 — diagnostica stale partitions (8 fact + 6 aggregati)
Due segnali incrociati per tabella: (a) valori NULL nelle colonne di partizione **reali**, lette da
`DESCRIBE TABLE` e non ipotizzate; (b) spread di `DWH_UPDATED_AT`, per individuare partizioni scritte da run
precedenti ai fix.

**Esito**: **nessuna partizione NULL residua** su tutte le 14 tabelle — il caso `F_PREP_SPED` era isolato e già
risolto. 12 tabelle su 14 hanno un solo giorno di scrittura (19/08), quindi sono interamente coerenti col
codice attuale.

**Conseguenza sulla decisione**: il **re-run completo a 22 siti non serve**, e un full refresh generalizzato
sarebbe lavoro a vuoto su 12 tabelle. Le eccezioni sono 2 e vanno trattate in modo opposto.

### Step 2 — rebuild `F_MOVIMENTAZIONE_CARRELLISTI` (ricostruibile)
Le sorgenti silver coprono tutte le date (`sessione_carrellista` 17 date, `missione_carrellista` 19) e il
notebook usa `replaceWhere` su `DATA_PRESENZA`, quindi è **idempotente per data**. Rieseguito il solo gold per
le 17 date presenti in silver: 17/17 rc=0.

| Verifica | Prima | Dopo |
|---|---|---|
| `NUM_PLT_MOVIMENTATI` NULL | 14 date su 15 | **0** |
| Date coperte | 15 | **17** (recuperate 06-11 e 06-12, prima assenti) |
| Righe totali | 1.484 | **1.719** = sessioni in silver |
| `2026-06-17` | 179 righe | **193** righe |
| Grain (CARRELLISTA, DATA, SITO) | — | univoco, 1.719/1.719 |
| `SUM(PLT) >= SUM(MISSIONI)` | n/d (NULL) | OK su tutte le 17 date |

**Scoperta oltre il previsto**: le partizioni di giugno non erano solo prive di `NUM_PLT` — che era il
follow-up noto di ACT_9005 — ma **incomplete**: mancavano 2 date intere e il 17/06 perdeva 14 righe su 193.

### Step 2b — `F_GIACENZE_DAILY`: ~170k righe NON ricostruibili
È un fact **snapshot**: `DATA_FOTO` deriva da `_silver_load_date`, cioè dalla data di caricamento. La landing
conserva **un solo snapshot** (`cdt-estr-landing/wl1_cndstostock/2026/06/09`) e `silver_curated.giacenze` una
sola data (2026-06-10). Le partizioni 13/16/19/21 giugno nacquero da file che non esistono più in nessun
livello: **non backfillabili**.

**Decisione**: non toccate. Cancellarle è irreversibile ed esce dal perimetro autorizzato (che riguardava le
partizioni a NULL). Resta una scelta aperta → OP-GIA-1.

**Rischio cloud verificato e RIENTRATO**: si temeva che un `full_refresh` su un fact snapshot potesse
distruggere storia non ricostruibile in produzione. Verificato che sia `gold_f_giacenze_daily` sia
`gold_f_movimentazione_carrellisti` usano `replaceWhere` limitato a `run_date`: la storia è strutturalmente
protetta. `full_refresh` nel repo esiste **solo** nel worktree abbandonato
`.claude/worktrees/nostalgic-panini-6713cd`, che non è codice vivo → da rimuovere, è confondente.

### Step 3 — dq_gate: 9 pipeline, 78 check, **78 PASS, 0 FAIL, 0 bloccanti falliti**
Stessa numerosità della validazione di [[ACT_9010]], quindi confronto diretto: **nessuna regressione**
introdotta dal rebuild. Esiti letti da `config_dev_etl.dq_results` (il log su file era illeggibile, vedi
Lezione 2).

### Step 3b — quadratura vs CDT_DW: **non certificabile come impostata**
Oracle raggiungibile in sola lettura (`CDT_DW.F_CARICO` = 63.762.953 righe). Ma:

1. **Errore di metodo**: quadrato su tutto giugno, mentre il warehouse locale contiene solo i giorni
   effettivamente ingeriti → tutte le chiavi risultano "solo in ODI". La documentazione
   (`07_certifica_gold_vs_cdtdw`) dichiara **attesa** questa condizione finché il backfill dello storico non è
   completo.
2. Anche sulla finestra documentata (`--da 2026-06-09 --a 2026-06-21 --soglia 5.0`) i 4 fact restano KO con
   ~100% di chiavi anomale, **dominate dalla copertura landing parziale**: la quadratura locale non è un test
   di correttezza finché il backfill non c'è. → OP-QDR-1.
3. `GIACENZE` e `TURNO_PREP_SITO` non partono affatto: colonne CDT_DW inesistenti (`GIORNO_STOCK_ID`,
   `GIORNO_PREPARAZ_ID`), coerente col commento `oracle_confirmed: False` nel dict `FACTS`. Servono
   `--discover`.

### Step 3c — DIFETTO TROVATO: `PES_CARICO` / `VOL_CARICO` NULL al 100%
`F_CARICO`: **59.621 righe su 59.621 con `PES_CARICO` e `VOL_CARICO` NULL**, mentre l'attività che li calcola
con la formula ODI risultava completata. Individuato dal delta `PES_d%` costante a 100,0% su **ogni** sito e
**ogni** data: un delta costante non è copertura mancante, è una colonna vuota.

**Causa**: `attach_carico_peso_volume` legge `{retail_master_schema}.LU_ART_UNITA_LOGISTICA`. Il default del
widget è `bronze_dev.condiviso` (scelta D2), che **in locale non esiste**: le LU derivate da CDT_DW stanno in
`cdtdw_condiviso`. Il `try/except` degrada a NULL con un solo `logger.warning` e la pipeline chiude in
successo.

**Fix verificato**: rieseguito `gold_f_carico` con `--set retail_master_schema=cdtdw_condiviso` →
`PES_CARICO` NULL **0**, `SUM(PES_CARICO)` = 32.912.850, `SUM(VOL_CARICO)` = 21.859.659.065. Gli 11.937 zeri
residui sono le righe senza match in anagrafica (48.875/59.621 = 82% di match), coerenti con l'`NVL(...,0)`
della formula ODI.

**Il difetto vero, e rilevante per il cloud**: il fallback è **silenzioso** e **nessun check DQ lo intercetta**
— `dq_gate` ha dato 13/13 PASS su `F_CARICO` con due misure di business interamente vuote. In cloud, uno
schema mal configurato produrrebbe un fact "verde" e inutilizzabile. → OP-CAR-6.

**Controprova incrociata sulla quadratura**: prima del fix `PES_d%` era costante a 100,0% mentre `CNT_d%` e
`QTA_d%` variavano; dopo il fix, sul singolo 2026-06-10, `PES_d%` scende a **68–98% e si muove insieme ai delta
di conteggio** (es. sito 20: CNT 78,3% / QTA 74,7% / PES 68,4%). Doppia conclusione: la formula ODI del peso è
corretta, e il delta residuo ha **una sola causa** — il Gold ha meno righe di ODI per copertura landing
parziale, non per errori di calcolo. Questo è il criterio da riusare: un delta *costante* accusa una colonna,
un delta *correlato al conteggio* accusa la copertura.

### Step 3d — `CORRIERE_COD` orphan 100%
`F_CARICO.CORRIERE_COD` = sentinel `-1` su tutte le 59.621 righe. **Non è un errore di join**:
`silver_curated.carico.CORRIERE_COD` è NULL su tutte le righe, la sorgente non porta il vettore per i carichi.
Emerge un'incoerenza di trattamento in `attach_carico_dimensions`: operatore NULL → `'ND'` (non orfano),
corriere NULL → `'-1'` (orfano, allarme al 100%). → OP-CAR-7.

**Nota**: si è sospettato un bug architetturale (un solo `retail_master_schema` per LU che vivono in due schemi
diversi). **Sospetto infondato**: il codice separa correttamente le LU retail (`retail_ms`) da quelle
logistiche (`{gold_catalog}.logistica`).

### Step 4 — VACUUM
Per-database con `PYTHONUNBUFFERED=1`, come da Lezione 1 di [[ACT_MNT-01]].

## Esito
Baseline Gold coerente col codice per 13 fact/aggregati su 14. `F_MOVIMENTAZIONE_CARRELLISTI` sanato e più
completo di prima. dq_gate 78/78. Trovati e diagnosticati 2 difetti (`PES`/`VOL_CARICO`, `CORRIERE_COD`) e 1
limite metodologico (quadratura non significativa senza backfill). **Il re-run completo a 22 siti è risultato
non necessario**: l'evidenza ha sostituito l'assunzione.

## Lezioni operative (ambiente locale)
1. **Un `docker exec` troncato non uccide il processo nel container.** Quando il tool ha interrotto il primo
   `dq_gate` a 10 minuti, il processo è rimasto vivo tenendo il lock del metastore Derby (single-writer) e ha
   fatto fallire il rilancio con `Unable to instantiate SessionHiveMetaStoreClient`. I job lunghi vanno lanciati
   in background dall'inizio; prima di rilanciare, verificare con `docker exec ... ps -eo pid,etime,cmd`.
2. **Non riusare lo stesso file di log per un rilancio.** Troncare un file su cui un altro processo scrive a un
   offset elevato crea un buco di byte NUL: `grep` lo classifica come binario e l'output diventa illeggibile.
   Un file per tentativo. In alternativa leggere gli esiti dalla loro sede autorevole (`dq_results`).
3. **`quadratura_fact.py` nel container**: passare `LOGISTICO_DATA=/workspace` (il default è un path Windows) e
   caricare il `.env` Oracle con `set -a; . .env; set +a`.

## Follow-up
- ✅ **OP-CAR-6 — RISOLTO** (2026-08-21). Tre interventi:
  1. `PES_CARICO`/`VOL_CARICO` in `not_null` (BLOCKING) nei criteri di `gold_f_carico`. `measures_nonneg` da
     solo **non li copriva**: un NULL non è un valore negativo, quindi passava con 0 negativi su colonne vuote.
  2. Fallback anagrafiche non più silenzioso: log **ERROR** + `dq_result` strutturato
     (`check_name=anagrafica_peso_volume_disponibile`, `passed=false`) con il widget da correggere. Nota
     implementativa: il `logger` passato ai notebook è un `logging.Logger` **stdlib** (`get_logger`) e non
     accetta kwargs custom — per l'evento strutturato si istanzia il nostro `Logger`, come fa
     `check_orphan_rate`. Il primo tentativo, che chiamava `logger.error(..., event=...)`, faceva **fallire il
     notebook dentro il blocco except**.
  3. Divergenza locale sanata alla radice: le 6 LU ripubblicate in `bronze_dev.condiviso` (sede D2, run
     `gold_lu_from_cdtdw` con `run_date=2026-07-03`, l'unica data che le copre tutte). Ora il **default del
     widget funziona senza override** e il locale rispecchia il cloud — nessun `--set` da ricordare.

  **Verifica end-to-end** (il punto che conta: provare che l'allarme suoni):
  | Scenario | Esito |
  |---|---|
  | default `bronze_dev.condiviso` | `PES_CARICO` NULL **0**, SUM 32.912.850, gate **16/16 PASS** (erano 13) |
  | `retail_master_schema=schema_inesistente` | allarme ERROR + **`DQBlockingError`**, 2 check BLOCKING falliti |
  | ripristino default | gate di nuovo verde |

  Lo scenario che prima passava 13/13 in silenzio ora si ferma. [[LL-005]] promossa a
  `guardrail-automatico`: debito di automazione da 4 a 3.
- **OP-CAR-7** (medio): decidere se `CORRIERE_COD` NULL debba diventare `'ND'` come gli operatori, oppure se la
  sorgente del vettore carico va colmata a monte.
- **OP-QDR-1** (alto): la quadratura va eseguita sulla sola copertura effettiva del Gold, o dopo il backfill.
  Aggiungere il default automatico della finestra dalla copertura reale. Confermare con `--discover` le colonne
  CDT_DW di `GIACENZE` e `TURNO_PREP_SITO`.
- **OP-GIA-1** (decisione utente): le ~170k righe di giugno di `F_GIACENZE_DAILY` non sono ricostruibili.
  Tenerle (logica mista) o rimuoverle (baseline a data singola, perdita definitiva)?
- Rimuovere il worktree abbandonato `.claude/worktrees/nostalgic-panini-6713cd`.
- ✅ **Fatto**: `pytest>=8.0` aggiunto a `docker/local_bronze/requirements.txt`. Non era nell'immagine: i 30
  test guardrail di [[ACT_9014]] esistevano ma **in locale nessuno poteva eseguirli**. Un guardrail non
  installato è documentazione, non protezione.
- ✅ **Fatto**: `oracledb>=4.0.2` e `python-dotenv>=1.2.3` aggiunti a
  `docker/local_bronze/requirements.txt` (erano installati solo a mano nel container e si perdevano al rebuild
  dell'immagine). L'intestazione di `quadratura_fact.py` documenta ora l'invocazione corretta nel container
  (`LOGISTICO_DATA=/workspace` + sourcing del `.env`) e l'avvertenza di interpretazione OP-QDR-1.
