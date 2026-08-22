# ACT_RS-01 · Rimozione rami secchi (8 notebook obsoleti)

**Status**: done   **Type**: fix   **Origin**: backlog RS-01..RS-08
**Sprint**: fuori-sprint (manutenzione codebase)   **Fase / Wave**: trasversale (pulizia)
**Closed**: 2026-06-20
**ADR collegate**: ADR-0007 (standard 2-notebook, che ha reso obsoleti alcuni percorsi)   **OP collegati**: —

## Contesto
Dopo il ridisegno "scelta B / standard 2-notebook" e il passaggio alle sorgenti Logistix reali, alcuni
notebook leggevano tabelle non estratte o producevano output non consumato a valle: rami secchi da rimuovere
per non confondere il codebase.

## Obiettivo
Eliminare i notebook morti (sorgente inesistente o output non consumato) senza impattare il flusso.

## Esito
Rimossi 8 notebook: `bronze_pdv` (RS-01, PDV arriva da CDT_DW), `silver_t_pdv` (RS-02, output non consumato),
`silver_swap` (RS-03), `silver_prep_sped_integrata` (RS-04, sostituito da `silver_prep_prep_sped`),
`silver_timbrature_sessioni` (RS-05), `silver_costo_trasporto` (RS-06), `silver_t_prep_sped` (RS-07, già
DEPRECATED, sostituito da `silver_prep_prep_sped`), `silver_trasp_mtv_build` (RS-08, già DEPRECATED,
sostituito da `silver_prep_trasporto`). Rimosso anche `silver_t_pdv` dalla SILVER_CLEAN list di
`tests/local_bronze/run_big_rerun.py`.
