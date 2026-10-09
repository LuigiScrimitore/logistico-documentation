---
data: 2026-10-01
titolo: ACT dedicata relay odisrvcno3 + trigger ODI (recap attività)
autore: Luigi Scrimitore
push_monorepo: a39e7a3
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_OP-INF-4, ACT_9012]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa e' stato fatto
- Creata la **ACT SSOT dell'attività infra**: [`ACT_OP-INF-4`](../acts/ACT_OP-INF-4_relay-linux-azcopy-ingestion.md)
  (work-order). Raccoglie in un unico file tutto il lavoro su relay + trigger, che finora era sparso tra OP-INF-4 e
  ACT_9012.
- **Inventario per server** (cosa è installato/configurato): `odisrvcno3` (LV 500G `/data/landing`, `svc_landing`,
  **AzCopy 10.32.7**, **NFS server**, `/opt/landing/{bin,conf,secrets}`, sshd legacy, authorized_keys forced command,
  sender + unit systemd); `odisrvcno1`/`odisrvcno2` (chiave RSA `id_rsa_landing`, trigger script, mount NFS; su
  odisrvcno1 anche il fix `ssh_config`).
- **Attività, decisioni e verifica** tracciate: chiavi + forced command, sshd legacy (KEX RHEL6↔Ubuntu26), convenzione
  path `<env>/<sistema>`, Opzione A, SAS token, LF su `.sh`; smoke test anti-injection; `exit=1` gated SAS.

## Novita'
- **ACT_9012 ridimensionata** al suo ruolo (analisi SFTP vs Blob) con rimando a `ACT_OP-INF-4` per il setup operativo.
- Agganci: riga in `15_backlog_master` (§3 ACT OP) + "SSOT attività" in OP-INF-4.
- **Lezioni candidate** annotate nella ACT (sintomo `Unable to negotiate a key exchange method` RHEL6→Ubuntu26;
  `HostKey` in `ssh_config` client) → da estrarre in `lessons/`.

## Doc aggiornati
- Nuovo `acts/ACT_OP-INF-4_relay-linux-azcopy-ingestion.md`; `acts/ACT_9012` (nota di rimando); `15_backlog_master.md`
  (§3); `05_open_points.md` (OP-INF-4: SSOT attività).

## Stato dopo il push / prossimi passi
- Attività infra ora ha la sua SSOT. Resta **gated dal SAS di Reply** (posa SAS + ri-deploy `upload_landing.sh` + test
  upload reale). Follow-up registrati nella ACT: industrializzazione estrazione ODI (nuova ACT), migrazione storico
  Volume→external, rotazione SAS, estrazione delle lezioni candidate in `lessons/`.
