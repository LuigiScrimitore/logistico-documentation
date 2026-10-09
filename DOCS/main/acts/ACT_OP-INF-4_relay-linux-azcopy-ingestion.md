# ACT_OP-INF-4 · Relay Linux `odisrvcno3` + trigger ODI per ingestion landing via AzCopy

**Status**: in-progress (provisioning consegnato + **collaudo relay OK** 2026-10-02; aperti: trigger E2E ODI, migrazione storico)
**Type**: infra
**Origin**: OP-INF-4 (host di extract & send verso landing)
**fuori-sprint**: open-point (emergente infra)
**Fase / Wave**: FASE 0 — Landing & Ingestion
**Gg (stima)**: ~3 (provisioning + trigger + convenzione) · **Blocco**: nessuno (collaudo + migrazione storico = nostro)
**Created**: 2026-09-25   **Closed**: —   **Owner**: team (ODI trasversale)
**Dipende da**: [[ADR-0023]] (trasporto AzCopy), [[ACT_9012]] (analisi SFTP vs Blob), provisioning Azure (Reply)
**Blocca**: primo upload reale in `logisticolanding`; flip `landing_mode=external`
**ADR collegate**: [[ADR-0023]] (AzCopy), [[ADR-0003]] (landing UC Volume), [[ADR-0005]] (no segreti / canale export), [[ADR-0022]] (auth via Managed Identity)   **OP collegati**: OP-INF-4 (SSOT stato), OP-07 (path landing), OP-08 (watermark full/delta)

## Contesto e motivazione
L'ingestion della landing avviene via **AzCopy** su Azure Blob ([[ADR-0023]]). Serve un host on-prem che (1) riceva i file estratti dagli agenti ODI e (2) li invii al container `logisticolanding`. Gli agenti ODI (`odisrvcno1` 10.8.1.211, `odisrvcno2` 10.8.1.212) sono **RHEL 6.8** (EOL): glibc 2.12 < 2.17 → **AzCopy nativo non gira**; Python 2.6.6, no SCL; trust CA datato. Quindi **non** possono essere l'host del trasporto. Soluzione: un **relay Linux dedicato** nella stessa rete, che fa da **storage + sender**. L'estrazione resta sugli agenti ODI (D5/[[ADR-0005]]: non gira su Databricks).

## Obiettivo
`estrazione (ODI, Oracle→file)` → `deposito (NFS sul relay)` → `invio (AzCopy dal relay)` → `landing logisticolanding`, con **trigger da ODI** (lineage in ODI) e impianto **riusabile** oltre il logistico (multi-ambiente, multi-sistema). Fatto = trigger da entrambi gli agenti che lancia AzCopy sul relay; alla consegna del SAS, upload reale idempotente.

## Analisi tecnica — architettura
```
Agenti ODI (RHEL 6.8)                         Relay odisrvcno3 (Ubuntu 26.04)           Azure
 odisrvcno1 10.8.1.211  --- estrae Oracle --> /data/landing/staging/<env>/<sistema>/ -- AzCopy --> Blob
 odisrvcno2 10.8.1.212      (scrive via NFS)  (storage + sender)                      logisticolanding
        \__ OdiOSCommand -> ssh (forced command) -> upload_landing.sh <env> <sistema> __/
```
- **Storage via endpoint pubblico** (DNS→IP pubblici 20.x, TLS/CA ok): **nessun Private Endpoint**.
- **Trigger = Opzione A** (OSCommand ODI → ssh → AzCopy): tiene l'intera filiera dentro ODI. Fallback Opzione B (marker + watcher systemd) **scartato** perché A funziona.

## Inventario per server (cosa è installato / configurato)

