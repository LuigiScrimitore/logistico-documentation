---
data: 2026-09-03
titolo: "E2E giacenze/trasporti: ACT_9024 validato; blocco sito sistemico (OP-TRA-1)"
autore: Francesco Foconi
push_monorepo: e5edcdc
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9024, ACT_ST-01]
adr: []
lesson: [LL-021]
op: [OP-TRA-1]
---

## Cosa e' stato fatto
- **[[ACT_9024]] done** (PR #4 mergiato): `bronze_movimenti_magazzino` ora skippa il sito senza file (pattern
  [[LL-021]], `df.columns` eager). Validato E2E: non è più il blocco, la catena giacenze arriva a
  `catena_unificata` (44.094 righe).
- Diagnosticati a fondo i 2 blocchi residui dei run E2E giacenze/trasporti (rimozione [[ACT_CND-01]]).

## Novita' — blocco sito SISTEMICO (impatta trasporti E giacenze)
- **[[OP-TRA-1]] esteso**: `MAG_SITO_COD` ha **3 formati** incoerenti → `catena`=`lgax` (minuscolo),
  `struttura_mag`/`lu_sito`=`LGAX` (MAIUSCOLO), `spedizioni@track`=`20` (numerico).
  - Trasporti: `gold_f_trasporto` orphan sito **100%** (numerico ≠ alfabetico).
  - Giacenze: `silver_t_stock` = **0 righe** → `F_GIACENZE_DAILY` vuota; join case-sensitive `lgax`≠`LGAX`.
    Il commento "FIX OP-29" in `silver_t_stock.py` è datato/errato (dice catena=`20` numerico).
- **[[ACT_ST-01]]**: annotato che il vuoto F_GIACENZE_DAILY è il **case sito** (OP-TRA-1), non il valore stock.
- **Proposta al team**: canonico sito = **MAIUSCOLO** (formato `lu_sito`), normalizzare a monte `catena`+`spedizioni`.
  Serve conferma canonico + lookup numerico→alfabetico per spedizioni (diagnosi girata a Luigi 2026-09-03).

## Doc aggiornati
- `acts/ACT_9024.md` (done), `acts/ACT_ST-01.md` (nota), `05_open_points.md` (OP-TRA-1 sistemico),
  `15_backlog_master.md` (9024 done). (Fix `bronze_movimenti_magazzino.py` già su main via PR #4.)

## Stato dopo il push / prossimi passi
- **ACT_9024**: chiuso. **ACT_CND-01** (rimozione rami morti cnd): validata E2E lato struttura, **PR in apertura**
  (branch `feat/act-cnd-01-remove-dead-cnd`), lasciato a revisione team (refactoring ampio area Luigi).
- **Bloccante per giacenze/trasporti a gold**: fix sito sistemico (OP-TRA-1) — attende conferma team sul canonico.
  Finché non risolto, `F_TRASPORTO`/`F_GIACENZE_DAILY` non passano il dq_gate (temi di mapping, non di struttura).
