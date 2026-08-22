---
id: LL-001
titolo: Il compact del vhdx recupera solo ciò che il TRIM ha scartato
sintomi:
  - "fstrim: 0 B (0 bytes) trimmed"
  - "compact vdisk completato ma il file resta della stessa dimensione"
  - "docker system df: RECLAIMABLE 0B ma il disco C: è pieno"
tag: [docker, wsl, disco, ambiente-locale]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_MNT-01]
---

## Sintomo
`docker_data.vhdx` da 41 GB con soli 24,9 GB usati da Docker. `fstrim` riporta **0 B**, `diskpart compact`
completa con successo ma il file **non cambia dimensione**. Sembra spazio intrappolato e irrecuperabile.

## Strada sbagliata
Due errori sovrapposti, entrambi plausibili:

1. **Metodo di trim sbagliato.** Usato `wsl.exe -d docker-desktop -e fstrim`. Sembra corretto perché la distro
   esiste e il comando non dà errore — ma il mapping dei device è sfasato tra i due contesti: da fuori
   `docker-desktop-disk` risulta `/dev/sdd`, da **dentro** la VM è `/dev/sde`. Si trimma il bersaglio sbagliato
   e si legge uno 0 B che sembra una diagnosi.
2. **Concludere che i GB mancanti siano irrecuperabili.** La differenza tra dimensione del file e dati Docker
   sembrava slack intrappolato. In realtà non c'era **nulla da scartare**: `builder prune` era già a 0 B e il
   VACUUM aveva agito sul warehouse, che è bind mount Windows.

## Regola
Sequenza: liberare dati dentro ext4 (`prune`, rimozione immagini) → `fstrim` **via nsenter** → **verificare che
abbia scartato GB** → `docker desktop stop` (graceful) → `wsl --shutdown` → `compact` con path assoluto.

```bash
MSYS_NO_PATHCONV=1 docker run --rm --privileged --pid=host alpine \
  nsenter -t 1 -m -- fstrim -v /mnt/docker-desktop-disk
```

**Se `fstrim` riporta ~0 B, non procedere al compact**: non c'è nulla da compattare, si torna a liberare dati.
Senza `MSYS_NO_PATHCONV=1` in Git Bash il path diventa `C:/Program Files/Git/mnt/...`.

Stop **graceful** (`docker desktop stop`), mai `Stop-Process -Force`: quest'ultimo corrompe i socket e Docker
non riparte.

## Perché
`compact vdisk` restituisce a Windows **solo i blocchi che il guest ha marcato liberi via TRIM/discard**. Il
discriminante è *dove* sono avvenute le cancellazioni: dentro il vhdx → il trim ha materia e il compact
recupera; sul warehouse (bind mount `C:\PROGETTI\LOGISTICO_DATA`) → lo spazio torna su C: direttamente e il
vhdx resta invariato, **correttamente**.

Esiste anche un pavimento strutturale: ext4 è formattato 1 TB con 67M inode, la cui tabella occupa ~17 GB
scritti fisicamente. Non è spazio libero e nessun trim/compact la recupera.

Esito reale una volta applicata la regola: rimossi ~10 GB di immagini dormienti → **23,9 GiB trimmati** →
vhdx 41 → 18,2 GB, C: da 9,2 a 31 GB.

## Conferme e contraddizioni
- 2026-06-23 · luigi.scrimitore · caso in cui il compact **funzionò** al primo colpo (fstrim 971 GiB, +47 GB):
  le cancellazioni erano avvenute dentro il vhdx durante la pipeline a 22 siti. Coerente con la regola.
- 2026-08-21 · luigi.scrimitore · l'annotazione precedente ("fstrim + compact recupera sempre") era troppo
  assertiva e ha portato a diagnosticare come irrecuperabile ciò che era solo non-ancora-liberato.
