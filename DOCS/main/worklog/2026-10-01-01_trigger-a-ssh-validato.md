---
data: 2026-10-01
titolo: Trigger A (ssh forced command) validato su odisrvcno1/2
autore: Luigi Scrimitore
push_monorepo: 9f727f7
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa e' stato fatto
- **Validato il Trigger A (Opzione A)** dell'ingestion landing: `OdiOSCommand → ssh svc_landing@odisrvcno3 →
  upload_landing.sh → AzCopy → container logisticolanding`, da **entrambi** gli agenti ODI (odisrvcno1 10.8.1.211,
  odisrvcno2 10.8.1.212). Il test chiude con `exit=1` **solo** perché il SAS non è ancora stato consegnato (AzCopy
  prova i file di staging e si ferma su `Please authenticate … SAS`) → catena cablata e funzionante.
- **ACT_9012 / OP-INF-4**: trigger "chiuso a livello meccanismo"; il fallback **Opzione B** (marker + watcher systemd)
  **non serve più**.

## Novita'
- **sshd legacy su `odisrvcno3`** (`/etc/ssh/sshd_config.d/10-odi-legacy.conf`, direttive **globali** — `KexAlgorithms`/
  `Ciphers`/`MACs`/`HostKeyAlgorithms` non sono ammesse in `Match` su OpenSSH 10): `KexAlgorithms
  +diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1`, `HostKeyAlgorithms +ssh-rsa`,
  `PubkeyAcceptedAlgorithms +ssh-rsa`. Riabilita gli algoritmi del client **OpenSSH 5.3** (RHEL6) senza togliere i
  default moderni; host **solo interno** (rete 10.8.x).
- **Chiave RSA dedicata** per agente (`~oracle/.ssh/id_rsa_landing`) + **`forced command`** in `svc_landing`:
  `command="/opt/landing/bin/upload_landing.sh",restrict,from="10.8.1.211,10.8.1.212"` → la pubkey ODI esegue
  **solo** lo script, da null'altro, e solo dai 2 IP.
- **Gotcha odisrvcno1**: il `ssh_config` **client** aveva per errore `HostKey /etc/ssh/ssh_host_ecdsa_key` (direttiva
  server) dentro `Host *` → bloccava ogni `ssh` in uscita; commentata (backup `ssh_config.bak`).
- **Cleanup residuo (gated SAS)**: lo script deployato in `/opt/landing/bin/` è una versione precedente (manca la
  guardia `[ -r SAS ]`) → **ri-deploy dalla versione del repo** alla posa del SAS; definire **rotazione SAS**.

## Doc aggiornati
- `05_open_points.md` (OP-INF-4: aggiornamento 2026-10-01 + Status), `acts/ACT_9012` (aggiornamento 2026-10-01),
  `scripts/relay_azcopy/README.md` (nuova sezione "Trigger invio — Opzione A").

## Stato dopo il push / prossimi passi
- **Provisioning in esecuzione lato Reply** (container/SAS + Access Connector + 3 utenze + lifecycle 220gg). Trigger A
  chiuso. Alla consegna del SAS: posa SAS su odisrvcno3 + ri-deploy `upload_landing.sh` + **test upload reale**. Poi:
  migrazione storico Volume→logisticolanding + ricreazione external Volume stesso nome; industrializzazione estrazione
  ODI (mapping che scrivono sulla staging NFS col layout corretto).
