---
data: 2026-10-01
titolo: Convenzione path <env>/<sistema> + sender e trigger ODI multi-ambiente
autore: Luigi Scrimitore
push_monorepo: 6d13af3
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: [OP-07, OP-INF-4]
---

## Cosa e' stato fatto
- **Definita la convenzione path della staging** sul relay, generica e riusabile oltre il logistico:
  `/data/landing/staging/<env>/<sistema>/<sorgente>-landing/<tabella>/YYYY/MM/DD/<file>`.
  - `<env>` = ambiente di destinazione (`dev` ora, `prod` in futuro); `staging` resta il root NFS già registrato,
    l'ambiente è un livello **sotto** (niente rename, zero impatto su export/fstab/mount/unit).
  - `<sistema>` = dominio applicativo (`logistico` ora, altri domani).
  - I livelli `<env>/<sistema>/` **non** finiscono nel container: si copia il *contenuto* → dentro `logisticolanding`
    resta `<sorgente>-landing/...` (**OP-07 invariato**).
- **Sender relay `upload_landing.sh` reso multi-env/multi-sistema**: legge `<env> <sistema>` da
  `$SSH_ORIGINAL_COMMAND` (o da argomenti per test), valida i token (`^[a-z0-9-]+$`, anti path-traversal/injection),
  risolve `(env,sistema) → (container, SAS)` via `/opt/landing/conf/<env>/<sistema>.conf`, ripristina la guardia
  `[ -r SAS ]`, copia con `azcopy copy "staging/<env>/<sistema>/*"`.
- **Script lato ODI `trigger_landing_upload.sh`**: è ciò che l'`OdiOSCommand` lancia sugli agenti (odisrvcno1/2, in
  balance); fa solo l'`ssh` verso il relay passando `"<env> <sistema>"` (il forced command esegue solo lo script).

## Novita'
- **Aggiungere un ambiente o un sistema = nuova sub-folder staging + nuovo file conf, zero modifiche agli script.**
- `.gitattributes`: `*.sh` e gli artefatti del relay (`.service`/`.timer`/`conf.example/**`) forzati a **LF**
  (girano su Linux: un CRLF romperebbe shebang/`set`). Parsing token verificato (smoke test: injection → REJECT).
- `landing-upload.service` (fallback systemd) → `ExecStart=... dev logistico`.

## Doc aggiornati
- `05_open_points.md` (OP-INF-4: "Convenzione path & sender multi-env/multi-sistema"), `scripts/relay_azcopy/README.md`
  (architettura, convenzione path, attivazione, sezione trigger con script ODI), `conf.example/dev/logistico.conf`.

## Stato dopo il push / prossimi passi
- Trigger A validato; impianto di invio ora **multi-env/multi-sistema**. Resta **gated dal SAS di Reply**: posa SAS in
  `/opt/landing/secrets/dev/logistico.sas` + ri-deploy `upload_landing.sh` dal repo + creazione `staging/dev/logistico`
  e `conf/dev/logistico.conf` → test upload reale. Poi: migrazione storico Volume→logisticolanding + external Volume
  stesso nome; industrializzazione estrazione ODI (mapping che scrivono sulla staging NFS col layout `dev/logistico/...`).
