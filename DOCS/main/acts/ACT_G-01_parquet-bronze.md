# ACT_G-01 · Supporto Parquet in Bronze (auto-detect formato)

**Status**: done   **Type**: feature   **Origin**: backlog G-01 (gap spec Reply)
**Sprint**: fuori-sprint (sviluppo tecnico offline)   **Fase / Wave**: trasversale (Bronze)
**Closed**: 2026-06-20
**ADR collegate**: —   **OP collegati**: OP-07 (formato landing), OP-08

## Contesto
La spec Reply prevede che la landing possa fornire Parquet oltre a CSV (OP-07: "Parquet da abilitare in
futuro"). I notebook Bronze leggevano solo CSV con separatore hardcoded. Serviva rendere l'ingestion
agnostica al formato senza toccare 35 notebook a mano.

## Obiettivo
Bronze in grado di leggere CSV o Parquet dalla landing con auto-detect, via widget `file_format`.

## Esito
`detect_format` + `read_landing` centralizzate in `utils.py`; runner aggiornato con `--file-format`; **35
notebook bronze migrati** all'helper condiviso. CSV resta default (`;`); Parquet abilitabile senza modifiche
ai singoli notebook.