### `odisrvcno3` — relay (Ubuntu 26.04.1 LTS, glibc 2.43, 8 vCPU/30 GiB, IP 10.8.1.158)
- **Disco**: LV `landing` **500G** (VG `ubuntu-vg`) ext4 montato su `/data/landing` (fstab).
- **Utenza di servizio**: `svc_landing` (uid 999 / gid 983, shell `/bin/bash`, home `/home/svc_landing`).
- **AzCopy 10.32.7** in `/usr/local/bin/azcopy` (egress + TLS + CA verso Blob verificati).
- **NFS server** (`nfs-kernel-server`): export di `/data/landing/staging` verso .211/.212 (`all_squash`, anon=svc_landing); giro ODI→NFS→staging **validato** (file owner `svc_landing`).
- **Cartelle applicative**: `/opt/landing/bin` (script), `/opt/landing/conf/<env>/` (routing), `/opt/landing/secrets/<env>/` (SAS, 600), `/var/log/landing` (log + piani AzCopy).
- **sshd legacy** (`/etc/ssh/sshd_config.d/10-odi-legacy.conf`, **globale**): `KexAlgorithms +diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1`, `HostKeyAlgorithms +ssh-rsa`, `PubkeyAcceptedAlgorithms +ssh-rsa` (compatibilità col client OpenSSH 5.3 degli agenti).
- **authorized_keys** di `svc_landing` (600): **2 righe** (una per agente) con `command="/opt/landing/bin/upload_landing.sh",restrict,from="10.8.1.211,10.8.1.212"`.
- **Sender**: `/opt/landing/bin/upload_landing.sh` (⚠️ al 2026-10-01 è ancora una versione **precedente**: da ri-deployare dalla versione repo multi-env/sistema alla posa del SAS); unit `landing-upload.service` + `.timer` (fallback schedulato `dev logistico`).

### `odisrvcno1` — agente ODI (RHEL 6.8, OpenSSH 5.3, IP 10.8.1.211)
- **Chiave** `~oracle/.ssh/id_rsa_landing` (RSA 4096) generata; host key del relay in `known_hosts`.
- **Fix** `/etc/ssh/ssh_config`: rimossa direttiva **server** `HostKey` finita per errore nel config **client** (bloccava ogni ssh in uscita); backup `ssh_config.bak`.
- **Trigger** `trigger_landing_upload.sh` (da deployare in `/home/oracle/bin/`, owner oracle).
- **NFS client**: mount `/data/landing/staging` del relay (da rendere persistente in fstab; scrive sotto `dev/logistico/...`).

### `odisrvcno2` — agente ODI (RHEL 6.8, OpenSSH 5.3, IP 10.8.1.212)
- **Chiave** `~oracle/.ssh/id_rsa_landing` (RSA 4096); host key relay in `known_hosts`.
- **Trigger** `trigger_landing_upload.sh` (come sopra).
- **NFS client**: mount verso il relay (come sopra). `ssh_config` **non** aveva il problema di odisrvcno1.

## Convenzione path (decisione)
`/data/landing/staging/<env>/<sistema>/<sorgente>-landing/<tabella>/YYYY/MM/DD/<file>`
- `<env>` = ambiente destinazione (`dev`→`prod`); `staging` resta il root NFS già registrato, l'env è un livello **sotto** (no rename, zero impatto su export/fstab/mount/unit).
- `<sistema>` = dominio applicativo (`logistico`→altri).
- `<env>/<sistema>` **non** finiscono nel container (si copia il *contenuto*): dentro `logisticolanding` resta `<sorgente>-landing/...` (**OP-07 invariato**).
- Routing `(env,sistema)→(container, SAS)` in `/opt/landing/conf/<env>/<sistema>.conf`; SAS in `/opt/landing/secrets/<env>/<sistema>.sas`. **Aggiungere env/sistema = nuova sub-folder + nuovo conf, zero codice.**

