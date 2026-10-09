---
id: LL-036
titolo: "HostKey nel ssh_config CLIENT → Bad configuration option: ogni ssh in uscita muore"
sintomi:
  - "/etc/ssh/ssh_config: line 51: Bad configuration option: HostKey"
  - "/etc/ssh/ssh_config: terminating, 1 bad configuration options"
  - "ssh esce con 255 prima ancora di connettersi"
tag: [ssh, ssh_config, on-prem, infra]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-10-01
origine: [ACT_OP-INF-4]
---

## Sintomo
Qualunque `ssh` **in uscita** da una macchina fallisce subito, prima della connessione, con `exit=255`:

```
/etc/ssh/ssh_config: line 51: Bad configuration option: HostKey
/etc/ssh/ssh_config: terminating, 1 bad configuration options
```

Nel `ssh_config` **client** (`/etc/ssh/ssh_config`) c'è una direttiva **server** `HostKey /etc/ssh/ssh_host_*_key`
(tipicamente dentro un blocco `Host *`), finita lì per errore (copia-incolla da un `sshd_config`). Il client ssh
rifiuta di partire.

## Strada sbagliata
- Pensare che sia un problema di rete/chiavi/negoziazione e mettere mano a `known_hosts`, firewall o algoritmi:
  l'errore è **di parsing del config**, avviene prima di aprire la socket (`exit=255`, nessun `debug1: Connecting`).
- Aggirare con `-F /dev/null` (ignora il config di sistema): risolve il singolo comando ma lascia **ogni altro**
  ssh del server rotto (incluso quello lanciato da ODI/OSCommand).

## Regola
Commentare la riga nel `ssh_config` **client** (è una direttiva valida solo in `sshd_config`):

```bash
sudo cp -a /etc/ssh/ssh_config /etc/ssh/ssh_config.bak
sudo sed -i 's|^HostKey /etc/ssh/ssh_host_ecdsa_key|#&|' /etc/ssh/ssh_config
# verifica e ri-test
grep -niE '^[[:space:]]*#?HostKey' /etc/ssh/ssh_config
ssh -v utente@host   # ora deve almeno connettersi
```

Attenzione a commentare **solo** `HostKey` (seguito da spazio): `HostKeyAlgorithms` e `HostKeyAlias` sono invece
direttive **client legittime** e vanno lasciate.

## Perché
`ssh` (client) e `sshd` (server) hanno grammatiche di config diverse. `HostKey` dichiara la chiave privata
d'identità del **server**: nel config client non esiste, quindi il parser la considera opzione sconosciuta e, per
sicurezza, **termina** invece di ignorarla. Poiché il client legge `/etc/ssh/ssh_config` per *ogni* connessione in
uscita, una sola riga errata blocca tutto l'host — ODI compreso.

## Conferme e contraddizioni
- 2026-10-01 · luigi.scrimitore · trovato su `odisrvcno1` (10.8.1.211): bloccava il trigger ssh verso il relay
  (`odisrvcno3`); `odisrvcno2` non aveva il problema. Spesso co-occorre con [[LL-035]] (integrazione RHEL6 ↔ OpenSSH
  moderno): si risolve prima il KEX lato server, poi questo parsing lato client.
