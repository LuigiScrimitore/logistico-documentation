# ACT_9038 · F_CARICO al 100%: recuperare le 2e pesate delle etichette multi-bolla (estrazione → bronze → silver)

**Status**: rilasciato (2026-11-04: PR #45, GitLab workflows v0.1.21 / lib v1.0.9, deploy dev 63bcff1); restano il recupero 31/10–04/11 e la correzione DataRelay
**Type**: fix (completezza dato)
**Origin**: emerged — residuo di [[ACT_9037]] (copertura 99,983%, ~88 etichette/mese)
**Fase / Wave**: FASE 2 — Wave A Carichi
**Gg (stima)**: ~1–1,5 gg DEV + 1 verifica Oracle (utente)
**Blocco**: correzione DataRelay (progetto esterno) per la causa A
**Created**: 2026-10-29   **Closed**: —   **Owner**: team
**Dipende da**: [[ACT_9037]] (grana etichetta × bolla, v2.3.0)   **OP collegati**: Q-01

## Contesto e motivazione
Dopo [[ACT_9037]] F_CARICO quadra su misure (4 chiave a delta 0,0%) e totali (UF −0,003%), con copertura
99,983%. Il residuo sono ~88 etichette/mese **multi-bolla**: in CDT_DW la stessa etichetta ha 2 righe con 2 bolle e
2 UF reali (es. 97696459: bolla …558/UF 72 + …559/UF 12). La vista legacy `V_CARICO_ORDINARIO` joina pesata↔righe
**INNER su `psp_numbol = srcar_nro_bolla_forn`** (OP-CAR-5) → la 2a riga esiste perché in Oracle ci sono **2 pesate**.
Da noi la 2a pesata **non arriva in landing** (verificato su 3 etichette campione: una sola pesata per etichetta).

**Causa**: `scripts/landing_simulator/extract_oracle_to_landing.py` deduplica le righe per `merge_keys` **prima** di
scrivere il file; per `pesate` le chiavi sono `["PSP_NUMETIC", "PSP_DATABOLLA"]` (config.yaml) → due pesate con stessa
etichetta e stessa data-bolla ma bolla diversa diventano una. La landing di set/ott è stata scritta da quell'estrattore.

## Obiettivo
Copertura F_CARICO **100,000%** vs CDT_DW (set + ott), senza regressioni: 0 duplicati, totale UF gold = ODI, 4 misure
chiave a delta 0,0%, multi-bolla gold = multi-bolla ODI.

## Piano
1. **Verifica Oracle (sola lettura, la lancia l'utente)**:
   `C:\PROGETTI\LOGISTICO_DATA\datarelay_compare\check_pesate_multibolla_oracle.py` → (a) le 2e pesate esistono in
   Oracle; (b) sui giorni scritti da **DataRelay** (28-29/10) Oracle ha casi multi-bolla che la landing non ha?
   Se sì anche DataRelay le scarta → la correzione va chiesta al progetto DataRelay.
2. **Estrazione**: `merge_keys` pesate += `PSP_NUMBOL` (config.yaml + config_backfill.yaml) e/o equivalente in DataRelay.
3. **Bronze/silver**: `PSP_NUMBOL` in chiave bronze **solo insieme** a una regola che scelga lo **stato della pesata visto
   dal legacy** (non "bolla presente nel dettaglio": col re-merge di ottobre ha lasciato passare stati intermedi →
   +0,009% UF). Candidata: preferire le righe con `PSP_DATA_ESTRAZIONE_DWH` valorizzato (= consumate dall'ODI), ultima
   versione; fallback ultimo snapshot. Da validare sul dato prima di adottarla.
4. **Storico**: ri-estrazione read-only delle pesate set/ott senza dedup → ri-landing → rebuild bronze→gold → quadratura.
5. **Causa B**: classificare le righe solo-gold (pesate con timbro ODI NULL? confine data della quadratura?) e
   replicare la regola che ne esce.
6. **Causa C**: analizzare i 54 casi di bolla diversa (timing del consumo ODI vs nostro snapshot).

## Verifica
Quadratura set + ott: copertura 100%, `UF_GOLD_TOT = UF_ODI_TOT` (guardia di ACT_9037), 0 duplicati, multi-bolla
gold = ODI (ott: 88), 4 misure 0,0%.

## Sviluppo (diario)
- 2026-10-29 · Aperta. Causa individuata (dedup estrattore). Accesso Oracle diretto da Claude bloccato dal
  classificatore permessi → verifica punto 1 preparata come script per l'utente.

- 2026-10-29 (VPN, Oracle sola lettura autorizzata dall'utente) · **Causa A confermata, anche in produzione.**
  Oracle ha le 2e pesate (97696459: …558/UF72 + …559/UF12; 97699217: 84036 + 84038; 95134009: 18024 + 18025,
  stesso timbro ODI). Sui file **DataRelay** 28-29/10: delle 57 pesate multi-bolla Oracle (data-bolla ≥25/10) ne
  arrivano 20, **una per coppia** → DataRelay replica la stessa dedup (etichetta+data-bolla). Le pesate si perdono ogni giorno.
- 2026-10-29 · **Prova numerica** (temporanea, poi RESTORE): inserite in bronze le 324 pesate multi-bolla presenti in
  Oracle e assenti dal bronze (da 01/08) + rebuild v2.3.0. Set: copertura 99,979%→**99,990%**, UF −0,010%→**−0,002%**;
  ott: 99,983%→**99,991%**, UF −0,003%→**+0,004%**; 4 misure 0,0%, 0 duplicati; solo-ODI ott 100→52.
  Log: `LOGISTICO_DATA/datarelay_compare/proof_9038.log`.
- 2026-10-29 · **Residuo dopo la prova = altre due famiglie, preesistenti** (le 129 righe solo-gold di ottobre c'erano
  identiche anche prima della prova):
  - **B — righe che il legacy non ha** (ott: 69 righe = 5 carichi interi assenti in ODI; 46 righe = etichette assenti
    in 37 carichi presenti). Ipotesi `V_CHECK_PESATE` (il legacy marca le pesate incongruenti con
    `PSP_DATA_ESTRAZIONE_DWH = 1`) **non confermata**: in set/ott nessuna pesata ha il marcatore `1` (solo timbri data
    1,25M e NULL 35k). Indizio da verificare: nei 5 carichi quasi tutte le pesate sono timbrate dall'ODI e 1-4 hanno
    timbro NULL (mai consumate dal legacy); possibile anche effetto di confine data (es. carico 755068 timbrato il
    28/10, quadratura fino al 27). Testo `V_CARICO_ORDINARIO` letto da Oracle: `LOGISTICO_DATA/datarelay_compare/viste_legacy_carico.sql`.
  - **C — stato diverso della stessa pesata** (14 solo-gold + 40 solo-ODI con bolla diversa, es. noi `'1'`, ODI
    `34453`): il legacy consuma la pesata in un momento diverso dal nostro ultimo snapshot.

- 2026-10-29 · **Audit dedup estrazione (Oracle, sola lettura)**: la dedup per `merge_keys` scarta righe in 11/14 tabelle
  (tracciace178 21.168 = 22%, dettaglio_carr 14.737, sto_righe_carico 13.150 = 11%, storico_bolle 7.232, …; pesate 36
  nella finestra del 29/10). Da separare duplicati identici vs righe diverse (script pronto, query bloccata lato Claude).
  `sto_righe_carico` senza bolla/ordine in chiave è candidato per la causa C. Nota tecnica per DataRelay (fix per tabella
  + vincolo di sequenza col bronze): `LOGISTICO_DATA/datarelay_compare/NOTA_DataRelay_dedup_merge_keys.md`.

- 2026-10-30 · **Richiesta utente: criteri del legacy fino al 100%, reversibile.** Criteri ricavati dalle fonti
  (`V_CARICO_ORDINARIO` letta da Oracle → `viste_legacy_carico.sql`; WL2→T_CARICO `02. ESTRAI CARICHI`; replica
  `replica_carichi3`):
  - grana F_CARICO = output di `V_CARICO_ORDINARIO` (i `MIN(ROWID)` di WL3/WL4 servono solo a CEIL/FLOOR di QTA_ORD_FORN,
    non deduplicano); join t⋈r su (sito, carico, data, **ordine**), p⋈r su (sito, carico, **bolla**, ordine,
    radice+variante = MSI), **nessuna riconciliazione** (ACT_9035 compensava righe perse in estrazione);
  - il legacy elabora per giro solo testate/pesate **pendenti** e poi le timbra → criterio dato: **pesata inclusa solo
    se timbrata** (`PSP_DATA_ESTRAZIONE_DWH` = timbro data, stesso giorno della testata). Verifica ott: 601.285 stesso
    giorno, 0 giorni diversi, **4.028 timbro NULL** (mai lette dal legacy = righe solo-gold). Gli snapshot pre-timbro
    (bolle placeholder) hanno timbro NULL → esclusi dallo stesso criterio.
  - Piano reversibile: (1) estrazione Oracle completa read-only (testate/righe/pesate carichi 25/08–31/10, no dedup) in
    tabelle ombra `bronze_dev.logistica._act9038_*`; (2) simulazione legacy in notebook separato + quadratura fino al
    100%; (3) porting nella catena con bookmark versioni Delta + coordinamento DataRelay. Nota: il criterio-timbro vale
    finché il legacy è acceso → in catena dietro parametro, con fallback per il post-spegnimento.

- 2026-10-30 · **Simulazione legacy in locale** (estrazione Oracle read-only completa: 127.843 testate, 1.166.945 righe,
  1.518.952 pesate, carichi 25/08–31/10; `V_CARICO_ORDINARIO` alla lettera; script `LOGISTICO_DATA/legacy9038/sim_local.py`;
  il caricamento su dev è stato bloccato dal classificatore → simulazione fatta sul PC, nessun dato spostato).
  Set+ott (1–27/10): **copertura 99,994%, 0 chiavi con misure diverse**, UF +0,001%; solo-ODI 78, solo-sim 148 su
  1.287.801. Oracle in Logistix: **nessuna PK/UK** su STO_TES_CARICHI, STO_RIGHE_CARICO, PESATE. Residuo classificato
  (`diff_classificato.csv`):
  - **B — etichette rinumerate dopo il consumo** (78 coppie, = tutte le solo-ODI): stessa pesata, numero etichetta
    cambiato in Logistix dopo il timbro (es. carico 233206 lfqx: ODI 96840676, oggi 96841694). Il legacy congela lo
    stato al consumo. Regola candidata in catena: escludere le pesate viste per la prima volta (`_bronze_insert_ts`) dopo
    il giorno del loro timbro.
  - **A — riferimento ODI indietro** (41): carichi timbrati dopo l'estrazione dei file ODI (28/10 20:24), es. 689640
    timbrato 29/10 06:49 → rigenerare il riferimento ODI dei giorni finali (`scripts/quadratura/extract_f_carico.py`).
  - **C — carichi letti dal legacy ma assenti in CDT_DW** (29 righe, 4 carichi: 532421, 512216, 1038135, 23832) →
    probabile scarto CDT_SA in `E_CARICO`; verifica `LOGISTICO_DATA/legacy9038/check_e_carico.py` (da lanciare
    dall'utente: lettura bloccata dal classificatore).
  Il criterio del timbro nella simulazione è neutro (Oracle letto ora = tutto già timbrato); in catena serve perché
  DataRelay estrae prima del giro legacy.

- 2026-10-30 · **Famiglia C confermata = scarti legacy**: tutte le 29 righe dei 4 carichi sono in `CDT_SA.E_CARICO`
  con `ERR_ID = 210103` (`check_e_carico.txt`). Ipotesi "variante articolo assente in anagrafica" **smentita** (231.014
  righe accettate dal legacy hanno varianti assenti dalla nostra `lu_art_unita_logistica`: il legacy usa le sue S_*).
  Regola esatta da leggere in Oracle: `check_err_210103.py` (dizionario errori + `all_source` che assegna 210103).
  Riferimento ODI 20-29/10 da rigenerare: il primo lancio è fallito (`py -3` senza oracledb → usare `python`).

- 2026-10-30 · **Residuo spiegato al 100%** (rif. ODI rigenerato 20-29/10; set + 1-28/10, 1.318.009 righe legacy):
  1.317.929 identiche (chiave+misure), 0 misure diverse, UF +0,0005%. Residuo = **80 etichette rinumerate** (160 righe,
  B) + **29 scarti ERRART** (C). Famiglia A (41) era il riferimento ODI vecchio: sparita.
  - `210103` = `ERRART` (articolo non trovato) in `CDT_SA.LOAD_F_CARICO_STEP1` (OWB); altri codici: 210101 doppi,
    210102 sito, 210104 fornitore, 210106 modello peso, 210107 affidabilità, 210108 fascia, 210109 vettore. Tabella
    di lookup articolo da leggere: `check_errart_lookup.py`.
  - Rinumerate: il nostro bronze ha la versione vecchia (96840676, vista 19/10 05:31, timbro NULL = prima del giro
    legacy 07:13) e la nuova (96841694, vista 20/10). **Regola legacy per la catena**: pesata inclusa se vista per la
    prima volta entro il giorno di consumo (timbro) della sua testata. Copre rinumerate e pesate tardive.

- 2026-10-30 · ERRART: il body di `LOAD_F_CARICO_STEP1` non è leggibile con la nostra utenza (all_source = solo spec).
  Ipotesi "coppia radice/variante assente in `CDT_DW.L_ART_VAR_LOGIS`" **smentita**: le 4 coppie scartate esistono
  (859.375 righe scaricate in `legacy9038/l_art_var_logis.parquet`; simulazione con la regola = 0 righe scartate).
  Ipotesi in verifica: variante creata in anagrafica DOPO il caricamento del carico → `check_l_art_var_logis_date.py`.

- 2026-10-30 · **Fonte ritrovata (era stata persa nel contesto)**: `errore f carico.txt` (Desktop, mapping CDT_SA del
  ramo doppi 210101) mostra il lookup articolo di `LOAD_F_CARICO_STEP1`: staging `C$_6E_CARICO` di un'anagrafica
  varianti **storicizzata**, `ART_RADICE_COD`+`ART_VAR_LOGIS_COD` con `GIORNO_CARICO_ID BETWEEN ART_ST_DATA_INIZ AND
  ART_ST_DATA_FINE` → ERRART = nessuna versione della variante valida alla data del carico. `CDT_DW_SP_LOAD_F_CARICO_ODI`
  marca `CARICO_INCOMPLETO_FLAG=1` sulle chiavi (sito,giorno,doc,ordine) presenti in `E_CARICO`. La decisione
  "niente varianti storicizzate" (07/08) riguarda le colonne esposte, non questo scarto. Verifica + download tabella:
  `check_art_storicizzata.py`.

- 2026-10-30 · **ERRART chiuso**: anagrafica `CDT_DW.L_ART_VAR_LOGIS_ST` (staging `C$_0ART_2` scaricata, 3.403.983
  righe → `legacy9038/art_storicizzata.parquet`). Le 4 varianti scartate sono valide dal **giorno dopo** il carico
  (es. 4606837/6: carico 26/10, valida dal 27/10). Regola in simulazione = `giorno carico BETWEEN ART_ST_DATA_INIZ AND
  ART_ST_DATA_FINE` → scarta **esattamente 29 righe**.
  **Simulazione completa (set + 1-28/10)**: righe 1.318.009 = 1.318.009; UF 355.469.559,941 = ODI; QTA 341.090.154 = ODI;
  0 misure diverse; residuo solo **80 etichette rinumerate** (stessa pesata/misure, numero etichetta letto oggi da
  Oracle) → in catena le risolve la regola "pesata vista entro il giorno di consumo del carico" (verificato sul bronze).

- 2026-10-30 · **Specifica legacy consolidata** dopo rilettura integrale delle fonti (legacy Desktop + documenti di
  progetto + codice): [spec_legacy_f_carico.md](../spec_legacy_f_carico.md) — riferimento per il porting. Nuove regole
  verificate sul testo: testata timbrata solo se ha pesate in coda (replica 20220228, R 611-613); `WL1_PESATE` = pesate in
  coda agganciate alle righe (R 919-940), le non agganciate vengono timbrate e perse (R 966-967). Marcatore incongruenza
  `= 1` mai presente in set-ott (pesate 1.518.952 timbrate; testate 4.652 a `0` = senza pesate in coda).

- 2026-10-30 · **Gold dev vs legacy, riga per riga (ottobre 1-28)** su richiesta dell'utente ("se il legacy ha un valore deve
  esserci anche qui, salvo spiegazione riga per riga"). Trovato e **recuperato** un buco del 28/10 (26 mila etichette): il
  file del 28 riscritto da DataRelay alle 20:35 non è mai arrivato al silver per il watermark incrementale ([[LL-041]];
  recupero con `process_from`, notebook deployati, bookmark versioni). Dopo il recupero: **633.080 etichette identiche su
  633.198**, residuo 219 righe **tutte spiegate con prova** (`LOGISTICO_DATA/legacy9038/spiegazione_residuo_ott_FINALE.csv`):
  A 65 pesate perse in estrazione · B 16 righe dettaglio perse in estrazione · C 33 multi-bolla collassate da silver_pesate
  v2.2.0 (corretto da ACT_9037) · G1 28 scarti ERRART · R 49 etichette create/rinumerate dopo il consumo (5 contate due
  volte dal recupero storico ACT_9035) · D 28 pesate cancellate in Logistix prima del consumo (non propaghiamo le
  cancellazioni). 0 non spiegate. Ogni famiglia ha la sua correzione nella colonna `correzione` del file.

- 2026-10-30 · **Disegno implementativo (approvato dall'utente: "procedi, se serve ricarica tutto")** — sostituisce le
  correzioni puntuali ACT_9033/9035/9037 con lo **stato del carico al giro legacy**:
  1. **Bronze** testate/righe/pesate: chiave = identità completa della riga (pesate: sito, etichetta, bolla, carico;
     righe: sito, carico, data, ordine, MSI, bolla; testate: sito, carico, data, ordine, magazzino), dedup della sorgente
     sulla chiave prima del MERGE (pronti a landing senza dedup), colonne `_first_seen_date` (all'insert, mai aggiornata)
     e `_last_seen_date` (aggiornata a ogni giro in cui la riga è in landing, anche se invariata).
  2. **Silver** pulite: stessa chiave, propagano `_first_seen_date`/`_last_seen_date` e i timbri `*_DATA_ESTRAZIONE_DWH`.
  3. **silver_prep_carico** = `V_CARICO_ORDINARIO` ([spec](../spec_legacy_f_carico.md) R-2.x): per ogni carico D = giorno del
     timbro della testata; righe/pesate del carico presenti al giro = `_first_seen_date ≤ D ≤ _last_seen_date`; join t⋈r
     (sito, carico, data, ordine), p⋈r (sito, carico, bolla, ordine, MSI); niente riconciliazione; carichi non ancora
     timbrati esclusi (parametro per il dopo-spegnimento del legacy).
  4. **ERRART**: scarto se nessuna versione di `L_ART_VAR_LOGIS_ST` è valida al giorno del carico (lookup CDT_DW da
     aggiungere all'estrazione delle anagrafiche CDT_DW).
  5. **Storico set-ott**: bronze ricaricato giorno per giorno dalla landing + integrazione dall'estrazione Oracle delle righe
     mai arrivate in landing (A/B), con prima/ultima vista = giorno di consumo; poi silver full refresh, prep, gold,
     quadratura + riconciliazione riga per riga. Reversibile: bookmark versioni Delta prima di ogni passo.

- 2026-10-30 · **Codice pronto** (branch `feat/act-9039-rimozione-misure-derivate`, commit 21820b7 + 8b9858e): bronze con
  chiave completa e giorni di vista, silver allineati, `silver_prep_carico` v3.0.0, notebook di recupero
  `backfill_act9038_ricarica_bronze_da_landing` / `backfill_act9038_integra_da_oracle`. Test locali 64/64.
  **Bloccato**: il caricamento su dev dei dati Oracle (tabelle `_act9038_*` e `condiviso.l_art_var_logis_st`) è stato
  fermato dal controllo permessi per tutta la sessione → lo esegue l'utente (`LOGISTICO_DATA/legacy9038/load_shadow_tables.py`
  + `carica_art_storicizzata.py`). Poi `esegui_ricarica_act9038.py` (bookmark → ricarica → integra → silver FR → prep → gold →
  quadratura); ritorno: `ripristina_act9038.py`. Vincoli: dopo il ricaricamento i job schedulati col codice vecchio non sono
  compatibili (chiave bronze nuova) → rilascio nello stesso giro o ripristino prima delle 07:00. ERRART in giornaliero richiede
  `L_ART_VAR_LOGIS_ST` estratta ogni giorno (oggi tabella statica: rischio di scartare varianti create dopo il 30/10).
- 2026-10-30 sera · **rilascio deciso dall'utente** ("fai il rilascio"): merge PR #45 → split multi-repo → GitLab
  (workflows + lib per `acceptance.py`) → `deploy_dev` → wheel ricaricato sul Volume. Protezione ERRART per la tabella
  statica (`silver_prep_carico` v3.3.0): lo scarto si applica solo ai carichi con data ≤ ultimo aggiornamento della
  tabella varianti (`DESCRIBE DETAIL … lastModified`); i carichi successivi non vengono scartati finché la tabella non è
  estratta ogni giorno. Settembre e 1-28 ottobre invariati (data ≤ 30/10).

## Esito
**2026-11-05 — giro M2 di DataRelay e lacuna 31/10–04/11.** DataRelay ha tolto la deduplica sulle 3 tabelle dei carichi e,
per il solo giro del 05/11, ha allargato la finestra dei timbri a 6 giorni (report
`Extractor_Relay/docs/report/REPORT_giro_2026-11-05_M2.md`: 0 righe scartate su 19 siti). Quadratura 29/10–03/11 vs
CDT_DW: 31/10, 1/11, 2/11 e 3/11 al 100% (righe, UF, QTA; 3 etichette rinumerate); mancavano 7 righe il 29/10 e 658 il
30/10, tutte su carichi timbrati il 31/10. **Causa**: `_P` (fotografia dopo il giro) era calcolata come D+1, ma dal
31/10 al 04/11 il bronze non ha fotografie; le righe di dettaglio definitive (bolla reale) compaiono per la prima volta
il 05/11 e restavano fuori. **Correzione** (`silver_prep_carico` v3.4.0): `_P` = primo giorno di landing effettivamente
caricato dopo D (prima vista di testate e pesate arrivate dalla landing, non da Oracle); prima del primo giorno di
landing (settembre, ricostruito da Oracle) resta D+1. Con fotografie continue il risultato è identico a prima.

**2026-11-04 — rilasciato.** PR #45 unita (b39a07f) → GitHub (lib 141cd75, workflows d4006ba, documentation
340658c) → GitLab solo `main` (workflows v0.1.21 63bcff1, lib v1.0.9 b00a8e5) → `deploy_dev` verificato (commit
63bcff1 nel `metadata.json` del bundle, `silver_prep_carico` v3.3.0) → wheel ricaricato sul Volume (copia precedente in
`_wheels/backup/…_20261104_prima_ACT9039.whl`). Dal 31/10 al 04/11 il job carichi era fallito ogni mattina sui task bronze
(`DELTA_MERGE_UNRESOLVED_EXPRESSION … _first_seen_date`: codice vecchio sul bronze ricaricato) senza scrivere nulla:
bronze/silver/gold sono rimasti allo stato quadrato del 30/10. **Recupero dei 5 giorni rinviato per decisione
dell'utente** finché DataRelay non smette di deduplicare (la landing di quei giorni ha ancora la perdita delle 2e pesate):
istruzioni a DataRelay in `LOGISTICO_DATA/datarelay_compare/ISTRUZIONI_DataRelay_2026-11-04.md` (M2 = segnale nostro).

**2026-10-30 — F_CARICO gold dev quadrato con CDT_DW su settembre e 1-28 ottobre** (7 giri di ricaricamento con
correzioni successive; codice sul branch `feat/act-9039-rimozione-misure-derivate`, ultimo commit 9f538ae):

| | Settembre | Ottobre 1-28 |
|---|---|---|
| Righe gold = legacy | 684.717 = 684.717 | 633.292 = 633.292 |
| UF, QTA, PES, VOL | identiche | identiche |
| Chiavi identiche | 684.675 | 633.283 |
| Differenze | 42 coppie | 9 coppie |

Le 51 coppie sono etichette **rinumerate in Logistix** dopo il giro legacy e prima che le vedessimo: stesso giorno,
sito, documento, bolla, UF e quantità, numero di etichetta diverso. Il numero vecchio non esiste più né in Oracle né in
landing (settembre non ha landing; a inizio ottobre il vecchio estrattore girava dopo il giro legacy) → non
ricostruibili. Elenco: `LOGISTICO_DATA/legacy9038/residuo_finale_rinumerate.csv`. 0 righe senza spiegazione.

Regole finali (`silver_prep_carico` v3.2 + `backfill_act9038_integra_da_oracle`): testata timbrata; righe "del giro" =
viste tra la fotografia prima e quella dopo il giro; pesate = timbrate nel giro del carico (gemelle rinumerate risolte);
storico integrato da Oracle (righe mai arrivate in landing, timbri, prima/ultima vista); ERRART; doppi.
Ripristino allo stato di stamattina: `ripristina_act9038.py` (segnalibro `bookmark_ricarica_act9038_ORIGINALE.json`).

**Prima del rilascio**: (1) i job schedulati col codice vecchio non sono compatibili col bronze ricaricato → rilascio
GitLab o ripristino prima della run delle 07:00 → **scelto il rilascio (30/10 sera)**; (2) `L_ART_VAR_LOGIS_ST` va
estratta ogni giorno (oggi copia fissa; nel frattempo ERRART limitato ai carichi fino all'ultimo aggiornamento della copia);
(3) DataRelay senza dedup (nota tecnica pronta) — finché resta, le famiglie A/B si ripresentano nei giorni nuovi.
