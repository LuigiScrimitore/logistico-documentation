# ACT_OP-35 · Watermark / controllo incrementale — rollout su tutti i _clean

**Status**: done   **Type**: feature   **Origin**: backlog W-01..W-06 / OP-35
**Sprint**: fuori-sprint (sviluppo tecnico offline)   **Fase / Wave**: trasversale (incrementalità Silver)
**Closed**: 2026-06-19
**Dipende da**: —   **Blocca**: W-05/W-06 (control catalog infra)
**ADR collegate**: ADR-0010 (incrementale 3 pilastri)   **OP collegati**: OP-35

## Contesto
Serviva un controllo incrementale per-sorgente sui notebook `_clean`, per non riprocessare l'intero storico
ad ogni run. Design (2026-06-14): tabella di controllo `control_<env>.etl.watermark`, chiave
`(stage, sistema, tabella, sito)`. Pilota su `silver_storico_liste_clean`.

## Obiettivo
Watermark transazionale (su FAIL non avanza) attivo su tutti i notebook `_clean`, con helper centralizzati
e test.

## Esito
Rollout completo (2026-06-19). Helper in `utils.py` (`get_control_table`, `ensure_watermark_table`,
`read_watermark`, `update_watermark`, `pending_landing_dates`) + layer `control` in `get_catalog`. Test
`tests/local_bronze/test_watermark.py` (ALL_OK). Coperti: `silver_storico_bolle_clean` (stat),
`silver_carichi_testate`/`silver_carichi_dettagli` (logistix), `silver_spedizioni_clean` (track),
`silver_ordini` (logistix), oltre al pilota `storico_liste_clean`. **Residui**: W-05 (`landing_to_bronze`
nell'orchestratore) e W-06 (deploy Terraform control catalog a regime) dipendono da infra control catalog
(I-02 / FASE 0).

## Follow-up
W-05/W-06 all'attivazione del control catalog su cloud → nuova ACT emergente se necessario.
