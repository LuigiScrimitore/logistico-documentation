# Relay AzCopy — ingestion landing (runbook)

Host relay che riceve i file estratti dagli agenti ODI e li invia alla landing su Azure Blob via **AzCopy**.
Decisione: [OP-INF-4](../../DOCS/main/05_open_points.md) · trasporto [ADR-0023](../../DOCS/main/adr/0023_trasporto_landing_azcopy.md).

## Architettura
```
Agenti ODI (RHEL 6.8: odisrvcno1 10.8.1.211, odisrvcno2 10.8.1.212)
   │  estrazione Oracle -> file CSV/Parquet  (mapping/tool ODI; RHEL6 non esegue i nostri script py3)
   ▼  (scrittura via NFS)
Relay odisrvcno3 (Ubuntu 26.04, 10.8.1.158): /data/landing/staging/<env>/<sistema>/  [share NFS]
   │  trigger: OSCommand ODI -> ssh (forced command) -> upload_landing.sh <env> <sistema>
   │  azcopy copy "staging/<env>/<sistema>/*" --recursive --overwrite=ifSourceNewer
   ▼
Azure Blob: stdevdataplatformweudata / container logisticolanding   (endpoint pubblico; landing_mode=external lato UC)
```
- **Estrazione** = sugli agenti ODI (non su questo relay). Il relay è **solo storage + sender**.
- **Convenzione path** (OP-INF-4 / OP-07): `/data/landing/staging/<env>/<sistema>/<sorgente>-landing/<tabella>/YYYY/MM/DD/<file>`.
  - `<env>` = ambiente di destinazione (`dev` ora; `prod` in futuro). `staging` resta il root NFS già registrato;
    l'ambiente è un livello **sotto** staging.
  - `<sistema>` = dominio applicativo che instrada verso il container giusto (`logistico` ora; domani altri).
  - I livelli `<env>/<sistema>/` **non** finiscono nel container: si copia il *contenuto* di `staging/<env>/<sistema>/`;
    nel container (`logisticolanding`) resta `<sorgente>-landing/<tabella>/YYYY/MM/DD/` (sorgenti: logistix, cdtdw, stat).
  - Mappa `(env,sistema) -> (container, SAS)` nei file `/opt/landing/conf/<env>/<sistema>.conf`. Aggiungere un
    ambiente o un sistema = nuova sub-folder staging + nuovo conf, **nessuna modifica agli script**.

## Stato ambiente (verificato 2026-09-25)
- Ubuntu 26.04.1 LTS, glibc 2.43, x86_64, 8 vCPU, 30 GiB RAM, NTP attivo.
- Disco: VG `ubuntu-vg` (~698G); LV `landing` **500G** montato su `/data/landing`.
- **AzCopy 10.32.7** installato; egress + TLS + CA verso Azure Blob **OK** (endpoint pubblico, no Private Endpoint in gioco).
- NFS export verso 10.8.1.211/212 attivo; giro ODI→NFS→staging **validato** (file owner `svc_landing`).

## Setup eseguito (sintesi comandi)
1. **Storage**: `lvcreate -L 500G -n landing ubuntu-vg` → `mkfs.ext4` → mount `/data/landing` (fstab).
2. **Utenza/cartelle**: `svc_landing` (uid 999/gid 983); `/data/landing/staging`, `/var/log/landing`,
   `/opt/landing/secrets` (700), `/opt/landing/conf`, `/opt/landing/bin`.
3. **AzCopy**: tarball `aka.ms/downloadazcopy-v10-linux` → `/usr/local/bin/azcopy`.
4. **NFS**: `nfs-kernel-server`; `/etc/exports` = vedi `exports.example`; `exportfs -ra` + `systemctl enable --now nfs-server`.
   - Lato ODI (RHEL6): `mount -t nfs 10.8.1.158:/data/landing/staging /mnt/landing` (fstab per persistenza; `-o vers=3` se serve).
   - ODI scrive sotto `<env>/<sistema>/`: `/mnt/landing/dev/logistico/<sorgente>-landing/<tabella>/YYYY/MM/DD/`.
5. **Sender**: `upload_landing.sh` in `/opt/landing/bin/`; conf per-(env,sistema) in `/opt/landing/conf/<env>/` (vedi
   `conf.example/dev/logistico.conf`); unit `landing-upload.service` + `.timer` in `/etc/systemd/system/`.

