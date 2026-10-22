# ACT_9034 · Resilienza landing snapshot: anagrafiche/lookup non falliscono se manca il giorno

**Status**: done
**Type**: fix (robustezza pipeline)
**Origin**: incident 2026-10-22 — job `logistica_landing_ingestion` e `logistica_dim_refresh` FAILED
**Sprint**: trasversale / operatività DEV
**Created**: 2026-10-22   **Closed**: 2026-10-22   **Owner**: team
**OP collegati**: —   **Lesson**: [[LL-021]]

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

## Esito (VALIDATO 2026-10-22) ✅
- **Codice** (helper SSOT `resolve_landing_snapshot_path` + wiring 6 notebook): `py_compile` OK, unit test
  helper verde (giorno presente / fallback / nessuno / finestra lookback / folder-senza-file).
- **Wheel** `logistica_utils-1.0.0` ricompilato e **ricaricato sul Volume** `_wheels` (backup precedente in
  `_wheels/backup/…-20261022-103756.whl`); helper verificato nel wheel sul Volume.
- **Rilascio**: monorepo @333b57e → GitHub (lib/workflows/documentation) → GitLab **lib v1.0.8** + **workflows
  v0.1.19** (push solo main, no tag [[LL-031]]). `deploy_dev` (CI MI) = success; verificato che il notebook
  sul job MI contiene l'helper.
- **Re-run 22/10** (riproduce lo scenario, file del 22 assenti):
  - `logistica_landing_ingestion` run 389330436923961 = **SUCCESS**; i 5 bronze prima KO (`s_logistix`,
    `wl1_mag_sito_storico`, `apvpunto_vendita`, `buoni_eco`, `tipo_attivita`) = **SUCCESS** (fallback al 21/10).
  - `logistica_dim_refresh` run 426194327104925 = **SUCCESS**; `gold_lu_from_cdtdw` = **SUCCESS** (fallback).
- **Residuo lato odi3**: resta da capire perché l'estrazione anagrafiche/lookup del 22 non ha consegnato
  (relay, fuori da questo ambiente). Da domani la pipeline **non fallisce più** per un giorno mancante
  (usa l'ultimo snapshot entro 7 gg; oltre, torna a fallire per far emergere l'outage).
