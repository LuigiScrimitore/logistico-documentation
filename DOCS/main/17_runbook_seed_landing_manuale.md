# 17 · Runbook — Seed manuale della landing DEV (workaround pre-AzCopy)

**Owner:** Team Logistico 2.0 · **Creato:** 2026-09-01 · **Stato:** interim
**Scopo:** finché l'ingestion via **AzCopy/ODI** ([[ADR-0023]]) non è attiva, alimentare la landing DEV
**a mano** con **fotografie giornaliere** estratte in locale, per far girare e validare la pipeline in cloud.
**Baseline = 2026-09-01** (poi si valuta se/come backfillare all'indietro).

> Interim: questo giro sostituisce temporaneamente il push AzCopy. Quando arriva il container (§F.2), il
> trasporto passa ad AzCopy e questo runbook si ritira. CDT_DW resta **solo** bridge lookup (OP-02) + quadratura,
> **non** una sorgente ([[cdtdw-non-e-sorgente]]).

## Modello operativo (ciclo giornaliero)
```
[1] estrai la fotografia di OGGI in locale  → landing_data/  (pulito, solo oggi)
[2] copia landing_data sul Volume DEV        (databricks fs cp --recursive)
[3] lancia i job in DEV e valida
[4] giorno dopo: ripeti [1]-[3] con run_date = nuovo giorno
```
Il **Volume accumula** la storia (day1 `…/09/01/`, day2 `…/09/02/`…); lo **stage** locale è solo del **giorno**
(svuotato ad ogni run). Ogni giorno viene **archiviato in zip** (`landing_archive\snap_YYYYMMDD.zip`, ricaricabile
se si ripulisce Azure). Nessuna cartella da creare a mano sul Volume, nessuna delete lato Volume.

## Automazione — wrapper `seed_landing_dev.ps1`
Il ciclo estrai→copia→archivia→pulisci è in un solo comando: `scripts/landing_simulator/seed_landing_dev.ps1`
(fa i §1–§4 sotto + archivio zip). Prerequisiti: `py -3` con accesso Oracle + Databricks CLI configurata (§2-§3).
```powershell
# fotografia di oggi, fetta minima (un sito + poche tabelle):
cd C:\PROGETTI\LOGISTICO\scripts\landing_simulator
.\seed_landing_dev.ps1 -Sites lgcx -Tables sto_tes_carichi,sto_righe_carico,pesate,tabgen
# anteprima senza eseguire:  -DryRun     |  giorno specifico:  -RunDate 2026-09-01
# ri-seed su Azure da archivio (no estrazione):  -ReseedZip <...\snap_20260901.zip>
```
Default: `-Systems logistix,stat` (per l'export quadratura CDT_DW aggiungi `cdt_estr`); lo stage viene zippato
in `landing_archive\` e svuotato. Le sezioni sotto restano il **dettaglio manuale** dei singoli passi.

---

## 1. Estrazione locale (fotografia del giorno)
Path **nuovo e pulito**, separato dai 31 GB storici (fermi a inizio luglio):
`C:\PROGETTI\LOGISTICO_DATA\landing_data`

Svuota lo staging, poi estrai con `run_date`/`to_date` = oggi e `--output-dir` sul nuovo path:
```powershell
Remove-Item -Recurse -Force C:\PROGETTI\LOGISTICO_DATA\landing_data\* -ErrorAction SilentlyContinue

# Operativi (Logistix/STAT/TRACK). Per la prima fetta: un sito + poche tabelle.
cd C:\PROGETTI\LOGISTICO\scripts\landing_simulator
py -3 extract_oracle_to_landing.py --to-date 2026-09-01 `
   --output-dir C:/PROGETTI/LOGISTICO_DATA/landing_data --query-timeout 3600
   # opz. per fetta minima: --sites lgcx --tables sto_tes_carichi,sto_righe_carico,pesate,tabgen

# Lookup master (bridge OP-02) + export quadratura. Le LU_* cambiano lente: non serve ogni giorno.
cd C:\PROGETTI\LOGISTICO\scripts\cdtdw_lookup_extractor
py -3 extract_cdtdw_lookups.py --run-date 2026-09-01 `
   --output-dir C:/PROGETTI/LOGISTICO_DATA/landing_data
```
Risultato: `landing_data/<source>-landing/[sito/]<tabella>/2026/09/01/<tabella>.csv` (separatore `;`).

## 2. Databricks CLI — installazione (una tantum, Windows)
Usare la **CLI nuova/unificata** (Go, v0.2xx). Metodo **raccomandato** dai doc Databricks (Windows): **winget**.
```powershell
winget install Databricks.DatabricksCLI    # poi riapri il terminale
databricks -v                              # atteso v0.2xx ; aggiornamento: winget upgrade Databricks.DatabricksCLI
```
Alternative ufficiali: **download diretto** dello `…_windows_amd64.zip` da github.com/databricks/cli/releases →
estrai `databricks.exe` in una cartella su PATH; oppure **Chocolatey** (`choco install databricks-cli`, marcato
*experimental*); oppure **WSL** (metodo curl).

> ⚠️ **Non usare** `pip install databricks-cli`: è la **CLI legacy** (Python, v0.17.x) — **deprecata**. È una cosa
> diversa dalla CLI nuova; i comandi qui (`databricks fs cp --recursive`, auth) sono per la **nuova** CLI.

## 3. Autenticazione (una tantum)
Genera un **Personal Access Token**: Databricks → avatar in alto a dx → **Settings → Developer → Access tokens → Generate**.
```powershell
databricks configure --token
#   Host:  https://adb-3179436993731139.19.azuredatabricks.net
#   Token: <il PAT>
databricks fs ls dbfs:/Volumes/landing_dev/logistica/files   # verifica connessione
```
Se la piattaforma disabilita i PAT: `databricks auth login --host https://adb-3179436993731139.19.azuredatabricks.net` (OAuth via browser).

## 4. Copia della fotografia sul Volume DEV
Root Volume: `dbfs:/Volumes/landing_dev/logistica/files`. Copia ricorsiva (ricrea da sola tutti i sottopath):
```powershell
databricks fs cp --recursive --overwrite `
  "C:/PROGETTI/LOGISTICO_DATA/landing_data/logistix-landing" `
  "dbfs:/Volumes/landing_dev/logistica/files/logistix-landing"
# ripeti per: cdtdw-landing, stat-landing, track-landing (solo quelli estratti)

databricks fs ls dbfs:/Volumes/landing_dev/logistica/files/logistix-landing   # verifica
```
Poiché `landing_data` contiene solo oggi, copi solo oggi. Il Volume accumula i giorni.

## 5. Run pipeline in DEV
- **Ordine DAG**: dimensioni → fact → aggregati (dim **prima**, sennò orphan — regola OP-29/DAG).
- **Preferisci i job deployati** (Jobs & Pipelines) al notebook interattivo: così a run-time il wheel arriva dal
  **Package Registry** (valida **DBR-05**) e non dipendi dal `sys.path` dei notebook.
  - `logistica_dim_refresh` (dims) → poi `logistica_carichi` (F_CARICO) → altri fact/aggregati.
  - Parametri: `run_date=2026-09-01`, `landing_base_path=/Volumes/landing_dev/logistica/files`.

## 6. Validazione
- Conteggi bronze/silver/gold, **orphan-rate** (target 0), esito **dq_gate**.
- ⚠️ **Quadratura vs CDT_DW NON significativa al giorno 1**: CDT_DW ha la storia piena di produzione, noi 1 giorno
  → tutte le chiavi risultano "solo in ODI" per **copertura**, non per errore di calcolo ([[OP-QDR-1]]). Al giorno 1
  si valida **funzione/plumbing**, non i numeri. La quadratura diventa significativa man mano che la copertura cresce.

## 7. Giorni successivi
Ripeti §1→§6 con `run_date` = giorno corrente. Il **watermark** (`config_dev.logistica_etl`) gestisce
l'incrementale: primo giorno = baseline, poi solo il delta.

## Note e limiti
- **Snapshot facts** (`F_GIACENZE_DAILY`): la storia stock **parte da 2026-09-01** e **non è backfillabile**
  ([[OP-GIA-1]]). I fact **transazionali** sì (estrai date passate con `--from-date/--to-date`).
- **Lookup CDT_DW**: lente → non serve estrarle ogni giorno (il notebook fa MERGE dove serve).
- **Futuro — Parquet**: i Bronze leggono già `csv|parquet` (auto-detect, C2). Basterà far scrivere Parquet agli
  extractor. **Da fare dopo** il primo run cloud completo in CSV (attenzione: Parquet porta i **tipi**, il CSV è
  tutto stringa → verificare eventuali differenze di tipo a valle).
- **Auth**: il PAT è **personale** (dell'utente), diverso dalla Managed Identity della CI ([[ADR-0022]]).