## Attivazione sender (dopo che Reply consegna container + SAS)
```bash
# 0) sub-folder (env/sistema) + conf (una tantum per combinazione)
sudo install -d -o svc_landing -g svc_landing -m 755 /data/landing/staging/dev/logistico
sudo install -d -m 755 /opt/landing/conf/dev
sudo install -o root -g root -m 644 conf.example/dev/logistico.conf /opt/landing/conf/dev/logistico.conf
# 1) ri-deploy dello script dal repo (allinea la versione multi-env/multi-sistema)
sudo install -o root -g root -m 755 upload_landing.sh /opt/landing/bin/upload_landing.sh
# 2) SAS in file protetto, per-(env,sistema) (NB: nome allineato a SAS_FILE nel conf)
sudo install -d -o svc_landing -g svc_landing -m 700 /opt/landing/secrets/dev
sudo install -o svc_landing -g svc_landing -m 600 /dev/stdin /opt/landing/secrets/dev/logistico.sas <<< '?sv=...&sig=...'
# 3) test manuale (env+sistema come argomenti; via ssh arrivano da $SSH_ORIGINAL_COMMAND)
sudo -u svc_landing /opt/landing/bin/upload_landing.sh dev logistico
# 4) schedulazione di fallback (il timer chiama lo script con "dev logistico")
sudo systemctl daemon-reload && sudo systemctl enable --now landing-upload.timer
systemctl list-timers landing-upload.timer
```

## Trigger invio — Opzione A (ssh forced command), validato 2026-10-01
Gli agenti ODI lanciano l'upload via `OdiOSCommand` → `ssh svc_landing@10.8.1.158` → sul relay parte **solo**
`upload_landing.sh` (nessun altro comando). Setup (una tantum):

1. **sshd legacy sul relay** — `odisrvcno3` ha OpenSSH 10, gli agenti RHEL6 hanno OpenSSH 5.3: senza questo
   l'handshake fallisce (`Unable to negotiate a key exchange method`). File `/etc/ssh/sshd_config.d/10-odi-legacy.conf`
   (direttive **globali**: `KexAlgorithms`/`Ciphers`/`MACs`/`HostKeyAlgorithms` **non** sono ammesse in `Match` su OpenSSH 10):
   ```
   KexAlgorithms +diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1
   HostKeyAlgorithms +ssh-rsa
   PubkeyAcceptedAlgorithms +ssh-rsa
   ```
   `+` aggiunge ai default moderni (gli altri accessi restano forti). Host solo interno (rete 10.8.x).
   Valida e ricarica: `sudo sshd -t && sudo systemctl reload ssh`.
2. **Chiave per agente** (RSA obbligatoria, il 5.3 non fa ed25519/ecdsa): su ogni agente, come `oracle`,
   `ssh-keygen -t rsa -b 4096 -N '' -f ~/.ssh/id_rsa_landing`.
3. **authorized_keys con forced command** (`/home/svc_landing/.ssh/authorized_keys`, 600, owner svc_landing) —
   una riga per agente:
   ```
   command="/opt/landing/bin/upload_landing.sh",restrict,from="10.8.1.211,10.8.1.212" ssh-rsa AAAA... <agente>
   ```
   `restrict` = niente pty/forwarding/agent; `from=` = solo i 2 IP ODI; `command=` = esegue solo lo script.
   Env e sistema **non** si mettono qui: arrivano a runtime da `$SSH_ORIGINAL_COMMAND` (ciò che passa il client).
4. **Script lato ODI** (`trigger_landing_upload.sh`, in questo repo) — deploy **identico** su odisrvcno1 e odisrvcno2
   (es. `/home/oracle/bin/`, owner oracle, 750). È quello che l'`OdiOSCommand` lancia; fa solo l'`ssh` verso il relay
   passando `"<env> <sistema>"`:
   ```
   /home/oracle/bin/trigger_landing_upload.sh dev logistico
   ```
5. **Test**: `ssh -T -o BatchMode=yes -i ~/.ssh/id_rsa_landing svc_landing@10.8.1.158 'dev logistico'` → prima della
   consegna del SAS esce con `exit=1` (AzCopy prova la staging e si ferma su `Please authenticate … SAS`) = catena OK.

> **Gotcha `odisrvcno1`**: il `ssh_config` **client** aveva per errore una direttiva server `HostKey ...` dentro
> `Host *` → ogni `ssh` in uscita moriva con `Bad configuration option`. Commentata (backup `ssh_config.bak`).
> **Cleanup (gated SAS)**: lo script `/opt/landing/bin/upload_landing.sh` deployato è una versione precedente
> (single-path, senza env/sistema né guardia `[ -r SAS ]`) → **ri-deployare dalla versione di questo repo** con lo
> step 1 dell'attivazione, contestualmente alla posa del SAS.

