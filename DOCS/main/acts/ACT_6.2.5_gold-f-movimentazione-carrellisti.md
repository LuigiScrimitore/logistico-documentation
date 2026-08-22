# ACT_6.2.5 · Gold `gold_f_movimentazione_carrellisti` (grana giornaliera, replaceWhere)

**Status**: done   **Type**: feature   **Origin**: sprint 6.2
**Sprint**: 6.2   **Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti   **Closed**: 2026-07-03
**ADR collegate**: ADR-0007 (standard 2-notebook), ADR-0008 (chiavi naturali Gold), ADR-0010 (incrementale)   **OP collegati**: OP-MOV-1, OP-27

## Contesto
Il fact carrellisti chiude la catena silver→gold della componente carrellisti di Wave E (Sprint 6.2),
alimentato da `silver_missione_carrellista` (ACT_6.2.3) e `silver_sessione_carrellista` (ACT_6.2.4).
È la base della vista KPI carrellisti (ACT_6.2.6).

> ⚠️ **Correzione naming 2026-08-04 ([[ACT_9008]])**: questa ACT parlava di un `gold_f_turno`, che **non
> esiste** nel repo. Il notebook/fact reale è **`gold_f_movimentazione_carrellisti`**
> (`notebooks/gold/carrellisti/gold_f_movimentazione_carrellisti.py`), orchestrato in
> `logistica_prep_sped.yml`. Il nome `gold_f_turno_prep_sito` è invece un **altro** fact (prep spedizioni,
> ACT_4.3.5) — da non confondere.

## Obiettivo
Gold carrellisti a **grana giornaliera** (`CARRELLISTA_COD × DATA_PRESENZA × SITO_COD`) con scrittura
idempotente per giorno.

## Esito
Consegnato `gold_f_movimentazione_carrellisti` (v3.1): grana giornaliera, `replaceWhere` su `DATA_PRESENZA`,
misure di presenza/attività (`ORE_PRESENZA`, `NUM_MISSIONI`, `NUM_CARICHI`, `NUM_RIEPILOGHI`,
`DURATA_TOT_MIN`) + **`NUM_PLT_MOVIMENTATI`** aggiunta in certificazione ([[ACT_9003]], allineata a
`F_MOV_CARR.NUM_PLT_MOV_CARR`). Base della vista KPI carrellisti (ACT_6.2.6). Nota OP-27: il Silver sessione
non espone `ORE_PRODUTTIVE` → i KPI usano `ORE_PRESENZA`. Grana per-movimento e movimenti annullati =
sviluppo futuro (OP-MOV-1).
