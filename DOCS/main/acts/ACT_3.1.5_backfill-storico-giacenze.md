# ACT_3.1.5 · Backfill storico giacenze

**Status**: in-progress
**Type**: feature
**Origin**: sprint 3.1
**Sprint**: 3.1 — Bronze Giacenze
**Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (richiede cloud + ADLS)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_3.1.2, ACT_3.1.3, ACT_3.1.4   **Blocca**: quadratura storica giacenze
**ADR collegate**: ADR-0010 (incrementale)   **OP collegati**: —

## Contesto e motivazione
I bronze giacenze (ACT_3.1.2–3.1.4) coprono lo snapshot corrente; per avere una serie storica delle
giacenze occorre ricaricare i giorni pregressi dagli estratti storici presenti su ADLS. Senza backfill
il datamart mensile `A_GIACENZE_MONTHLY` / `A_STOCK_MENSILE` e gli aging (KPI `kpi_aging_articoli`
30/60/90/180+, ACT_3.3.5) non hanno profondità temporale: aggregano solo il singolo snapshot corrente.

Il pattern dei bronze giacenze è **SNAPSHOT** (`02_pipeline_mapping.md` §Giacenze, MODE C): ogni giorno
è una fotografia storicizzata, partizionata per data. Le tabelle interessate sono
`bronze.logistica.t_stock` (CND, ~150k righe/g), `bronze.logistica.catena` (~158k/g) e
`bronze.logistica.catena_esterni` (~5.3k/g). A differenza delle entità transazionali (MERGE), qui il
backfill NON è un ricalcolo incrementale ma un ripopolamento giorno-per-giorno delle partizioni mancanti.

## Obiettivo
Storico giacenze ripopolato sui bronze snapshot per l'intervallo di date pregresso. Fatto = per ogni
giorno target esiste la partizione `_bronze_load_date = <giorno>` nei bronze giacenze
(`t_stock`, `catena`, `catena_esterni`), leggibile a valle da silver/gold senza buchi nella serie.

## Analisi tecnica
- **Meccanismo**: rieseguire i notebook bronze per ogni `run_date` storico. La scrittura è idempotente:
  `bronze_giacenze_snapshot.py` fa `mode("overwrite")` con `replaceWhere _bronze_load_date = '{run_date}'`
  e `partitionBy("_bronze_load_date")` → rieseguire lo stesso giorno sovrascrive solo quella partizione,
  senza raddoppio e senza toccare lo storico già presente.
- **Path landing storico** (da `bronze_giacenze_snapshot.py`, funzione `landing_path()`):
  `{landing_base_path}/{source_system}-landing/{table}/{year}/{month}/{day}/` — es. per T_STOCK:
  `abfss://logistica@<storage>.dfs.core.windows.net/cnd-landing/t_stock/YYYY/MM/DD/`. Formato CSV
  (sep `;`, header, UTF-8) o Parquet, auto-detect via `detect_format`. Se il file del giorno non esiste
  il notebook esce `NO_DATA` (graceful) → nessun blocco, ma quel giorno resta mancante.
- **Sorgente storica su ADLS**: accessibile solo in cloud → non eseguibile offline. Vincolo confermato
  dal blocco `☁️ cloud/PROD`.
- **Coordinamento**: il ripopolamento va allineato al big re-run multisito (memoria progetto
  "Big re-run pending") per non desincronizzare i 22 siti; i notebook bronze catena sono multisito
  (path `logistix-landing/{sito}/catena`), quindi il backfill catena va iterato su siti × giorni.
- **Nota path convention**: `bronze_giacenze_snapshot.py` segnala che la struttura landing è *pending
  OP-07* (struttura Foconi da confermare con Reply) → validare la convenzione path prima del run massivo.
- **Ordering (OP-29)**: non impatta il Bronze (nessuna dipendenza inter-tabella in bronze); il vincolo
  di ordinamento `silver_t_stock` ↔ `silver_catena_unificata` è a valle (vedi [[ACT_3.4.1_workflow-giacenze]]).
  In cloud il DAG del workflow garantisce l'ordine; localmente è fisiologico. Per il backfill basta
  che, giorno per giorno, il bronze sia completo prima di rilanciare i silver di quel giorno.

## Sviluppo (diario)
- 2026-07-03 · avanzamento ~20%; logica pronta (notebook bronze idempotenti), esecuzione bloccata su
  accesso cloud/ADLS.

## Verifica
- Conteggio partizioni `_bronze_load_date` distinte vs elenco giorni attesi per `t_stock`, `catena`,
  `catena_esterni` (query `SELECT _bronze_load_date, COUNT(*) ... GROUP BY _bronze_load_date`).
- Letture a campione dei giorni storici: verificare `rows_read > 0` e assenza di gap nella sequenza date.
- Nessun raddoppio: rieseguendo un giorno già caricato il count della partizione resta stabile
  (idempotenza `replaceWhere`).
- A valle: i giorni storici devono propagarsi fino a `F_GIACENZE_DAILY` e all'aggregato mensile.

## Esito
— (in attesa di accesso cloud + ADLS)

## Follow-up
Nessuna finché non sblocca il cloud.
