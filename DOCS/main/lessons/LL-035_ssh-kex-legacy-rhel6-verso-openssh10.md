---
id: LL-035
titolo: ssh da RHEL6 (OpenSSH 5.3) verso Ubuntu 26.04 (OpenSSH 10) — riabilitare KEX/host-key legacy sul server
sintomi:
  - "Unable to negotiate a key exchange method"
  - "no matching host key type found. Their offer: ssh-rsa"
  - "no matching key exchange method found"
tag: [ssh, rhel6, openssh, on-prem, relay, infra]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-10-01
origine: [ACT_OP-INF-4]
---

## Sintomo
Un `ssh` da una macchina **RHEL 6.x** (client **OpenSSH_5.3p1**, es. agenti ODI `odisrvcno1/2`) verso un host
**Ubuntu 26.04** (server **OpenSSH_10.x**, es. relay `odisrvcno3`) muore durante l'handshake:

```
debug1: kex: server->client aes128-ctr hmac-sha1 none
Unable to negotiate a key exchange method
```

Cipher e MAC vengono negoziati (aes128-ctr / hmac-sha1), ma **il key exchange no**: OpenSSH 10 ha dismesso gli
algoritmi KEX che il 5.3 conosce. Risolto il KEX, il blocco successivo è la **host key** (`no matching host key
type … ssh-rsa`), perché il client 5.3 non conosce ed25519/ecdsa/rsa-sha2: l'unico comune è `ssh-rsa` (SHA-1),
disabilitato di default sul server moderno.

## Strada sbagliata
- Toccare il **client** RHEL6 (aggiungere `-oKexAlgorithms=...`): funziona per il singolo comando ma non è
  industrializzabile e non copre la host key.
- Mettere le direttive in un blocco **`Match`** sul server: su OpenSSH 10 `KexAlgorithms`, `Ciphers`, `MACs`,
  `HostKeyAlgorithms` **non sono ammessi** in `Match` → `Directive 'KexAlgorithms' is not allowed within a Match
  block`. Vanno **globali** (solo `PubkeyAcceptedAlgorithms` è ammesso in `Match`). Quindi lo scope "solo i 2 IP"
  non è ottenibile per il KEX: lo si accetta su host **solo interno**.

## Regola
Sul **server** (relay), file `/etc/ssh/sshd_config.d/10-odi-legacy.conf`, direttive **globali**:

```
KexAlgorithms +diffie-hellman-group-exchange-sha256,diffie-hellman-group14-sha1
HostKeyAlgorithms +ssh-rsa
PubkeyAcceptedAlgorithms +ssh-rsa
```

Poi `sudo sshd -t && sudo systemctl reload ssh` (valida PRIMA di ricaricare, evita lockout). La chiave utente deve
essere **RSA** (`ssh-keygen -t rsa -b 4096`): il 5.3 non fa ed25519/ecdsa. Test lato RHEL6:
`ssh -v -o StrictHostKeyChecking=no -i id_rsa_landing utente@host` → deve arrivare all'auth
(`Permission denied (publickey)` = handshake OK).

## Perché
Il `+` **aggiunge** agli algoritmi di default moderni senza rimuoverli: gli altri client (moderni) continuano a
usare gli algoritmi forti; solo il client legacy ricade su `group-exchange-sha256` (SHA-256, accettabile) o, come
fallback, `group14-sha1`/`ssh-rsa` (SHA-1). `group-exchange-sha256` è preferito perché più robusto tra quelli che
il 5.3 sa fare. Essendo globali e SHA-1 nel fallback, l'uso è giustificato solo su host **interni** e di scopo
limitato (qui: relay di trasporto, rete 10.8.x). La soluzione "pulita" sarebbe aggiornare l'OS del client (RHEL6 è
EOL), fuori scope.

## Conferme e contraddizioni
- 2026-10-01 · luigi.scrimitore · validato su `odisrvcno1`/`odisrvcno2` (10.8.1.211/212) → relay `odisrvcno3`
  (10.8.1.158): dopo le 3 direttive, handshake e host-key OK; l'`exit` residuo dipendeva solo da altro (SAS), non
  dall'ssh. Vedi [[LL-036]] per un blocco collaterale sul `ssh_config` client di odisrvcno1.
