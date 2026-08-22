# Manuale operativo — Recupero spazio disco Docker (WSL2 vhdx)

> **Scopo**: liberare spazio sul disco C: di Windows occupato dal disco virtuale di Docker Desktop.
> **Verificato**: 2026-06-16 → da 76.2 GB a 34.4 GB di vhdx, C: libero da 25.8 a 67.6 GB (**~42 GB recuperati**).
> **Macchina di riferimento**: ITFIR-LS3345 — Docker Desktop 29.x, backend WSL2.

---

## 1. Perché succede

Docker Desktop tiene **tutto** (immagini, container, build cache, volumi) dentro un unico file disco dinamico:

```
C:\Users\luigi.scrimitore\AppData\Local\Docker\wsl\disk\docker_data.vhdx
```

Questo file è **condiviso tra TUTTI i progetti Docker** della macchina (logistico-spark, aos, levity, caronte, wf_analytics, coind-dbt...), non solo la pipeline Logistico.

Caratteristica chiave: il vhdx **cresce** quando aggiungi dati ma **non si restringe da solo** quando cancelli dentro la VM. Per restituire lo spazio a Windows servono due passi distinti:

1. **Liberare** dati dentro la VM (prune della build cache, ecc.).
2. **Compattare** il vhdx (`diskpart compact`) per restituire i blocchi liberati a Windows.

> ⚠️ I dati LOGISTICO (warehouse ~6 GB, landing ~11 GB) sono bind-mount su Windows in `C:\PROGETTI\LOGISTICO_DATA`, **NON** dentro il vhdx. Non vengono toccati da questa procedura.

---

## 2. Diagnosi iniziale (sempre prima di agire)

Con Docker Desktop **acceso**, da PowerShell:

```powershell
docker system df
```

Output tipico:

```
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          36        31        39.53GB   695MB (1%)
Containers      35        10        282.5MB   277.6MB (98%)
Local Volumes   26        18        4.03GB    1.335GB (33%)
Build Cache     287       0         28.64GB   13.68GB
```

Leggi la colonna **RECLAIMABLE**: è quanto puoi liberare. Quasi sempre il grosso sta nella **Build Cache**.

Dimensione attuale del vhdx e spazio libero su C::

```powershell
$vhdx = "C:\Users\luigi.scrimitore\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
"vhdx: $([math]::Round((Get-Item $vhdx).Length/1GB,1)) GB | C: libero: $([math]::Round((Get-PSDrive C).Free/1GB,1)) GB"
```

---

## 3. Procedura standard (3 passi)

### Passo 1 — Libera la build cache (sicuro, NON tocca immagini né container attivi)

Con Docker acceso:

```powershell
docker builder prune -f
```

