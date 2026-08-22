# ACT_9003 · F_MOVIMENTAZIONE — arricchimento NUM_PLT (OP-MOV-1, opzione A)

**Status**: done   **Type**: feature   **Origin**: emerged (certifica F_MOVIMENTAZIONE vs famiglia CDT_DW)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 6 — Wave E (Carrellisti)
**Closed**: 2026-07-05
**Dipende da**: —   **Blocca**: —
**ADR collegate**: —   **OP collegati**: OP-MOV-1

## Contesto
La certifica (A0-A2, 2026-07-05) ha mostrato che il nostro `f_movimentazione_carrellisti` a grana
**giornaliera** (carrellista×giorno×sito) è più snello della famiglia CDT_DW (`F_MOV_CARR` per-movimento +
`F_OPER_CARR_LAV` ore + `F_MOV_ANN_CARR` rifiutati): mancava la misura **`NUM_PLT` (pallet movimentati)**. La
sorgente `DETTAGLIO_CARR` è però già in bronze → è una scelta di modellazione, non un blocco.

## Obiettivo
Colmare il gap misura mantenendo la grana giornaliera, senza ricostruire il per-movimento.

## Esito
**Opzione A**: mantenuta grana giornaliera + aggiunta `NUM_PLT_MOVIMENTATI` in `gold_f_movimentazione_carrellisti`
v3.1 (`SUM(2 se DOPPIO_MOVIM='SI' else 1)` per carrellista×giorno×sito, allineata a `F_MOV_CARR.NUM_PLT_MOV_CARR`;
`DOPPIO_MOVIM` già in `silver.missione_carrellista`). Validato 2026-06-10: 126 righe, `SUM(NUM_PLT)=3640` ≥
`SUM(NUM_MISSIONI)=3543` (97 doppi movimenti). Grana per-movimento e movimenti annullati = **sviluppo futuro
OP-MOV-1** (nessun blocco sorgente).
