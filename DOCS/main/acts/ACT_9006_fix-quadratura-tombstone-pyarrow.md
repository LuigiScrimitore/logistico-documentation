# ACT_9006 · Fix quadratura tombstone pyarrow (`live_delta_files` via `_delta_log`)

**Status**: done   **Type**: fix   **Origin**: emerged (CERT-01 / OP-CAR-4 causa A)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (tooling quadratura)
**Closed**: 2026-07-02
**Dipende da**: —   **Blocca**: affidabilità quadrature ([[ACT_9000]])
**ADR collegate**: —   **OP collegati**: OP-CAR-4 (causa A)

## Contesto
La quadratura mostrava il Gold gonfiato ~4× (F_CARICO Jun-17 a 200-300%): non un difetto pipeline ma della
**quadratura** stessa. `query_gold_kpi` leggeva TUTTI i parquet fisici via `rglob`, inclusi i **tombstone**
dei `full_refresh` (righe rimosse ma ancora su disco). Vedi [[delta-tombstone-pyarrow-read]].

## Obiettivo
Lettura Delta corretta da pyarrow (senza Spark), contando solo i file vivi.

## Esito
Aggiunto helper `live_delta_files()` in `scripts/quadratura/quadratura_fact.py` che legge il `_delta_log`
(add − remove + checkpoint) invece di `rglob` sui parquet. Elimina il gonfiaggio ~4×; la quadratura è ora
affidabile. Pattern riusabile per ogni lettura Delta via pyarrow.