Recupera la build cache non usata (nell'ultima esecuzione: 13.7 GB). È **non distruttivo**: non rimuove immagini, container o volumi.

> **Opzionali, con cautela** (solo se serve ancora spazio):
> - `docker image prune -a -f` → rimuove immagini **non usate da alcun container**. ⚠️ Cancella le immagini dei progetti dormienti (aos, levity, caronte...): andranno ricostruite al loro prossimo avvio. Fai prima `docker system df` e valuta.
> - `docker volume prune -f` → rimuove volumi non agganciati a container. ⚠️ Possono contenere dati di progetti fermi.

### Passo 2 — Spegni Docker e WSL

Da PowerShell (basta utente normale):

```powershell
Get-Process '*docker*','*com.docker*' -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
Start-Sleep 3
wsl --shutdown
Start-Sleep 8
```

Il vhdx deve essere **non in uso** per poterlo compattare.

### Passo 3 — Compatta il vhdx (richiede PowerShell ADMIN)

> 🔴 **TRAPPOLA PATH**: la finestra Admin sulla macchina di riferimento gira sotto un account **diverso** (`usrv.l.scrimitore`). Lì `$env:LOCALAPPDATA` punta al profilo sbagliato e diskpart dà "file non esiste". **Usa sempre il path ASSOLUTO** del profilo `luigi.scrimitore`.

Nella finestra **PowerShell Admin**:

```powershell
$vhdx = "C:\Users\luigi.scrimitore\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
"Prima: $([math]::Round((Get-Item $vhdx).Length/1GB,1)) GB | C: libero: $([math]::Round((Get-PSDrive C).Free/1GB,1)) GB"
@"
select vdisk file=`"$vhdx`"
attach vdisk readonly
compact vdisk
detach vdisk
exit
"@ | diskpart
"Dopo: $([math]::Round((Get-Item $vhdx).Length/1GB,1)) GB | C: libero: $([math]::Round((Get-PSDrive C).Free/1GB,1)) GB"
```

Output atteso: il vhdx scende (es. 76 → 34 GB) e C: libero sale di conseguenza.

### Fine — Riavvia Docker Desktop

Riapri Docker Desktop normalmente dall'icona o dal menu Start.

---

## 4. Dettaglio tecnico: perché il compact a volte "non recupera nulla"

Il `compact vdisk` può restituire spazio **solo dai blocchi liberi marcati come sparse** dentro il filesystem ext4 della VM. Due cause tipiche di "recupero zero":

1. **Non hai liberato nulla prima** → il filesystem è pieno, non c'è spazio da compattare. *Soluzione*: esegui il Passo 1.
2. **I blocchi liberi non sono marcati** → su filesystem senza discard servirebbe un `fstrim` prima. *Sulla macchina di riferimento il filesystem monta con `discard` online*, quindi i blocchi cancellati sono già marcati automaticamente: un `fstrim` successivo trova solo ~100 MB residui (è **normale**, non un errore).

### Come ispezionare i mount dentro la VM (per debug)

Se devi capire dove vivono davvero i dati:

```powershell
docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -- df -h
```

- **`/dev/sdd` su `/mnt/docker-desktop-disk`** = disco dati reale (formattato 1 TB sparse, ~32 GB usati). **Questo** è il filesystem che conta.
- `/` (overlay, 9.8 GB) = root effimera della VM. **NON** zero-fillarla: si riempie dopo ~10 GB e non recupera nulla (bersaglio sbagliato — errore già commesso).

Se mai servisse forzare il trim sul mount giusto:

```powershell
docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -- fstrim -v /mnt/docker-desktop-disk
```

> Nota: `wsl -d docker-desktop -e /sbin/fstrim ...` **non funziona** su questa macchina perché `wsl --list` non mostra distro (Docker usa un backend che non registra distro WSL standard). Usa sempre il container privilegiato con `nsenter`.

---


### ⚠️ Correzione 2026-08-20 — il trim va fatto col metodo giusto E dopo aver liberato qualcosa

Caso reale che ha smentito la nota "2." qui sopra: vhdx 41 GB, solo 26 GB di dati Docker, `fstrim` **0 B**,
`compact` **0 GB**. Sembrava spazio non recuperabile. Erano due errori sovrapposti:

1. **Metodo di trim sbagliato**: usato `wsl.exe -d docker-desktop -e fstrim`. Il mapping dei device è
   sfasato tra i due contesti — da fuori `docker-desktop-disk` risulta `/dev/sdd`, da **dentro** la VM è
   `/dev/sde` — quindi si trimma il bersaglio sbagliato. Vale la regola già scritta sopra: **solo nsenter**.
   In Git Bash serve `MSYS_NO_PATHCONV=1`, altrimenti il path diventa `C:/Program Files/Git/mnt/...`:
   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --privileged --pid=host alpine \
     nsenter -t 1 -m -- fstrim -v /mnt/docker-desktop-disk
   ```
2. **Non c'era nulla da scartare**: `builder prune` = 0 B (cache già vuota) e il VACUUM aveva agito sul
   **warehouse**, che è bind-mount Windows → libera C: senza toccare il vhdx. Dentro ext4 nessuna
   cancellazione = niente da trimmare = niente da compattare.

Dopo la rimozione di ~10 GB di immagini di progetti dormienti, lo stesso comando ha scartato **23,9 GiB** e
il compact ha portato il vhdx **41 → 18,2 GB**, C: **9,2 → 31 GB** (**+22,8 GB**).

> **Regola**: se `fstrim` riporta ~0 B, **non** procedere al compact — torna a liberare dati (Passo 1).
> Un fstrim a ~0 è "normale" solo se hai appena compattato; dopo un prune sostanzioso deve riportare GB.

**Floor del vhdx**: ext4 è formattato 1 TB con 67M inode → la tabella inode occupa **~17 GB scritti
fisicamente**, che non sono spazio libero e nessun trim/compact recupera. Il vhdx non scende sotto
(dati + ~17 GB). Solo il reset del disco dati la ricrea, ed è **distruttivo**.

**Stop di Docker: graceful, non forzato.** `docker desktop stop` (CLI Docker Desktop) invece di
`Stop-Process -Force` del Passo 2: evita in partenza la corruzione dei socket descritta al §5.

**Prima di rimuovere immagini/volumi**: le immagini si ricostruiscono da Dockerfile, i **volumi no**.
Verifica sempre `docker system df -v` e fai il dump dei volumi con dati reali:
```bash
MSYS_NO_PATHCONV=1 docker run --rm -v <volume>:/src:ro -v /c/PROGETTI/_docker_backup:/dst \
  alpine tar czf /dst/<volume>.tar.gz -C /src .
```

## 5. Troubleshooting: Docker Desktop non parte dopo un kill forzato

### Sintomo

All'avvio compare:

> Docker Desktop encountered an unexpected error and needs to close.
> ```
> starting services: initializing Inference manager: listening on
> unix://...\Docker\run\dockerInference: remove ...\dockerInference:
> The file cannot be accessed by the system.
> (listener: The filename, directory name, or volume label syntax is incorrect.)
> ```

(Il nome del socket può variare: `dockerInference`, `engine.sock` in `docker-secrets-engine`, ecc.)

### Causa

I socket Unix (`AF_UNIX`) che Docker crea su Windows sono **reparse point**. Un kill forzato (`Stop-Process -Force`) li lascia in uno stato **corrotto**: non si cancellano in alcun modo (errore 1920 anche con `del`, `fsutil reparsepoint delete`, `[System.IO.File]::Delete`), e **sopravvivono al riavvio del PC**. All'avvio successivo Docker prova a rimuoverli, fallisce, e crasha.

### Fix (NON richiede admin, NON tocca le immagini)

Non si cancellano i file: si **rinomina la cartella** che li contiene. Rinominare la directory non apre i file corrotti dentro, e Docker ricrea cartelle fresche al riavvio.

```powershell
# 1. Assicura Docker spento
Get-Process '*docker*','*com.docker*' -EA SilentlyContinue | Stop-Process -Force -EA SilentlyContinue
wsl --shutdown
Start-Sleep 5

# 2. Trova e parcheggia TUTTE le cartelle socket coinvolte
$folders = @(
  "$env:LOCALAPPDATA\Docker\run",
  "$env:LOCALAPPDATA\docker-secrets-engine"
)
foreach ($f in $folders) {
  if (Test-Path $f) {
    $newname = (Split-Path $f -Leaf) + "_old_" + (Get-Random)
    Rename-Item -LiteralPath $f -NewName $newname -ErrorAction SilentlyContinue
    "Parcheggiata: $f -> $newname"
  }
}

# 3. Riavvia Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

Se al riavvio crasha su un **altro** socket, ripeti il Passo 2 aggiungendo la cartella citata nel nuovo messaggio d'errore. Docker avanza di un socket per volta finché non parte pulito.

Verifica engine attivo:

```powershell
docker version --format '{{.Server.Version}}'   # se risponde il numero, l'engine è su
docker images                                     # conferma che le immagini ci sono ancora
```

### ⚠️ Cosa NON fare

- **NON** affidarti a `docker save` come piano B per "salvare le immagini" se Docker non parte: `docker save` richiede l'**engine acceso**. Se Docker non avvia, non puoi esportare nulla. Per fortuna le immagini stanno nel vhdx e non sono a rischio — il problema sono solo gli stub dei socket.
- **NON** disinstallare/reinstallare Docker per questo problema: è sproporzionato e rischi di perdere il vhdx. Il fix delle cartelle socket risolve in pochi secondi.
- Le cartelle `*_old_*` parcheggiate si possono lasciare lì (sono innocue, 0 byte) o tentare di rimuoverle dopo un riavvio del PC.

---

## 6. Recupero spazio dal WAREHOUSE Delta (leva separata dal vhdx)

> **Quando serve**: C: pieno ma `docker system df` mostra **Build Cache reclaimable ~0** e il `compact` non recupera nulla. In quel caso lo spazio non è nel vhdx ma nel **warehouse**.
> **Verificato**: 2026-06-19 → warehouse da 24.94 GB a 7.45 GB, **17.5 GB liberati su C:** in ~3 min.

### Perché succede

Il warehouse (`C:\PROGETTI\LOGISTICO_DATA\data\warehouse`) è **bind-mount su C:**, NON dentro il vhdx → la procedura Docker (§1–5) non lo tocca.

Ogni `MERGE INTO` riscrive i file parquet e marca i vecchi come **tombstone** (non più referenziati dalla versione corrente, ma fisicamente ancora su disco). Con run ripetuti, le tabelle ad alto churn accumulano centinaia di parquet morti. Esempio reale: `bronze.storico_bolle` aveva 770 parquet di cui **668 (87%) rimovibili**.

I tombstone si eliminano **solo** con `VACUUM` — che legge il Delta log e cancella i file non referenziati. **Mai cancellare i parquet a mano**: si corrompe la tabella.

### Diagnosi: quali tabelle sono gonfie

```powershell
$wh = "C:\PROGETTI\LOGISTICO_DATA\data\warehouse"
Get-ChildItem $wh -Recurse -Directory -Force -EA SilentlyContinue |
  Where-Object { $_.GetFiles('*.parquet').Count -gt 0 } |
  ForEach-Object {
    $sz=(Get-ChildItem $_.FullName -File -Force -EA SilentlyContinue|Measure-Object Length -Sum).Sum
    [PSCustomObject]@{GB=[math]::Round($sz/1GB,2);Files=$_.GetFiles('*.parquet').Count;Path=$_.FullName.Replace($wh,'')}
  } | Sort-Object GB -Descending | Select-Object -First 15 | Format-Table -AutoSize
```

Conteggi parquet a 3 cifre per tabella = tombstone accumulati → candidata a VACUUM.

### Procedura (richiede Docker ACCESO)

Lo script `tests/local_bronze/vacuum_warehouse.py` percorre tutte le tabelle Delta del warehouse e fa `VACUUM RETAIN 0 HOURS` (sicuro in locale: sessione singola, nessun lettore concorrente; disabilita `retentionDurationCheck` per consentire retention < 168h).

```powershell
# 1. Anteprima (NON cancella): elenca i file rimovibili per tabella
docker exec logistico-spark python -u /workspace/code/tests/local_bronze/vacuum_warehouse.py --dry-run

# 2. VACUUM reale
docker exec logistico-spark python -u /workspace/code/tests/local_bronze/vacuum_warehouse.py
```

> ⚠️ **Usa sempre `python -u`** (unbuffered): senza, lo stdout di Python resta bufferizzato e se il processo viene killato (es. disco pieno) non vedi nessun output. Filtra il rumore Spark con `| Select-String -Pattern "VAC |TOTALE|DONE|Error|Exception"`.
> ⚠️ Su disco quasi pieno il listing è lento (~30–90 s/tabella). È normale, non è un blocco.

### Note operative

- `RETAIN 0 HOURS` cancella **tutti** i tombstone → niente più time-travel sulle versioni precedenti. In locale va bene; in cloud (PROD) usare la retention di default (7 gg) o concordata.
- A regime conviene una passata `vacuum_warehouse.py` periodica (es. settimanale o a fine pipeline) per evitare che il warehouse ricresca.
- Il VACUUM libera spazio **direttamente su C:** (warehouse è su Windows) — niente `compact` necessario dopo.

---

## 7. Checklist rapida (TL;DR)

**Via A — vhdx Docker** (quando Build Cache reclaimable è alta):
```
[ ] docker system df                      # diagnosi: guarda RECLAIMABLE
[ ] docker builder prune -f               # libera build cache (sicuro)
[ ] se reclaimable ~0: rimuovi immagini dormienti (backup volumi prima!)
[ ] fstrim via nsenter + MSYS_NO_PATHCONV=1  # DEVE riportare GB, non 0 B
[ ] docker desktop stop                   # graceful, non Stop-Process -Force
[ ] Stop-Process docker + wsl --shutdown  # spegni
[ ] (ADMIN) diskpart compact con PATH ASSOLUTO al vhdx di luigi.scrimitore
[ ] Riavvia Docker Desktop
```

**Via B — warehouse Delta** (quando Build Cache ~0 e compact non recupera → vedi §6):
```
[ ] Docker ACCESO
[ ] docker exec logistico-spark python -u .../vacuum_warehouse.py --dry-run   # anteprima
[ ] docker exec logistico-spark python -u .../vacuum_warehouse.py             # VACUUM reale
```

**Se Docker non parte** (crash su socket): spegni → rinomina cartelle `Docker\run` e `docker-secrets-engine` → riavvia Docker.

---

*Vincoli ambiente: lettura/modifica/esecuzione libere in project home + temp Claude. Oracle READ-ONLY. Dati reali mai su GitHub.*
