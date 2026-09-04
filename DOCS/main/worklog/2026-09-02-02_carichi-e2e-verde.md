---
data: 2026-09-02
titolo: Carichi E2E verde su dato reale; dim_refresh 17/17; aperta ACT_CND-01 (bronze cnd)
autore: Luigi Scrimitore
push_monorepo: 45f8224
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_CND-01]
adr: [ADR-0025]
lesson: [LL-020, LL-021]
op: [OP-CND-1]
---

## Cosa e' stato fatto
- **Seed mirato** delle sorgenti mancanti per 2026-09-01: `cdt_estr_raw` (automezzi, apvpunto_vendita) + `track`
  (vettori 96, spedizioni 3466) — il seed "completo" precedente era solo logistix+stat+cdtdw.
- **trasporti**: da 4 a **11/14** (track/cdt_estr ok, incluso `bronze_vettori_track` che serve a carichi).
- **dim_refresh 17/17**: fix dedup in `gold_lu_from_cdtdw` (`dropDuplicates` sulla chiave prima del MERGE ->
  risolve `MULTIPLE_SOURCE_ROW_MATCHING`); `silver/gold_dim_corriere` verdi -> **`LU_CORRIERE` creata**.
- **CARICHI 14/14 sul dato reale**: `F_CARICO` = **1498 righe**, `F_TRACCIABILITA_LOTTI` = 3511, DQ tracciabilita
  33/33 e carichi 16/18 (2 solo WARNING) -> **`dq_gate` verde**. Il DQ finding di stamattina e' chiuso.

## Novita'
- **DQ finding = watermark** (non qualita' dato): ri-seed dello stesso run_date -> filtro incrementale scarta
  tutto. Reset watermark -> reprocess full. (Gotcha operativo.)
- **ACT_CND-01 + OP-CND-1** (aperti): 3 Bronze leggono ancora la sorgente **`cnd` dismessa** (SCELTA B) ->
  `bronze_vettori`/`bronze_trasporti`/`bronze_giacenze_snapshot`. Rework di **design** (repoint a track/logistix,
  rebuild MTV da spedizioni) -> blocca gold trasporti/giacenze/prep_sped. Non hackerato (niente masking).

## Doc aggiornati
- `acts/ACT_CND-01` (nuovo) · `05_open_points` (OP-CND-1 + tabella) · `15_backlog_master` (CND-01) · worklog.

## Stato dopo il push / prossimi passi
- **carichi** ✅ E2E + DQ · **dim_refresh** ✅ 17/17 · **trasporti** 11/14 (bloccato su OP-CND-1) ·
  giacenze/prep_sped: da fare (stessa OP-CND-1 + seed cnd dismesso). **aggregati**: dipende dai gold.
- Prossimo: **ACT_CND-01** (design repoint cnd, serve intento dominio sul rebuild MTV). Poi giacenze/prep_sped/aggregati.
- `databricks.yml` root_path->home resta locale. Provisioning wheel = interim `%pip` ([[ADR-0025]]).
