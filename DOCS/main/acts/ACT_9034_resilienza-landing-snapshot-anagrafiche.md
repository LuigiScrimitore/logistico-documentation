# ACT_9034 · Resilienza landing snapshot: anagrafiche/lookup non falliscono se manca il giorno

**Status**: in-progress
**Type**: fix (robustezza pipeline)
**Origin**: incident 2026-10-22 — job `logistica_landing_ingestion` e `logistica_dim_refresh` FAILED
**Sprint**: trasversale / operatività DEV
**Created**: 2026-10-22   **Closed**: —   **Owner**: team
**OP collegati**: —   **Lesson**: [[LL-040]]

## Sintomo
Run schedulate del 2026-10-22: `logistica_landing_ingestion` e `logistica_dim_refresh` **FAILED**.
Task falliti: `bronze_s_logistix`, `bronze_wl1_mag_sito_storico`, `bronze_apvpunto_vendita`,
`bronze_buoni_eco`, `bronze_tipo_attivita` (landing) e `gold_lu_from_cdtdw` (dim_refresh).
Le altre anagrafiche e tutte le transazionali (carichi/giacenze) = verdi.

## Diagnosi (misurata sui run)
- Errore reale dei task (da `get-run-output`): `[PATH_NOT_FOUND] Path does not exist:
  abfss://logisticolanding@.../cdt-estr-raw-landing/s_logistix/2026/10/22/*.csv. SQLSTATE 42K03`.
- **Causa 1 (dato)**: l'estrazione odi3 del 22/10 ha consegnato le transazionali e **parte** delle
  anagrafiche, ma NON queste 5 sorgenti + i lookup `cdtdw-landing` (consegna parziale, lato relay).
- **Causa 2 (codice)**: i bronze gestiscono il file mancante con `except AnalysisException ->
  dbutils.notebook.exit("NO_DATA")`. Ma su **serverless (Spark Connect)** `PATH_NOT_FOUND` è una
  `pyspark.errors...AnalysisException` che **NON** eredita da `pyspark.sql.utils.AnalysisException`
  (quella importata): l'except non la cattura → **task KO** invece dell'uscita pulita prevista.

## Obiettivo ("fatto" =)
Un giorno di **mancata consegna** di un'anagrafica/lookup **non fa fallire** la pipeline:
- il notebook rileva l'assenza **prima** della `spark.read` (nessuna eccezione sfuggita),
- usa l'**ultimo snapshot disponibile** (entro una finestra di lookback) → tabella FULL = stato corrente,
- se nessuno snapshot negli ultimi N giorni → `NO_DATA` pulito (non KO), e dopo N gg l'outage ri-emerge.

## Fix (design)
- **SSOT**: nuovo helper `resolve_landing_snapshot_path(day_path_fn, run_date, dbutils, max_lookback_days=7)`
  in `lib/logistica_utils/utils.py`. Prova `run_date`; se la cartella-giorno non ha file (verificato con
  `dbutils.fs.ls`, che cattura il path mancante), **retrocede** fino a `max_lookback_days` all'ultimo
  snapshot con dati. Ritorna `(data_effettiva, path)` o `(None, None)`. Non fa mai `spark.read` alla cieca.
- **Wiring** (solo snapshot FULL single-path, dove "ultimo vince" è corretto):
  `bronze_s_logistix`, `bronze_wl1_mag_sito_storico`, `bronze_apvpunto_vendita`, `bronze_tipo_attivita`
  (FULL_OVERWRITE), `bronze_buoni_eco` (DELTA_MERGE: re-merge idempotente dell'ultimo giorno),
  e `gold_lu_from_cdtdw` (per-tabella, nel loop L_*).
- `_bronze_load_date` resta = `run_date` (caricato oggi, contenuto = ultimo snapshot disponibile).
- Log WARNING esplicito quando scatta il fallback (giorno atteso vs giorno usato).

## Fuori scope (follow-up)
- Transazionali (carichi/pesate/giacenze) e SNAPSHOT giacenze: **NON** usano il fallback (fallback al
  giorno prima sarebbe semanticamente errato). Hanno lo stesso latente bug serverless sull'except: da
  convertire in uscita `NO_DATA` robusta (senza fallback) in un secondo giro — non toccato oggi.
- Anagrafiche multisito (logistix-landing per-sito): non coinvolte nell'incident, non toccate.
- Root cause lato odi3 (perché l'estrazione anagrafiche del 22 non ha consegnato): da verificare sul relay.

## Come verificarla
- Unit test locale dell'helper (giorno presente / assente+fallback / nessuno) = verde.
- Deploy dev (wheel sul Volume + bundle MI via CI) → re-run `logistica_landing_ingestion` e
  `logistica_dim_refresh` sul 2026-10-22 → **SUCCESS**, con WARNING di fallback sui 5+lookup e le FULL
  anagrafiche/LU che conservano l'ultimo snapshot (21/10).

## Esito (in corso — 2026-10-22)
- **Codice implementato + validato localmente** ✅
  - `utils.py`: helper `resolve_landing_snapshot_path` (SSOT). Unit test: giorno presente / fallback /
    nessuno / finestra lookback / folder-senza-file = tutti verdi.
  - Wiring nei 6 notebook (5 bronze + `gold_lu_from_cdtdw`). `py_compile` OK su tutti.
- **Wheel**: `logistica_utils-1.0.0` ricompilato da `lib/` e **ricaricato sul Volume** `_wheels`
  (backup del precedente in `_wheels/backup/…-20261022-103756.whl`). Verificato: l'helper è nel wheel sul Volume.
  Additivo/retro-compatibile → i notebook vecchi non ne risentono finché non vengono deployati.
- **Da fare per chiudere**: deploy notebooks ai job MI via GitLab `deploy_dev` (richiede VPN+PAT, push solo
  main, no tag [[LL-031]]) → re-run `logistica_landing_ingestion` + `logistica_dim_refresh` sul 22/10 →
  atteso SUCCESS con WARNING di fallback (snapshot 21/10). Poi worklog + indicazioni al team.