## Decisioni chiave
1. **Relay Linux dedicato** (non la macchina Windows, non gli agenti RHEL6): risolve glibc/CA e tiene il flusso on-prem nello stesso rack ODI.
2. **Trigger Opzione A** (OSCommand→ssh→AzCopy) per preservare il lineage ODI; B scartata.
3. **Sicurezza ssh**: chiave dedicata per agente + **forced command** + `restrict` + `from=` ai soli 2 IP ODI. Il SAS vive **solo** sul relay (gli agenti non lo vedono).
4. **sshd legacy globale**: su OpenSSH 10 `KexAlgorithms`/`Ciphers`/`MACs`/`HostKeyAlgorithms` **non** sono ammessi in `Match` → vanno globali; accettabile perché host **solo interno** e `+` lascia intatti i default moderni.
5. **Auth scrittura = SAS token** (semplice dalle macchine on-prem datate; SP come evoluzione). **Lettura Databricks** via Access Connector + External Location (`landing_mode=external`).
6. **Convenzione path `<env>/<sistema>`** (sopra) per rendere l'impianto riusabile.
7. **`.sh` forzati a LF** via `.gitattributes` (girano su Linux; un CRLF romperebbe shebang/`set`).
8. **Retention** lifecycle **220 gg** su DEV; **3 utenze operatore** Contributor sul solo container (accesso manuale).
9. **Landing interim** = Volume UC **managed** `landing_dev.logistica.files` (non SFTP); **cutover** = ricrearlo come Volume **external** stesso nome → `landing_base_path` invariato.

## Sviluppo (diario)
- **2026-09-25** · discovery relay (Ubuntu 26.04, glibc 2.43); LV 500G `/data/landing`; utenza `svc_landing`; **AzCopy 10.32.7**; NFS export + giro ODI→NFS→staging validato. Artefatti versionati in `scripts/relay_azcopy/`. Inviata a Reply richiesta provisioning (container + SAS + Access Connector).
- **2026-09-29/30** · Reply conferma provisioning; definite retention 220gg, 3 utenze operatore; compilato template Blob `AZUSTD_BLOB_STORAGE`; chiarita landing interim (Volume managed) + strategia cutover.
- **2026-10-01** · **sshd legacy** sul relay (fix KEX `Unable to negotiate`); **chiavi RSA** su .211/.212 + **forced command**; **fix ssh_config** di odisrvcno1; **trigger A validato su entrambi gli agenti** (AzCopy parte, `exit=1` solo per SAS assente). Poi **convenzione path `<env>/<sistema>`** + `upload_landing.sh` e `trigger_landing_upload.sh` multi-env/sistema + conf d'esempio + `.gitattributes` LF. Lezioni estratte: [[LL-035]], [[LL-036]].
- **2026-10-01 (pomeriggio)** · **Reply consegna il provisioning** (mail Eddy): container `logisticolanding` (lifecycle 220gg), **SAS** R/W/C/A/List HTTPS-only scad. 31/03/2027 via policy `logistico-azcopy-20270331` (file `logistico-azcopy-access.json`, **segreto gitignored**; SAS **senza Delete**), Access Connector `ac-dev-logistico-00` + Storage Credential `logisticolanding_dev_ro` + External Location `logisticolanding_dev` (READ FILES a `Group-Engineering-dev` + SP `id-dev-dataplatform-workload-00`), Contributor sul container a 3 utenze. → avvio **collaudo** dal relay.
- **2026-10-02** · **collaudo dal relay OK**: SAS posato in `/opt/landing/secrets/dev/logistico.sas` (estratto dal JSON via `python3`, JSON poi rimosso dal relay), `conf/dev/logistico.conf` + `staging/dev/logistico` creati, `upload_landing.sh` multi-env ri-deployato. `upload_landing.sh dev logistico` → AzCopy **Completed**, `exit=0`; `azcopy list` conferma blob `_smoketest/2026/10/01/check.txt` **senza** prefisso `dev/logistico/` (OP-07 ok).
- **2026-10-02 (extract+send sul relay)** · verificati i prerequisiti per eseguire **l'estrazione direttamente sul relay**:
  Python **3.14.4**, `oracledb` **THIN** contro **Oracle 19c** (→ **nessun Instant Client**), AzCopy 10.32.7, disco ~467 GB;
  venv `/opt/landing/venv` + librerie. Creato orchestratore **`extract_and_send.sh`** (source env Oracle → estrae con i
  2 script Python in `staging/<env>/<sistema>` → `upload_landing.sh` → AzCopy; multi-env/sistema, `DRYRUN`, token-safe,
  `run_date` default=oggi, **recap per esecuzione** in `/var/log/landing/extract_send_recap.log` + log run in
  `/var/log/landing/runs/`). **Primo carico REALE**: run-date 2026-10-01, tutti i sistemi + CDT_DW → AzCopy
  **`Completed` 307 file / ~2,23 GB / 0 Failed** in `logisticolanding`. **Scheduling** via systemd
  `landing-extract-send.service`/`.timer` (05:00, Persistent). ⚠️ **Variante architetturale**: l'estrazione gira **sul
  relay**, non sugli agenti ODI (vedi nota in Analisi) → da decidere / eventuale ADR.

