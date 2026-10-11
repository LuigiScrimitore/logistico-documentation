---
data: 2026-10-11
titolo: "Estrazione giornaliera: ignorato il flag CDC dell'ODI legacy fino al go-live (eccezione imbfmovim) + job ODI alle 05:00"
autore: Francesco Foconi
push_monorepo: "PR dedicata (estrattore + extract_and_send.sh + doc)"
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
- Job ODI su odi3: schedulato alle **05:00** ora italiana (03:00 UTC su odi3, data corretta). Con il flag ignorato
  l'orario non è più legato a quello dell'ODI legacy.
- Deploy su odi3: copiare `extract_and_send.sh` in `/opt/landing/bin/`, `extract_oracle_to_landing.py` e
  `config.yaml` in `/opt/landing/app/scripts/landing_simulator/` (insieme arrivano anche il fix
  `SSH_ORIGINAL_COMMAND` e i siti spenti della PR #20).

## Costo
Ogni giro riestrae 4 giorni sulle tabelle delta: righe ripetute tra giorni consecutivi, deduplicate dal merge del
bronze sulle chiavi (nessun doppione a valle).

## Prossimi passi
1. Deploy dei 3 file su odi3 e prova `DRYRUN=1`, poi spostamento dello schedule ODI alle 05:00.
2. Al go-live: `IGNORE_ODI_FLAG=0` (o rimozione) e verifica.
3. `imbfmovim`: individuare una colonna data per togliere anche lì la dipendenza dal flag.
