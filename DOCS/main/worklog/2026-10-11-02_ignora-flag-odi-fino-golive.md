---
data: 2026-10-11
titolo: "Estrazione giornaliera: ignorato il flag CDC dell'ODI legacy fino al go-live (eccezione imbfmovim) + job ODI alle 05:00"
autore: Francesco Foconi
push_monorepo: "PR #25 @c5cd120 (estrattore + extract_and_send.sh + doc) + PR esito"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: [LL-024]
op: [OP-INF-4, OP-08]
---

## Contesto
L'estrattore, sulle tabelle delta, combina la finestra data **[run_date − 3, run_date]** (estremi inclusi) con il
flag CDC dell'ODI legacy `NVL(<tab>_DATA_ESTRAZIONE_DWH, 0) = 0`, cioè "record non ancora estratto dall'ODI".
Finché l'ODI legacy gira in produzione (job alle 06:30), i record che ha già estratto escono dalla nostra
estrazione **anche se sono dentro la finestra**: il lookback non li recupera.

Tabelle col flag: Logistix `sto_tes_carichi`, `pesate`, `tracciace178`, `dettaglio_carr`, `cartellino`,
`imbfmovim`, `abb_tolti`; STAT `storico_bolle`, `storico_riepiloghi`, `testate_bolle`.
Senza flag (solo finestra): `sto_righe_carico`, `storico_liste`, TRACK `spedizioni`.

Evidenze: [[LL-024]] (`lgcx/pesate` 01-07 ago: 0 righe col flag, 1.065 senza; seed 1,19 M righe col flag contro
3,65 M senza). Nel container `logisticolanding`: testate carichi (flag) 50-115 KB/giorno contro righe carico
(senza flag) 14-20 MB/giorno.

## Decisione
Fino al **go-live in produzione** (spegnimento del vecchio flusso ODI) l'estrazione giornaliera **ignora il flag**:
fa fede solo la finestra data. Dopo il go-live il flag non verrà più valorizzato da nessuno, quindi diventa
ininfluente; la variabile si potrà comunque riportare a 0.

Spostare solo l'orario prima delle 06:30 **non bastava**: i record creati tra il nostro giro e le 06:30 vengono
marcati dall'ODI legacy prima del giro successivo e si perdono ogni giorno; e un giro saltato non si recupera.

**Eccezione `imbfmovim`**: è l'unica tabella delta senza colonna data, filtrata solo dal flag. Misura su Oracle
(19 siti attivi): **2.308.772 righe** di storico contro **5.481** con flag=0. Senza flag verrebbe riletta per intero
ogni giorno (~2,3 M righe/giorno, oltre la stima di 40-50 GB di retention concordata con Reply). Quindi per le
tabelle **senza finestra data** il flag resta applicato anche con `--ignore-odi-flag`.
Aperto: trovare una colonna data utilizzabile per `imbfmovim`.

## Cosa
- `extract_oracle_to_landing.py`: con `--ignore-odi-flag` il flag viene ignorato **solo** sulle tabelle in cui è
  applicata la finestra data; sulle tabelle senza `date_column` resta (log di avviso).
- `extract_and_send.sh`: nuova variabile `IGNORE_ODI_FLAG` (**default 1** fino al go-live) che passa
  `--ignore-odi-flag` all'estrattore principale; valore riportato nel log di avvio e nel recap.
- Job ODI su odi3: resta schedulato alle **06:00** ora italiana (04:00 UTC su odi3, data corretta); finisce verso le
  06:13. Con il flag ignorato l'orario non è più legato a quello dell'ODI legacy (si era valutato di anticiparlo alle 05:00).
- Deploy su odi3: copiare `extract_and_send.sh` in `/opt/landing/bin/`, `extract_oracle_to_landing.py` e
  `config.yaml` in `/opt/landing/app/scripts/landing_simulator/` (insieme arrivano anche il fix
  `SSH_ORIGINAL_COMMAND` e i siti spenti della PR #20).

## Costo
Ogni giro riestrae 4 giorni sulle tabelle delta: righe ripetute tra giorni consecutivi, deduplicate dal merge del
bronze sulle chiavi (nessun doppione a valle).

## Esito (2026-10-11/12) — IN PRODUZIONE SU ODI3
- **Deploy su odi3**: copiati `extract_and_send.sh` (`/opt/landing/bin/`, root 755), `extract_oracle_to_landing.py`
  e `config.yaml` (`/opt/landing/app/scripts/landing_simulator/`, svc_landing), con backup `.bak`. Il `diff` del
  config ha mostrato solo il commento sui siti spenti: su odi3 laix/lfsx/lgsx erano **già** esclusi.
- **Prova `DRYRUN=1`** su odi3: `ignore_odi_flag=1`; flag IGNORATO su sto_tes_carichi, pesate, tracciace178,
  dettaglio_carr, cartellino, abb_tolti; MANTENUTO su imbfmovim.
- **Recupero dei giorni già caricati** (01, 02, 03, 07, 08, 10, 11 ottobre), **solo tabelle col flag** (per non
  toccare le `catena`): estrazione OK (`errors=0`), invio AzCopy 763 file / 0 falliti / 8,3 GB. Verifica sul
  container, KB per giorno prima → dopo: `pesate` 0-4.200 → 11.800-28.300; `sto_tes_carichi` 50-115 → 925-1.450;
  `tracciace178` 0-161 → 6.000-9.300; `dettaglio_carr` 0-83 → 7.700-12.100; STAT `testate_bolle` 9-110 →
  1.765-2.615. STAT `storico_bolle` e `storico_riepiloghi` invariate (lì il flag non tagliava).
  I giorni mancanti (04-06, 09) sono coperti dalla finestra di 4 giorni dei giorni successivi.
- **Giacenze del 02/10**: rimosse dalla staging di odi3 le cartelle `catena`/`catena_esterni` di `2026/10/02`
  (fotografia del 11/10 con data sbagliata). Nel container restano 21 file da cancellare da Storage Explorer
  (utenza Contributor; il SAS non ha Delete).
- **Primo giro schedulato (2026-10-12, 06:00)**: file scritti alle 06:13, tabelle col flag piene (`pesate` 15 siti,
  `sto_tes_carichi` 18, `dettaglio_carr` 18, `tracciace178` 17), `imbfmovim` col flag, `catena` del giorno giusto.
  Volumi più bassi della media attesi: finestra = ven+sab+dom interi + lunedì fino alle 06:00 (es. `pesate` 6,0 MB
  contro 11,8 MB della partizione 11/10, che conteneva anche il giovedì).
- Nota operativa: con due `sudo` in sequenza e un'estrazione più lunga di 15 minuti, il secondo `sudo` richiede di
  nuovo la password e va in timeout. Lanciare l'invio come comando separato.

## Prossimi passi
1. Cancellare dal container le 21 cartelle `catena*/2026/10/02` (azcopy su odi3 con login dell'utenza Contributor).
2. Al go-live: `IGNORE_ODI_FLAG=0` (o rimozione) e verifica.
3. `imbfmovim`: individuare una colonna data per togliere anche lì la dipendenza dal flag.
