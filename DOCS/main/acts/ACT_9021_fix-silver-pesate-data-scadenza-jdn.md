# ACT_9021 · Fix silver_pesate DATA_SCADENZA (JDN, non DATE)

**Status**: done   **Type**: fix   **Origin**: emerged
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 2 — Wave A Carichi   **Closed**: 2026-09-02
**ADR collegate**: —   **OP collegati**: —

## Contesto
`silver_pesate` faceva `.cast("date")` diretto su `DATA_SCADENZA` (Oracle `PSP_DATA_SCADENZA`), che in Logistix
è un **Julian Day Number** legacy. Il cast produceva anni assurdi → `gold_late_arriving_handler` crashava con
`ValueError: year 2461373 is out of range`. Distinto dai fix cast int (`NRO_COLLI`/`PZ_PER_CARTONE`) già su `main`.
Emerso col **seed storico** via `--ignore-odi-flag` ([[ACT_9020]]), che porta molte pesate con `DATA_SCADENZA`
valorizzata.

## Obiettivo
`DATA_SCADENZA` convertita con `julian_to_date` (come le altre date Logistix); LAD non crasha più.

## Esito
`notebooks/silver/carichi/silver_pesate.py`: import `julian_to_date` + `julian_to_date(F.col("DATA_SCADENZA"))`
al posto del cast. **PR #2** mergiato (`418be79`). Validato E2E in DEV (2026-09-02): 17.102/17.102 pesate con
`DATA_SCADENZA` corretta (min 2026, max 2031), `gold_late_arriving_handler` = `NO_LATE_ARRIVING`, zero
"year out of range". Residuo noto: 93 righe pre-fix in `silver_dev.logistica.pesata` da ripulire con full_refresh.

## Lezioni
- [[LL-022]] — Le date Logistix sono JDN, mai `.cast("date")` diretto (usa `julian_to_date`).
