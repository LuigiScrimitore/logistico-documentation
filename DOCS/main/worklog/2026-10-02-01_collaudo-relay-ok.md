---
data: 2026-10-02
titolo: Collaudo relay OK — upload reale verificato su logisticolanding
autore: Luigi Scrimitore
push_monorepo: 235474c
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: []
op: [OP-INF-4, OP-07]
---

## Cosa e' stato fatto
- **Collaudo end-to-end del relay superato** con il SAS consegnato da Reply:
  - SAS estratto dal JSON (`python3`) e posato in `/opt/landing/secrets/dev/logistico.sas` (600, svc_landing); JSON
    rimosso dal relay (segreto).
  - Creati `conf/dev/logistico.conf` + `staging/dev/logistico`; **ri-deployato** `upload_landing.sh` (versione
    multi-env, verificata: 0 CRLF, token parse, sintassi).
  - `upload_landing.sh dev logistico` → AzCopy **`Final Job Status: Completed`**, `1 Done / 0 Failed`, **`exit=0`**.
  - `azcopy list` → blob **`_smoketest/2026/10/01/check.txt`** **senza** prefisso `dev/logistico/` → convenzione path
    confermata (**OP-07**: nel container resta solo `<sorgente>-landing/...`).

## Novita'
- Canale **relay → Azure Blob operativo**. `Blocco` OP-INF-4: nessuno lato Reply (resta lavoro nostro).
- Il file `_smoketest` resta nel container (SAS **senza `Delete`**): rimozione via Storage Explorer (utenza
  Contributor) o lo scarta il lifecycle 220gg.

## Doc aggiornati
- `05_open_points.md` (OP-INF-4: collaudo OK + Status), `acts/ACT_OP-INF-4` (diario + Status + Verifica).

## Stato dopo il push / prossimi passi
- Trasporto landing **validato end-to-end dal relay**. Prossimi: **trigger E2E da ODI** (deploy
  `trigger_landing_upload.sh` su .211/.212 + test `OdiOSCommand`); **migrazione storico Volume→logisticolanding** +
  ricreazione external Volume stesso nome (poi flip `landing_mode=external`); industrializzazione estrazione ODI.
