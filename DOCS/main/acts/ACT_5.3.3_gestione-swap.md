# ACT_5.3.3 · Gestione Swap (FLAG_SWAPPED, link ordine sostituto)

**Status**: done   **Type**: feature   **Origin**: sprint 5.3
**Sprint**: 5.3 — Gold F_ORDINI & F_TRASPORTO   **Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)   **Closed**: 2026-07-03
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto
Gli ordini possono essere sostituiti (swap): serve tracciare il flag e il link all'ordine sostituto in F_ORDINI. Vedi sprint 5.3 e ACT_5.3.1.

## Obiettivo
Gestione swap: FLAG_SWAPPED e link all'ordine sostituto.

## Esito
Consegnato: FLAG_SWAPPED e collegamento ordine sostituto integrati in `gold_f_ordini`.
