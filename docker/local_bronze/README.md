# Docker — Test Locale Bronze

Ambiente Docker containerizzato per eseguire i notebook Bronze fuori da Databricks,
sui CSV reali estratti con il landing simulator.

**Versione:** 1.0 — 2026-06-09
**Stack:** PySpark 3.5.0 + Delta Lake 3.2.0 + Java 17 (immagine `jupyter/pyspark-notebook:spark-3.5.0`).
**Allineato a Databricks Runtime 15.4 LTS** (OP-19).

## Prerequisiti

- **Docker Desktop** installato con backend WSL2 (gia' presente nel tuo ambiente).
- Cartelle host pronte (lo script landing_simulator deve aver gia' prodotto i CSV):
  - `C:\PROGETTI\LOGISTICO_DATA\data\landing\` (deve esistere)
  - `C:\PROGETTI\LOGISTICO_DATA\data\warehouse\` (verra' creata al primo run)

## Setup (una sola volta)

```powershell
cd C:\PROGETTI\LOGISTICO\docker\local_bronze

# Crea la cartella warehouse sull'host (Docker non la crea automaticamente)
New-Item -ItemType Directory -Force -Path C:\PROGETTI\LOGISTICO_DATA\data\warehouse | Out-Null

# (Opzionale) personalizza i path o la memoria Spark in un file .env
Copy-Item .env.example .env
# poi modifica .env se necessario

# Build dell'immagine (scarica ~1.5 GB la prima volta, poi cache locale)
docker compose build

# Avvio del container in background (resta attivo, headless)
docker compose up -d
```

Verifica che il container sia su:
```powershell
docker compose ps
# STATUS deve essere "running" o "Up X seconds"
```

## Esecuzione notebook Bronze

### Helper PowerShell (consigliato)

```powershell
# Smoke test: anagrafica multi-sito (FULL_OVERWRITE)
.\run.ps1 notebooks\bronze\anagrafiche\bronze_tabgen.py

# Test DELTA_MERGE su carichi
.\run.ps1 notebooks\bronze\carichi\bronze_carichi_testate.py --run-date 2026-06-09

# STAT prep-spedizioni
.\run.ps1 notebooks\bronze\prep_spedizioni\bronze_prep_riepiloghi.py

# Solo un sito
.\run.ps1 notebooks\bronze\carichi\bronze_pesate.py --siti lgax
```

L'helper:
1. Avvia automaticamente il container se non e' attivo.
2. Converte i path Windows → Linux.
3. Passa tutti gli argomenti extra a `run_notebook.py`.

### Comando docker diretto (equivalente)

```powershell
docker compose exec spark `
    python /workspace/code/tests/local_bronze/run_notebook.py `
        --notebook /workspace/code/notebooks/bronze/anagrafiche/bronze_tabgen.py `
        --landing /workspace/data/landing `
        --warehouse /workspace/data/warehouse `
        --run-date 2026-06-09
```

## Ispezione tabelle Delta

```powershell
# Tutte le tabelle in tutti i database
.\inspect.ps1

# Solo bronze_dev
.\inspect.ps1 --database bronze_dev

# Schema completo + 5 righe di una tabella specifica
.\inspect.ps1 --database bronze_dev --table sto_tes_carichi --schema --show 5
```

## Ciclo di lavoro tipico

```powershell
# 1. (Una volta) Setup
docker compose build
docker compose up -d

# 2. (Sviluppo) Esegui un Bronze, verifica, ripeti
.\run.ps1 notebooks\bronze\anagrafiche\bronze_tabgen.py
.\inspect.ps1 --database bronze_dev --table tabgen --show 3

.\run.ps1 notebooks\bronze\carichi\bronze_carichi_testate.py
.\inspect.ps1 --database bronze_dev --table sto_tes_carichi --show 5

# 3. (Stop a fine giornata)
docker compose stop

# 4. (Reset completo - quando vuoi ripartire da capo)
docker compose down -v
Remove-Item -Recurse -Force C:\PROGETTI\LOGISTICO_DATA\data\warehouse
New-Item -ItemType Directory -Force -Path C:\PROGETTI\LOGISTICO_DATA\data\warehouse | Out-Null
```

## Troubleshooting

### `docker compose build` fallisce con timeout
- Controlla connessione internet. Il primo build scarica ~1.5 GB.
- Se l'errore e' sul pre-cache delta jars: rimuovi temporaneamente il blocco `RUN python -c ...` dal Dockerfile, ribuilda; al primo `docker compose exec` i jar verranno scaricati al volo (~30s extra).

### "Permission denied" sui file montati
- Verifica che Docker Desktop abbia accesso alla cartella `C:\PROGETTI\LOGISTICO_DATA`:
  Settings → Resources → File sharing → aggiungi `C:\PROGETTI\LOGISTICO_DATA` (o `C:\PROGETTI`).
- Riavvia Docker Desktop dopo la modifica.

### "No such file or directory: /workspace/data/landing/..."
- La cartella landing host non esiste o e' vuota. Esegui prima il landing simulator:
  ```powershell
  cd C:\PROGETTI\LOGISTICO\scripts\landing_simulator
  py extract_oracle_to_landing.py --max-rows 50000 --query-timeout 300
  ```

### Container parte ma i comandi sono lenti
- Aumenta memoria driver in `.env`: `SPARK_DRIVER_MEMORY=6g`.
- Aumenta CPU/RAM Docker Desktop: Settings → Resources.
- `docker compose down && docker compose up -d` per applicare.

### Modifico un notebook ma il container vede ancora la vecchia versione
- Il mount del repo e' read-only ma riflette **in tempo reale** le modifiche fatte sull'host.
- Salva il file, rilancia `.\run.ps1 ...`. Non serve restart del container.

### Voglio vedere i log Spark dettagliati
- Modifica in `docker-compose.yml`: `JAVA_TOOL_OPTIONS: "-Dlog4j.rootCategory=INFO"`.
- `docker compose up -d --force-recreate spark` per applicare.

## Struttura warehouse persistito

Dopo i run, sull'host troverai:
```
C:\PROGETTI\LOGISTICO_DATA\data\warehouse\
├── bronze_dev.db\
│   ├── tabgen\          # Delta table
│   ├── sto_tes_carichi\
│   └── ...
├── silver_dev.db\
└── gold_prod.db\
```

Ogni cartella tabella contiene file Parquet (Delta) + `_delta_log/`. Persiste fra restart del container.

## Note

- I notebook girano con `env=dev` di default. Per testare il path prod: `.\run.ps1 ... --env prod` (produce tabelle in `bronze_prod`/`silver_prod`).
- Il container e' **headless**: nessuna porta esposta, no Jupyter web. Se in futuro serve, decommentare la sezione `ports` nel compose.
- Il fix di `get_catalog` (firma a 2 argomenti) e' gia' in `lib/logistica_utils/utils.py`: i notebook funzionano dentro Docker esattamente come funzioneranno su Databricks.