## Estrazione sul relay (`extract_and_send.sh`) — variante
Il relay raggiunge **sia Oracle (19c) sia Azure**, quindi può eseguire anche l'**estrazione** (`oracledb` in
**THIN mode**, nessun Instant Client), unificando **extract + send** sullo stesso host. È un'**alternativa**
all'estrazione sugli agenti ODI (da decidere / eventuale ADR — vedi [[ACT_OP-INF-4]]).

**Prerequisiti** (verificati 2026-10-02): Python 3.x (3.14 ok) + venv `/opt/landing/venv` con
`oracledb`/`pyyaml`/`python-dotenv`; app in `/opt/landing/app/scripts/...`; credenziali Oracle in
`/opt/landing/conf/<env>/<sistema>.oracle.env` (600, `svc_landing`); `/data/landing/staging/<env>` scrivibile da
`svc_landing` (l'estrattore scrive i log in `output_dir.parent/logs`).

**Uso** (come `svc_landing`; `run_date` omesso = oggi; default = tutti i sistemi + CDT_DW):
```bash
sudo -u svc_landing /opt/landing/bin/extract_and_send.sh dev logistico
# prova sicura (non scrive, non invia):
sudo -u svc_landing env DRYRUN=1 /opt/landing/bin/extract_and_send.sh dev logistico
# override: SYSTEMS=stat DO_CDTDW=0 ...
# flag CDC dell'ODI legacy: IGNORE_ODI_FLAG=1 (default fino al go-live) = solo finestra data;
#   le tabelle senza colonna data (imbfmovim) tengono comunque il flag. Al go-live: IGNORE_ODI_FLAG=0.
#   Dal 2026-10-16 (ACT_9030) le tabelle con `selection` in config.yaml (carichi, pesate, righe carico, traccia,
#   carrellisti, cartellino, abb tolti, imbfmovim, bolle/liste/riepiloghi STAT) NON usano piu' la finestra data:
#   leggono il timbro dell'ODI in sola lettura (sospesi + timbrati negli ultimi 2 giorni). IGNORE_ODI_FLAG non le tocca.
# recupero (opzioni in piu' all'estrattore): EXTRACT_EXTRA="--stamp-from 2026-10-01 --max-rows 0" = tutto cio' che
#   l'ODI ha timbrato dal 1/10 (+ sospesi). Va con SKIP_SNAPSHOT=1 se la run_date non e' oggi.
# snapshot (catena, catena_esterni = giacenze): SKIP_SNAPSHOT=auto (default) le esclude se run_date non e' oggi,
#   perche' sono la fotografia del momento e con una data passata avrebbero la data sbagliata (LL-006).
#   SKIP_SNAPSHOT=1 le esclude sempre, SKIP_SNAPSHOT=0 le include sempre.
```

**Scheduling senza login** — unit `landing-extract-send.service`/`.timer` (oneshot `svc_landing`, `OnCalendar=05:00`,
`Persistent=true`):
```bash
sudo install -o root -g root -m 644 landing-extract-send.service /etc/systemd/system/
sudo install -o root -g root -m 644 landing-extract-send.timer   /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now landing-extract-send.timer
sudo systemctl disable --now landing-upload.timer 2>/dev/null || true   # evita doppio invio (solo-upload)
```

**Recap per esecuzione**: blocco riassuntivo appeso a `/var/log/landing/extract_send_recap.log` (esito estrazione
`files/rows/errors`, esito AzCopy `Completed/file/GB`, durate, OK/KO) + log completo del run in
`/var/log/landing/runs/extract_send_<ts>.log`.

## Job ODI schedulato → `extract_and_send.sh` sul relay (2026-10-11)
Obiettivo: un **job ODI schedulato**, eseguito dall'agent `odisrvcno1` o `odisrvcno2`, che lancia il giro completo
estrai+invia **sul relay** `odisrvcno3` (10.8.1.158). Riusa il canale dell'Opzione A (stessa chiave, `restrict`,
`from=`); cambia solo lo **script forzato** sul relay. Sugli agenti non serve nessuno script nuovo.

