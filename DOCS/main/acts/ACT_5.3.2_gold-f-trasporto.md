# ACT_5.3.2 · gold_f_trasporto (lookup DIM_CORRIERE, costo/lead_time)

**Status**: done   **Type**: feature   **Origin**: sprint 5.3
**Sprint**: 5.3 — Gold F_ORDINI & F_TRASPORTO   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0013 (F_TRASPORTO grana MTV), ADR-0008 (chiavi naturali Gold)   **OP collegati**: OP-26

## Contesto
Fact trasporto a grana MTV (ADR-0013), alimentato da SPEDIZIONI@TRACK via landing (OP-26), con lookup corriere e misure costo/lead_time. Vedi sprint 5.3.

## Obiettivo
`gold_f_trasporto` con lookup DIM_CORRIERE, costo e lead_time.

## Esito
Consegnato (F_TRASPORTO ~23k righe nel big re-run). Chiavi naturali Gold (ADR-0008); grana MTV deliberata (ADR-0013).
