# ACT_MNT-01 · Manutenzione disco Docker/warehouse (ricorrente, solo-locale)

**Status**: in-progress   **Type**: infra   **Origin**: backlog MNT-01, MNT-02
**Sprint**: fuori-sprint (manutenzione ricorrente)   **Fase / Wave**: trasversale (ambiente locale)
**Gg (stima)**: ricorrente   **Blocco**: 🟢 (solo-locale, non impatta cloud)
**Created**: 2026-07-05   **Closed**: — (ricorrente, mai "chiuso")
**Dipende da**: —   **Blocca**: run pesanti quando C: < 20 GB liberi
**ADR collegate**: —   **OP collegati**: R-06 (monitoraggio spazio C:)

## Contesto e motivazione
Le pipeline locali a 22 siti consumano molto spazio su C: (tombstone Delta + crescita `docker_data.vhdx`).
Serve una procedura ricorrente per recuperare spazio ed evitare SIGKILL/riempimento disco. **Solo-locale**:
a regime su Databricks non si applica.

## Obiettivo
Spazio disco locale sotto controllo dopo ogni run pesante: VACUUM warehouse eseguito nel runner; reclaim
vhdx disponibile on-demand.

## Analisi tecnica
- **MNT-01** — VACUUM warehouse Delta (tombstone) dopo ogni pipeline run: `tests/local_bronze/vacuum_warehouse.py`
  (già invocato dal runner).
- **MNT-02** — reclaim vhdx quando C: < 20 GB (R-06): ordine corretto = builder prune → **fstrim** via
  container privilegiato (Docker UP) → **Stop Docker** → **diskpart compact** (admin). Invertire l'ordine
  (compact senza fstrim) recupera 0 GB. **Ma anche nell'ordine giusto il compact recupera 0 GB se `fstrim`
  riporta ~0 B**: vedi Lezione 2. Vedi [[wsl-vhdx-disk-reclaim]] e [[warehouse-vacuum-disk-reclaim]].

## Sviluppo (diario)
- 2026-06-23 · pipeline 22 siti: fstrim (971 GiB trimmed) + compact → vhdx 83.4→37.1 GB, C: +47 GB.
- 2026-07 (sessione recente) · ripetuto reclaim → C: ~27 GB vhdx.
- 2026-08-20 (ACT_9005) · VACUUM mirato sulle 25 tabelle rigenerate: **0,82 GB** di tombstone
  (`gold_dev_logistica` 875 -> 354 MB, di cui ~500 MB su `f_prep_sped` dopo il DELETE della partizione
  `DATA_PREL IS NULL`). Poi `image prune` 82 MB + `volume prune` 680 MB. **fstrim: 0 B** su
  `/mnt/docker-desktop-disk` e compact 0 GB **col metodo sbagliato** (vedi Lezione 2); dopo rimozione di
  ~10 GB di immagini dormienti (ollama, kind, levity - autorizzate) + fstrim via nsenter: **23,9 GiB
  trimmati**, vhdx **41 -> 18,2 GB**, C: **9,2 -> 31 GB (+22,8 GB)**. Backup di `levity_postgres_data` in
  `C:PROGETTI_docker_backup` prima di toccare qualsiasi cosa. Reset del disco dati **non necessario**.

### Lezione 1 - VACUUM per-database con output unbuffered
Lanciare `vacuum_warehouse.py` su tutto il warehouse in un colpo solo, con l'output rediretto su file,
e' controproducente su bind mount Windows:
- `find_delta_tables` ordina **alfabeticamente**, quindi processa prima ~69 tabelle bronze **senza tombstone**
  e arriva alle gold (dove sta lo spazio) dopo decine di minuti;
- le `print()` Python sono **bufferate** sulla redirezione: si vedono solo i messaggi JVM di Delta e sembra
  che il processo sia bloccato.

Procedura corretta: un'invocazione **per database**, limitata a quelli rigenerati, con `PYTHONUNBUFFERED=1`:
```bash
for db in gold_dev_logistica.db gold_dev_logistica_dm.db silver_dev_logistica_curated.db; do
  MSYS_NO_PATHCONV=1 docker exec -e PYTHONUNBUFFERED=1 logistico-spark \
    python /workspace/code/tests/local_bronze/vacuum_warehouse.py \
    --warehouse "/workspace/data/warehouse/$db"
done
```
Minuti invece di ore, con avanzamento visibile tabella per tabella.