## Verifica
- **Handshake ssh** .211/.212 → relay: OK (`ssh_rsa_verify: signature correct`, NEWKEYS).
- **Forced command**: `ssh svc_landing@relay "dev logistico"` esegue **solo** `upload_landing.sh`; qualunque altro comando è ignorato.
- **Anti-injection**: token validati `^[a-z0-9-]+$` (smoke test: `dev; rm -rf /` → REJECT; token singolo → REJECT).
- **Catena E2E**: AzCopy tenta i file di staging e si ferma su `Please authenticate … SAS` (`exit=1`) = tutto cablato tranne il SAS.
- **NFS**: round-trip ODI→staging con file owner `svc_landing`.
- ✅ **Upload reale (2026-10-02)**: `upload_landing.sh dev logistico` → `Completed`, `exit=0`; `azcopy list` conferma il path nel container (no prefisso env/sistema). Resta: trigger E2E da ODI + attivazione timer.

## Esito (parziale)
Impianto di trasporto pronto e **trigger A validato**; manca solo il SAS per l'upload reale. Artefatti in `scripts/relay_azcopy/` (`upload_landing.sh`, `trigger_landing_upload.sh`, `conf.example/dev/logistico.conf`, `landing-upload.service`/`.timer`, `exports.example`, `README.md`). Commit di riferimento: trigger A validato + doc (`9f727f7`, `4d1539a`); convenzione path + sender/trigger multi-env (`6d13af3`, `df562dd`). Stato vivo in [[OP-INF-4]].

## Lezioni
Scoperte **trasferibili**, estratte in `DOCS/main/lessons/` (ADR-0020):
- [[LL-035]] — `ssh: Unable to negotiate a key exchange method` da client **OpenSSH 5.3 (RHEL6)** verso **OpenSSH 10 (Ubuntu 26.04)**: riabilitare sul server, **globalmente** (non in `Match`), `KexAlgorithms +diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1` + `HostKeyAlgorithms +ssh-rsa` + `PubkeyAcceptedAlgorithms +ssh-rsa`; chiave utente **RSA** obbligatoria.
- [[LL-036]] — direttiva **server** `HostKey` in `ssh_config` **client** → `Bad configuration option`, ogni ssh in uscita muore (`exit=255`): commentarla (solo `HostKey`, non `HostKeyAlgorithms`/`HostKeyAlias`).
- Nota minore: `*.sh` destinati a Linux vanno a **LF** (gitattributes), altrimenti CRLF rompe shebang/`set`.

## Follow-up
- ✅ **Gated SAS** (consegna Reply 2026-10-01): SAS posato + `staging/dev/logistico` + `conf/dev/logistico.conf` + ri-deploy `upload_landing.sh` + **upload reale verificato** (collaudo 2026-10-02).
- ✅ **Estrazione sul relay** (variante): prereq verificati (Python 3.14 / oracledb thin / Oracle 19c), `extract_and_send.sh` + unit systemd + recap; **primo carico reale** 307 file/~2,23 GB (2026-10-02). → vedi worklog `2026-10-02-03`.
- **DECISIONE aperta**: estrazione **sul relay** (extract+send unico host) **vs** sugli **agenti ODI** (lineage ODI, trigger forced-command già pronto) → eventuale **ADR**. Coordinare con Luigi.
- **Migrazione storico** Volume managed → `logisticolanding` + ricreazione **external Volume** stesso nome (cutover → flip `landing_mode=external`).
- **Rotazione SAS** (scad. 31/03/2027) e **cleanup staging** post-upload da definire.
- ✅ Lezioni estratte in `lessons/`: [[LL-035]], [[LL-036]].
