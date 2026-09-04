# ACT_9027 · Run 7-job E2E — fix strutturali serverless/ANSI → 7/7 verde

**Status**: done
**Type**: fix
**Origin**: emerged (run completo dei 7 job DEV, richiesto per la fase di fix strutturale)
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: FASE 3 — E2E DEV (tutte le wave)
**Gg (stima)**: 1.5
**Blocco**: nessuno
**Created**: 2026-09-04   **Closed**: 2026-09-04
**Dipende da**: [[ACT_9026]] (canonico sito), [[ACT_CND-01]] (rimozione CND morto)
**Blocca**: —   **ADR collegate**: —   **OP collegati**: OP-TRA-1 (chiuso)

## Contesto e motivazione
Primo run completo E2E dei 7 job in DEV (run_date 2026-09-02): 1/7 verde. Raccolti status+errori
per job/task. La maggior parte dei rossi NON erano bug logici ma: (a) sorgenti CND morte, (b) cast
ANSI su dati legacy sporchi (serverless ha ANSI ON: un cast invalido LANCIA invece di dare null),
(c) una conf Spark vietata in serverless, (d) bronze che fallivano su path assente.

## Obiettivo
Portare i **7 job a verde** in DEV, con fix strutturali (non workaround), tracciati e riusabili.

## Analisi tecnica e interventi
**1. CND dead-code** ([[ACT_CND-01]], PR #5 mergiato nel branch): rimossi `bronze_giacenze_snapshot`,
`bronze_trasporti`, `bronze_vettori` + silver morti + task. `giacenze` usa `silver.t_stock` (da catena),
`trasporti`/`vettori` da TRACK. → giacenze + trasporti sbloccati.

**2. Serverless conf vietata**: `bronze_storico_liste` usava `spark.databricks.delta.schema.autoMerge.enabled`
(CONFIG_NOT_AVAILABLE) → sostituita con `.withSchemaEvolution()` sul merge builder (Delta 3.x). [[LL-028]]

**3. Cast/parse ANSI-safe su dati legacy sporchi** ([[LL-027]]): serverless ANSI ON → `cast`/`to_timestamp`
su valori sporchi (`'S'`, `'2.0'`, `'1.4'`, `'0'`, timestamp `'2026-09-01 603'`) lanciano. Sostituiti con
`try_cast`/`try_to_timestamp`:
- `julian_to_date` (wheel): reso ANSI-safe (cifre pure → JDN; fallback data/timestamp std). [[LL-022]] generalizzata.
- `silver_prep_riepiloghi`: cast numerici → `try_cast`.
- `silver_prep_prep_sped`: rimosso pre-`cast(long)` su LSPRL_DATA_PRELIEVO; `di` via `try_to_timestamp`;
  codici `BOL_COD_*`/`BOL_NRO_BOLLA`/`BOL_SPEDIZIONIERE` e prezzi `BOL_PRZ_*` via `try_cast` (il
  `coalesce(stringa, lit(0))` forzava coercizione a intero → crash su codice/prezzo decimale sporco).
- `silver_prep_turno_prep_sito`: `to_ts` via `try_to_timestamp`.
- `silver_sessione_carrellista`: `ORA_LOGIN/LOGOUT` via `try_cast timestamp`; `ORE_PRESENZA` via
  `try_cast decimal(6,2)` (durate anomale fuori range → NULL).
- **NB**: `F.try_cast` NON esiste in questa versione PySpark → usare `F.expr("try_cast(... as ...)")`.
  `F.try_to_timestamp` invece esiste. [[LL-027]]

**4. Bronze skip-safe su path assente** ([[LL-021]]): `bronze_cartellino`, `bronze_missioni_carr`,
`bronze_artdgene` (dismessa) — risoluzione EAGER (`df.columns`) nel try + `except Exception` → sito/sorgente
senza file viene skippato, il job non fallisce.

**5. Canonico sito numerico** ([[ACT_9026]]): completato su carichi/giacenze (full_refresh=OVERWRITE su
`silver_carichi_dettagli/testate/pesate`); `LU_SITO` espone `SITO_COD_ALFA`+`SITO_COD_MAG`+`SITO_DESC`.

## Verifica
Validati singolarmente in DEV (run_date 2026-09-02) — **7/7 verde**:
- landing_ingestion ✅ · dim_refresh ✅ · carichi ✅ (F_CARICO orphan 0) · trasporti ✅ · giacenze ✅
  (F_GIACENZE_DAILY popolata) · prep_sped ✅ (20/20) · datamart ✅ (12/12).

## Esito
7/7 job verdi in DEV. I fix sono strutturali (try_cast/try_to_timestamp, withSchemaEvolution, skip-safe,
canonico numerico) e coprono la classe "ANSI serverless + dati legacy sporchi" per riuso futuro.

## Lezioni
- [[LL-027]] (ANSI serverless: try_cast/try_to_timestamp; F.try_cast assente → expr).
- [[LL-028]] (serverless: niente spark.conf autoMerge → withSchemaEvolution).
- [[LL-021]] (path assente lazy → eager+skip), [[LL-022]] (JDN), [[LL-026]] (full_refresh=overwrite).

## Follow-up
- Valutare un pass sistematico `try_cast` sulle restanti silver STAT (stessa classe di dati sporchi).
- Seed reale `cartellino`/`dettaglio_carr` per validare i fact carrellisti a volume pieno (ora skip-safe).