1. **Relay** — forced command da `upload_landing.sh` a `extract_and_send.sh` (una riga per agente in
   `/home/svc_landing/.ssh/authorized_keys`; gli argomenti nel `command=` sono ammessi):
   ```
   command="/opt/landing/bin/extract_and_send.sh dev logistico",restrict,from="10.8.1.211,10.8.1.212" ssh-rsa AAAA... <agente>
   ```
   ```bash
   sudo cp -a /home/svc_landing/.ssh/authorized_keys /home/svc_landing/.ssh/authorized_keys.bak
   sudo sed -i 's|command="/opt/landing/bin/upload_landing.sh"|command="/opt/landing/bin/extract_and_send.sh dev logistico"|' /home/svc_landing/.ssh/authorized_keys
   sudo grep -c 'extract_and_send.sh dev logistico' /home/svc_landing/.ssh/authorized_keys   # atteso: 2
   ```
   Da qui la chiave degli agenti lancia **solo** estrai+invia (`run_date` = giorno di esecuzione); il trigger di solo
   invio non esiste più. Per un giorno passato si lancia a mano sul relay con la data come 3° argomento.
2. **Relay** — spegnere i timer systemd, se presenti (altrimenti il giro parte due volte). Al 2026-10-11
   `landing-extract-send.timer` non risultava installato su odi3; disabilitare i due timer **separatamente**
   (con un'unità inesistente `systemctl` si ferma alla prima):
   `sudo systemctl disable --now landing-extract-send.timer` · `sudo systemctl disable --now landing-upload.timer`
3. **ODI** — step `OdiOSCommand` **sincrono** (in una procedura o un package → scenario), eseguito dall'agent; la
   chiave è quella di `oracle`, quindi l'agent deve girare come `oracle`:
   ```
   ssh -T -i /home/oracle/.ssh/id_rsa_landing -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -o ServerAliveInterval=60 -o ServerAliveCountMax=10 svc_landing@10.8.1.158 dev logistico
   ```
   Senza apici: ssh unisce gli argomenti finali con uno spazio, quindi su odi3 arriva comunque `dev logistico`, sia che
   ODI esegua il comando tramite shell sia che lo spezzi sugli spazi (con gli apici rischierebbero di arrivare letterali).
   ⚠️ La stringa finale **non è ignorata**: arriva su odi3 in `SSH_ORIGINAL_COMMAND` e `upload_landing.sh` le dà la
   precedenza sui propri argomenti. Va quindi passato **`dev logistico`** (con `extract-send` il primo test del
   2026-10-11 ha estratto ma l'invio è fallito con `sistema non valido: ''`). Da `extract_and_send.sh` aggiornato
   (repo, 2026-10-11) il sender viene chiamato con `env -u SSH_ORIGINAL_COMMAND`, quindi la stringa diventa
   indifferente, ma passare `dev logistico` resta la scelta sicura anche con la versione vecchia. L'exit
   code del relay torna a ODI: se estrazione o invio vanno KO, lo step fallisce. Il keepalive evita che la sessione
   cada durante un giro lungo.
4. **Schedulazione** in ODI: scenario → *Scheduling* → New (agent, giornaliero, orario) → *Update Schedule*
   sull'agent. Attivo dal 2026-10-11: ogni giorno alle **06:00** ora italiana (04:00 UTC su odi3); il giro finisce
   verso le 06:13, prima del vecchio ETL delle 06:30 (comunque ininfluente con il flag ODI ignorato).
   ⚠️ odi3 è su **UTC** e `run_date` di default è la data di odi3: non schedulare tra 00:00 e 02:00 italiane,
   altrimenti estrae il giorno precedente.
5. **Verifica** del primo run: step ODI verde + ultimo blocco di `/var/log/landing/extract_send_recap.log` sul relay
   (`status: OK`, `upload: Completed`) + file del giorno in `logisticolanding`.

## In attesa da Reply (gate esterni)
- **Container `logisticolanding` + SAS** (permessi Read/Write/Create/Add/List) → sblocca l'upload reale.
- **Access Connector + External Location** su UC → lettura da Databricks (`landing_mode=external`).
- Conferma soft: eventuale **IP allowlist** sullo storage (l'IP del relay risulta già ammesso).

## Operazioni
- **Log**: `/var/log/landing/` (AzCopy) + `/var/log/landing/upload.log`. Piani job in `/var/log/landing/plans`.
- **Idempotenza**: `--overwrite=ifSourceNewer` (ri-esecuzioni sicure).
- **Retention/cleanup** della staging: da definire (oggi non si cancella; valutare pulizia post-upload).
- **Segreti**: SAS in `/opt/landing/secrets/<env>/<sistema>.sas` (600, svc_landing). SAS ha scadenza → definire rotazione.
- **Evoluzione**: passaggio da SAS a Service Principal quando/se fattibile.
