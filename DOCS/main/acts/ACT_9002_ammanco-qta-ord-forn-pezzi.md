# ACT_9002 · Ammanco QTA_ORD_FORN in pezzi (OP-CAR-3, opzione B)

**Status**: done   **Type**: fix   **Origin**: emerged (OP-CAR-3 quantità ordinata fornitore)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (Wave A Carichi / aggregati)
**Closed**: 2026-07-05
**Dipende da**: [[ACT_9001]] (catena silver carico)   **Blocca**: `kpi_qualita_ricevimento`, misure scarto A_INBOUND
**ADR collegate**: ADR-0012 (ammanco in pezzi, unità omogenea)   **OP collegati**: OP-CAR-3

## Contesto
`QTA_ORD_FORN` (quantità ordinata fornitore, catena WL4) era degenere/forzata a 0 → scarto ricevimento non
calcolabile, `A_INBOUND` senza misure di scarto e `kpi_qualita_ricevimento` bloccata. La formula legacy ODI
è auto-cancellante (bug latente): l'invariante reale è che `SUM(QTA_ORD_FORN)` per gruppo = `MAX_QTA_ORD`.

## Obiettivo
Ripristinare `QTA_ORD_FORN` in modo che quadri vs CDT_DW per SUM, con unità coerente (pezzi) per calcolare
l'ammanco.

## Esito
**Opzione B (equivalente pulito)**: `silver_prep_carico` porta `QTA_ORDINATA` (da `carico_dettaglio`) e la
assegna alla **prima etichetta** del gruppo (SITO, ORDINE, ART_RADICE, ART_VAR) via `row_number`
deterministico (order by `ETICHET_NRO`), 0 alle altre → `SUM(QTA_ORD_FORN)` = `MAX_QTA_ORD` legacy. Validato
re-run 2026-07-05: `SUM=1.921.348` (prima 0), 38.210 gruppi. **Unità (ADR-0012)**: `QTA_ORD_FORN` in
**COLLI**, `QTA_CARICO` in **PEZZI** → ammanco calcolato in pezzi: `A_INBOUND.QTA_ORDINATA_TOT =
SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN)` → **+253.243 pz = 1.51%** (prima −14.6M per unità miste). Rimossa
la colonna morta `AMMANCO_QTA` da `carico_dettaglio` (ammanco = concetto d'ordine, non di riga).
