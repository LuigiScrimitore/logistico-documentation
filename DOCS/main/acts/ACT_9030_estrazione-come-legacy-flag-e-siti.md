# ACT_9030 · Estrazione "come il legacy": selezione guidata dal flag ODI (sola lettura) + tutti i 19 siti Logistix

**Status**: in-progress
**Type**: ingestion / correttezza dati
**Origin**: verifica volumi bassi di ottobre (F_PREP_SPED 05/10 e 12/10, F_CARICO 12/10) contro CDT_DW
**Sprint**: trasversale (pre go-live)
**Fase / Wave**: cutover landing ([[ACT_OP-INF-4]])
**Created**: 2026-10-16   **Closed**: —   **Owner**: Francesco Foconi
**Dipende da**: Oracle sorgenti via db-link (`LOG_<sito>`, `STAT`), relay odi3 (`extract_and_send.sh`), bundle `workflows`
**ADR collegate**: [[ADR-0003]]   **Lezioni**: [[LL-006]], [[LL-038]]   **OP collegati**: OP-INF-4

## Contesto
Confronto giorno per giorno Gold dev vs `CDT_DW` (legacy, alimentato dall'ODI) dal 21/09 al 15/10:
- `F_PREP_SPED` per `GIORNO_PREL_INIZ_ID`: nei feriali normali il Gold ha il **90–97%** del legacy; **05/10 17%**,
  **12/10 47%**, sabati 38–42%, domenica 04/10 0%, molti giorni di settembre vicini a 0.
- `F_CARICO` per `GIORNO_CARICO_ID`: stabile al **26–30%** del legacy, **12/10 14%**.

Due cause indipendenti.

### Causa 1 — finestra sulle date sbagliate
L'estrattore (`scripts/landing_simulator/extract_oracle_to_landing.py`, `--lookback-days 3`) estrae
`[run_date−3, run_date]` sulla `date_column` di `config.yaml`, con il flag ODI ignorato fino al go-live
(`IGNORE_ODI_FLAG=1`). Per alcune tabelle quella data non è quella dell'evento:
- `storico_liste` → `LSPRL_DATA_ORDIN_NEG` (data **ordine**, non del prelievo);
- `pesate` → `PSP_DATABOLLA` (data **bolla fornitore**, non dello scarico).

Il run parte alle 06:00, prima del lavoro del giorno: un prelievo del giorno P viene visto solo dal run P+1, che copre
ordini fino a P−2. Prelievi del 12/10 nel legacy per ritardo ordine→prelievo: 0–1 gg 83.125 (Gold 83.005), 2 gg 198.392
(Gold 113.107), **3 gg 128.676 (Gold 0)**, ≥4 gg 6.806 (Gold 0). Su un mese di legacy (11,5 M righe) i prelievi entro
2 giorni dall'ordine sono il **91,7%**, entro 3 il 99,1%, entro 6 il 99,9%. Il lunedì (ordini di venerdì/sabato) perde
di più; il 05/10 mancavano anche le cartelle 04–06.

### Causa 2 — solo 5 siti su 19
La landing riceve **19 siti** Logistix (`lbvx lcax leax lfax lfmx lfqx lfvx lgax lgcx lgnx lgqx lgrx lgvx lgzx lonx losx
lslx lsmx lsvx`, = i db-link attivi in `config.yaml`; il legacy ne ha 18). Il parametro di job `siti` di
`landing_ingestion`, `carichi`, `giacenze`, `prep_sped` è fermo a `lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx`: di
questi ne esistono **5** (`lgax lgcx lcax lonx lslx`). Carichi, pesate, tracciabilità, carrellisti, giacenze e
anagrafiche Logistix sono quindi caricati per 5 siti: il 27% di `F_CARICO` vs legacy viene da qui (non dalla grana).
`LU_SITO` ha già 22 siti e la mappa alias (`get_sito_alias_map`, da `S_LOGISTIX`) li risolve tutti ([[ACT_9026]]).

## Come estrae il legacy (sorgenti PL/SQL sul Desktop, `1. LOGISTICO\`)
Nessuna finestra sulle date: parte da un documento "chiuso" non ancora estratto e prende tutto ciò che gli è collegato,
poi lo marca.
- **Logistix** (`replica_carichi3`, `F_CARICO F_PESATE\`): testate `STO_TES_CARICHI` con
  `NVL(STCAR_DATA_ESTRAZIONE_DWH,0)=0` → pesate e righe **di quei carichi**; poi scrive il flag. Valore del flag =
  **timbro data/ora dell'estrazione ODI** `YYYYMMDDHHMI` (es. `202610160647`); durante la lavorazione valori transitori
  (`0`, `11`). Verificato alla fonte (`@LOG_LGAX`, ultimi 15 gg): pesate con bolla dell'01/10 timbrate fino al 13/10
  (arrivi tardivi presi comunque). Stesso timbro su `TRACCIACE178`, `DETTAGLIO_CARR`, `CARTELLINO`, `ABB_TOLTI`,
  `IMBFMOVIM`.
- **STAT** (`package_replica_prep_sped_new.sql`): `TESTATE_BOLLE` con `TEBO_FLAG_ESTRAZIONE_DWH='N' AND TEBO_STATO='E'`
  (bolle emesse) → `UPDATE ... SET TEBO_FLAG_ESTRAZIONE_DWH='S', TEBO_DATA_ESTRAZIONE_DWH=<timbro>`; `STORICO_LISTE`
  **delle bolle selezionate** (sito, negozio, nro bolla, data bolla); `STORICO_RIEPILOGHI` dei riepiloghi di quelle liste.
  Il flag proprio di liste/bolle/riepiloghi è sempre NULL: la selezione passa dalle bolle.

## Obiettivo
1. **Siti**: tutti i job elaborano i 19 siti della landing (variabile unica del bundle).
2. **Estrazione** che riproduce la selezione del legacy **in sola lettura** (nessun UPDATE sulle sorgenti prima del
   go-live), così da non dipendere da finestre sulle date:
   - tabelle Logistix con flag: righe con flag "non ancora estratto" (NULL / `0` / transitori) **oppure** timbro
     `>= <run_date − N giorni>0000` (prese dall'ODI dopo il nostro run precedente; il run delle 06:00 precede l'ODI delle
     ~06:46). Le sovrapposizioni tra giorni sono innocue (bronze `DELTA_MERGE` sulla chiave);
   - righe carico (`STO_RIGHE_CARICO`, senza flag): quelle dei carichi selezionati;
   - STAT: bolle emesse selezionate come sopra (`TEBO_*`), poi liste, righe bolla e riepiloghi di quelle bolle;
   - recupero: lo stesso criterio con un timbro di partenza esplicito (es. dal 2026-10-01).
3. **Recupero** di ottobre (estrazione su odi3 + rilancio dei job con `process_from`) e nuovo confronto con CDT_DW.

## Disegno dell'estrattore (passo 3)
Profilo dei flag alla fonte su tutta la storia (`@LOG_LGAX`, `@STAT`, 16/10):
- `STO_TES_CARICHI`: 385 mila timbrate, **9.736 con flag `0` più vecchie di 30 giorni** (mai prese dall'ODI), 92 NULL
  recenti, 2 con `11`; le altre tabelle Logistix: solo poche centinaia di NULL recenti, il resto timbrato.
- `TESTATE_BOLLE`: stato `E` + flag `S` timbrate (4,7 M); stato `N` + flag `N` (42 mila, mai emesse, ignorate dal
  legacy); stato `F` con timbro in formato giuliano (ignorate dal legacy).

Nuova chiave per tabella in `config.yaml`, `selection` (se assente: comportamento attuale a finestra sulla data):
- `legacy_flag`: `(<in sospeso> AND <date_column> >= run_date − pending_days) OR <stamp_column> >= :stamp_from
  [AND < :stamp_to]`. "In sospeso" = `NVL(flag,0) < 100000000000` (NULL, `0`, transitori) oppure `pending_where`
  (es. `TEBO_STATO = 'E' AND TEBO_FLAG_ESTRAZIONE_DWH = 'N'`). La finestra di 30 giorni sui sospesi evita di rileggere
  ogni giorno le righe che l'ODI non prende mai.
- `parent`: `(<colonne figlio>) IN (SELECT <colonne padre> FROM <padre>@<stesso db-link> WHERE <selezione del padre>)`,
  ricorsivo (riepiloghi → liste → bolle).

| tabella | selezione |
|---|---|
| `sto_tes_carichi`, `pesate`, `tracciace178`, `dettaglio_carr`, `cartellino`, `abb_tolti`, `imbfmovim` | `legacy_flag` sul proprio flag |
| `sto_righe_carico` | `parent` → `sto_tes_carichi` (nro carico, magazzino) |
| `testate_bolle` | `legacy_flag` con `pending_where` stato `E` / flag `N`, timbro `TEBO_DATA_ESTRAZIONE_DWH` |
| `storico_liste`, `storico_bolle` | `parent` → `testate_bolle` (sito, negozio, nro bolla, data bolla) |
| `storico_riepiloghi` | `parent` → `storico_liste` (sito, nro riepilogo, negozio) |

Opzioni CLI: `--stamp-lookback-days` (default 2: il run delle 06:00 prende ciò che l'ODI delle ~06:46 ha timbrato dopo il
run precedente, con margine), `--stamp-from` / `--stamp-to` (recupero e verifica), `--pending-days` (default 30).
Sul relay: variabile `EXTRACT_EXTRA` in `extract_and_send.sh` per passare queste opzioni a mano (recupero); il comando
del job ODI non cambia. Restano a finestra sulla data `track/spedizioni` (nessun flag) e le tabelle `full`/`snapshot`.

## Piano
1. Doc (questo ACT + worklog per ogni passo).
2. Siti: variabile `siti_logistix` in `databricks.yml` (19 siti) usata dai 4 job; rilascio `workflows`. Da quel momento
   i run giornalieri coprono 19 siti; lo storico degli altri 14 si carica con il recupero del passo 4.
3. Estrattore: modalità di selezione "come il legacy" per tabella in `config.yaml`, prova in locale contro Oracle
   (conteggi per tabella vs legacy), PR; copia su odi3 (utente).
4. Recupero unico (passo 2 + 3 insieme): estrazione di recupero su odi3, rilancio dei giorni in ordine crescente e
   chiusura con `process_from` (procedura del worklog 2026-10-15-03), confronto giorno per giorno con CDT_DW.
5. **Al go-live** (ODI spento): l'estrattore deve scrivere lui il flag come l'ODI (permessi di UPDATE sulle sorgenti),
   altrimenti le righe "non ancora estratte" crescono senza limite. Da aggiungere ai passi di go-live con
   `IGNORE_ODI_FLAG=0` e `schedule_pause_status` prod.

## Diario
- 2026-10-16 · Analisi e confronto con CDT_DW (sopra). Worklog 2026-10-16-02 (siti).

## Esito
_(in corso)_