### Lezione 2 - il compact recupera solo cio' che il TRIM ha scartato: due errori da evitare
Primo tentativo 2026-08-20: `fstrim` 0 B, `compact` 0 GB su un vhdx da 41 GB con soli 26 GB di dati Docker.
Sembrava spazio intrappolato e non recuperabile. Erano **due errori sovrapposti**, entrambi risolti dal
manuale operativo `DOCS/guide_dev/manuale-recupero-spazio-docker.md`:

1. **Metodo di trim sbagliato.** Avevo usato `wsl.exe -d docker-desktop -e fstrim`, che il manuale (§4)
   dichiara **non funzionante su questa macchina**. Il mapping dei device e' sfasato tra i due contesti
   (da fuori `docker-desktop-disk` risulta `/dev/sdd`, da dentro la VM e' `/dev/sde`): stavo trimmando il
   bersaglio sbagliato. Il metodo corretto e' il container privilegiato con `nsenter`, e in Git Bash serve
   `MSYS_NO_PATHCONV=1` o il path viene mangiato:
   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --privileged --pid=host alpine \
     nsenter -t 1 -m -- fstrim -v /mnt/docker-desktop-disk
   ```
2. **Niente da scartare.** Il trim restituisce solo blocchi **liberati**. `builder prune` era 0 B (cache
   gia' vuota) e il VACUUM aveva agito sul warehouse, che e' **bind mount Windows** e libera C: senza
   passare dal vhdx: dentro ext4 non era stato cancellato nulla.

Dopo aver rimosso ~10 GB di immagini di progetti dormienti, lo stesso `fstrim` ha scartato **23,9 GiB** e il
compact ha portato il vhdx **41 -> 18,2 GB, C: da 9,2 a 31 GB (+22,8 GB)**.

**Sequenza corretta**: liberare dati dentro ext4 (prune/rimozione immagini) -> `fstrim` con nsenter ->
verificare che abbia scartato GB -> stop **graceful** di Docker (`docker desktop stop`, mai
`Stop-Process -Force`: corrompe i socket, manuale §5) -> `wsl --shutdown` -> `compact` con **path assoluto**.
Se il trim riporta ~0 B, non c'e' nulla da compattare: torna al passo 1, non al compact.

> Nota sul floor del vhdx: il filesystem ext4 e' formattato 1 TB con 67M inode, la cui tabella occupa
> ~17 GB scritti fisicamente. Non e' spazio libero e nessun trim/compact la recupera: il vhdx non scende
> sotto ~(dati + metadata). Solo il reset del disco dati la ricrea, ed e' distruttivo.

### Lezione 3 - distinguere il vincolo Docker dal vincolo C:
Il 2026-08-20 C: era pieno al 98% (435/444 GB) con il vhdx a soli 41 GB: **~394 GB stanno fuori da Docker**.
Prima di spendere tempo su VACUUM/prune/compact, verificare che il consumo sia davvero attribuibile a
Docker/warehouse, altrimenti la procedura MNT-02 recupera pochi GB su un problema di centinaia.

## Verifica
Post-procedura: C: sopra soglia e run pesante successivo senza SIGKILL memoria/disco. Il `docker_data.vhdx`
si riduce **solo** se `fstrim` aveva blocchi da scartare (Lezione 2); se il recupero e' arrivato dal VACUUM sul
bind mount, il vhdx resta invariato ed e' corretto cosi'.

## Esito
Procedura consolidata e ricorrente (non si chiude). Attivare quando R-06 scatta (C: < 20 GB).

## Follow-up
- Non applicabile su Databricks (ogni notebook = task isolato).
- Valutare l'ordinamento di `find_delta_tables` per dimensione decrescente (o un flag `--db`), cosi' il
  VACUUM attacca subito le tabelle dove sta lo spazio.
- Indagine aperta sui ~394 GB non-Docker su C: (fuori perimetro progetto, ma vincola i run pesanti).
- Alternativa a costo zero al reset Docker: spostare il warehouse fuori da C: (e' gia' bind mount, basta
  cambiare path).
