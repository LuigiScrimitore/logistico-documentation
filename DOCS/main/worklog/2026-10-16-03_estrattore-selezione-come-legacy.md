---
data: 2026-10-16
titolo: "Estrattore landing: selezione come il legacy (timbro ODI in sola lettura, righe collegate dai documenti) al posto della finestra sulle date"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "split dopo merge"
push_gitlab: "nessuno (estrattore sul relay odi3: copia a mano)"
act: [ACT_9030]
adr: []
lesson: [LL-006]
op: [OP-INF-4]
---

## Contesto
[[ACT_9030]]: con la finestra `[run_date−3, run_date]` sulla data ordine (`storico_liste`) e sulla data bolla
(`pesate`) si perdono i prelievi/carichi fatti più di 2 giorni dopo quella data (12/10: preparazioni al 47% e carichi al
14% del legacy). Il legacy invece parte dai documenti non ancora estratti (flag) e prende tutto ciò che è collegato.

## Modifica
- `scripts/landing_simulator/extract_oracle_to_landing.py`: chiave `selection` per tabella (`legacy_flag`, `parent`),
  funzione `selection_where` (ricorsiva sul padre, identificatori in whitelist, `pending_where` solo `COL = 'X' [AND ...]`),
  opzioni `--stamp-lookback-days` (2), `--stamp-from`, `--stamp-to` (esclusa, senza sospesi), `--pending-days` (30).
  Le tabelle senza `selection` restano a finestra sulla data (nessun cambio).
- `config.yaml`: `legacy_flag` su `sto_tes_carichi`, `pesate`, `tracciace178`, `dettaglio_carr`, `cartellino`,
  `abb_tolti`, `imbfmovim`, `testate_bolle` (sospesi = stato `E` + flag `N`); `parent` su `sto_righe_carico` (→ testate),
  `storico_liste` e `storico_bolle` (→ bolle), `storico_riepiloghi` (→ liste).
- `scripts/relay_azcopy/extract_and_send.sh`: variabile `EXTRACT_EXTRA` (opzioni in più all'estrattore, solo lanci a
  mano) + riga `extra` nel recap; README aggiornato.
- `tests/test_extract_selection.py`: 6 test sulla forma delle query (senza Oracle).

## Verifica contro Oracle (16/10, da PC, sola lettura)
Selezione con finestra chiusa sui timbri `[12/10, 16/10)` (quello che l'ODI ha preso il 12–15/10), confrontata con CDT_DW:

| giorno | liste selezionate per giorno di prelievo | legacy `F_PREP_SPED` | pesate selezionate per giorno di carico (19 siti) | legacy `F_CARICO` |
|---|---|---|---|---|
| 11/10 | 73.423 | 73.432 | 5.510 | 5.511 |
| 12/10 | 416.476 | 417.948 | 25.763 | 25.764 |
| 13/10 | 425.774 | 439.140 | 26.413 | 26.415 |
| 14/10 | 135.985 | 136.149 | 28.418 | 28.418 |
| 15/10 | — | — | 236 | 236 |

13/10 preparazioni: parte delle bolle timbrata il 16/10, fuori dalla finestra di prova. 09–10/10 bassi per lo stesso motivo
(timbrati prima del 12). La selezione riproduce il legacy.
`pytest tests/test_extract_selection.py tests/test_workflows_alignment.py`: 64 passed.

## Esito
- PR [#40](https://github.com/LuigiScrimitore/Logistico2.0/pull/40) mergiata; copia su odi3 fatta dall'utente (vedi diario
  [[ACT_9030]]: `--backup=numbered` toglie proprietario e permesso di esecuzione, ripristinati con `--reference`).
- Estrazione di recupero 01–16/10 (giorno per giorno, timbri `[D, D+1)`): 16/16 OK.
- Rilancio Databricks 01–16/10 + chiusura con `process_from=2026-09-30`: tutti i job SUCCESS (dopo le correzioni dei
  worklog 2026-10-16-04 e -05). Confronto con CDT_DW: **`F_PREP_SPED` = 100% del legacy ogni giorno dal 30/09 al 12/10**
  (12/10: 418.105 vs 417.948; prima 47%); `F_CARICO` dal 26–30% al **77–82%**, con tutti i 18 siti del legacy.
