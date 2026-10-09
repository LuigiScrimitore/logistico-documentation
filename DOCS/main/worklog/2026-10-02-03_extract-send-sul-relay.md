---
data: 2026-10-02
titolo: "Extract+send sul relay: primo carico reale in logisticolanding (307 file, ~2,23 GB)"
autore: Francesco Foconi
push_monorepo: "PR dedicata (extract_and_send.sh + ACT/OP/README/worklog)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: []
op: [OP-INF-4, OP-07, OP-08]
---

## Contesto
Provisioning consegnato (01/10) + collaudo relay OK (02/10): canale `relay → AzCopy → logisticolanding`
validato. Siccome il relay `odisrvcno3` raggiunge **sia Oracle sia Azure**, si è verificato se può eseguire
**anche l'estrazione** (oggi gli estrattori girano in locale su Windows), così da unificare **extract + send**
on-prem sullo stesso host.

## Cosa è stato fatto
- **Prerequisiti verificati sul relay** (`odisrvcno3`, Ubuntu 26.04): Python **3.14.4**; `oracledb` in **THIN mode**
  contro **Oracle 19c** → **nessun Instant Client**; AzCopy 10.32.7; disco `/data/landing` ~467 GB liberi.
  Creato venv `/opt/landing/venv` + librerie `oracledb`/`pyyaml`/`python-dotenv`.
- **Nuovo orchestratore** `scripts/relay_azcopy/extract_and_send.sh`: carica le credenziali Oracle da un env file
  (600), **estrae** con i due script Python (`extract_oracle_to_landing.py` + `extract_cdtdw_lookups.py`) nella
  **staging** `/data/landing/staging/<env>/<sistema>/<sorgente>-landing/...`, poi **invia** riusando
  `upload_landing.sh <env> <sistema>` → AzCopy. Multi-env/sistema, `DRYRUN`, validazione token anti-injection,
  pre-flight. `run_date` **default = giorno di esecuzione** (`date +%F`), per lo scheduling giornaliero.
- **Setup sul relay**: app in `/opt/landing/app`, credenziali Oracle in `/opt/landing/conf/dev/logistico.oracle.env`
  (600, svc_landing), script in `/opt/landing/bin/`; fix ownership `svc_landing` su `/data/landing/staging/dev`
  (l'estrattore scrive i log in `output_dir.parent/logs`). Eseguito come **`svc_landing`** (utente che possiede la
  staging e legge il SAS).
- **DRY-RUN** validato (query, finestra lookback 3gg su julian_day, path `stat-landing/<tabella>/2026/10/01/...`
  corretti).
- **Primo carico REALE**: `extract_and_send.sh dev logistico 2026-10-01`, **tutti i sistemi** (logistix × 22 siti +
  stat + cdt_estr + track) **+ anagrafiche CDT_DW** → AzCopy **`Completed`: 307 file, ~2,23 GB, 0 Failed/0 Skipped**
  in `logisticolanding` (OP-07: nel container resta `<sorgente>-landing/...`, nessun prefisso `dev/logistico/`).
- **Schedulazione** (senza login): unit systemd `landing-extract-send.service` + `.timer` (oneshot come
  `svc_landing`, `OnCalendar=05:00`, `Persistent=true`; `run_date` default = oggi). Versionate in `scripts/relay_azcopy/`.
  NB: disattivare `landing-upload.timer` (solo-upload) per non duplicare l'invio.
- **Recap per esecuzione**: lo script scrive un **log completo** in `/var/log/landing/runs/extract_send_<ts>.log`
  e appende un **blocco riassuntivo** a `/var/log/landing/extract_send_recap.log` (esito estrazione `files/rows/errors`,
  esito AzCopy `Completed/file/GB`, durate, OK/KO) → storico consultabile senza seguire il run.

## Novità / decisione aperta (da coordinare con Luigi)
- **L'estrazione ora gira sul relay**, non solo sugli agenti ODI. È una **variante** rispetto all'architettura
  documentata nell'[[ACT_OP-INF-4]] (relay = "solo storage + sender"; estrazione sugli agenti RHEL6 per il lineage ODI).
  Il relay la esegue nativamente (Python 3.14 + oracledb thin + accesso Oracle/Azure).
- **Da decidere**: estrazione **sul relay** (più semplice, un solo host extract+send) **vs** sugli **agenti ODI**
  (lineage ODI, trigger forced-command già pronto). Possibile **ADR** dedicato. Non deciso qui.

## Note
- Il carico copre **solo il 1 ottobre** (delta del giorno, lookback 3). Lo **storico completo** resta la decisione
  separata: ri-estrazione backfill (`--from-date/--to-date` + eventuale `--ignore-odi-flag`) **vs** migrazione dal
  **Volume managed** (fonte affidabile, non soggetta al flag ODI).
- SAS **senza Delete**: eventuali rimozioni via utenze Contributor / lifecycle 220gg.

## Doc aggiornati
- `acts/ACT_OP-INF-4` (diario 2026-10-02 + follow-up), `05_open_points.md` (OP-INF-4), `scripts/relay_azcopy/README.md`
  (sezione "Estrazione sul relay + scheduling + recap"), worklog INDEX.
- Artefatti versionati in `scripts/relay_azcopy/`: `extract_and_send.sh`, `landing-extract-send.service`, `landing-extract-send.timer`.

## Prossimi passi
1. **Decisione estrazione** relay vs agenti ODI (+ eventuale ADR) con Luigi.
2. **Schedulazione** del giro giornaliero (timer systemd / cron; `run_date` default = oggi).
3. **Storico**: backfill vs migrazione dal Volume → popolare `logisticolanding`.
4. **Cutover**: ricreare `landing_dev.logistica.files` come Volume **external** stesso nome → flip `landing_mode=external`
   (Access Connector `ac-dev-logistico-00` / External Location `logisticolanding_dev` già pronti).
