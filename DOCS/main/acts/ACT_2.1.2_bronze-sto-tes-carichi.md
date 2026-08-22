# ACT_2.1.2 · bronze_sto_tes_carichi (22 siti, DELTA_MERGE + row_hash)

**Status**: done   **Type**: feature   **Origin**: sprint 2.1
**Sprint**: 2.1   **Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0010 (incrementale watermark)   **OP collegati**: —

## Contesto
Ingestion testate carico su 22 siti in Bronze, con MERGE incrementale e row_hash per il change-detection. Rif. mapping in ACT_2.1.1.

## Obiettivo
Notebook `bronze_sto_tes_carichi` che carica le testate su tutti i 22 siti con MERGE Delta null-safe e row_hash.

## Esito
Consegnato `bronze_sto_tes_carichi` (DELTA_MERGE + row_hash), chiave MERGE null-safe `<=>`. Testato in locale.
