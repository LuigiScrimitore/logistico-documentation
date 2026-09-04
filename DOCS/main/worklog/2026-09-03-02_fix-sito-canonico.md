---
data: 2026-09-03
titolo: "Fix sito canonico alfabetico: giacenze verde, trasporti parziale (OP-TRA-1) + LL-025"
autore: Francesco Foconi
push_monorepo: bae018f
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9025]
adr: []
lesson: [LL-025]
op: [OP-TRA-1]
---

## Cosa e' stato fatto
- Risolto il canonico sito **su base dati** (non a naso): `F_CARICO.SITO_COD`=`LGAX`… aggancia `LU_SITO` a **0%
  orphan** → canonico = **ALFABETICO MAIUSCOLO** (il "numerico" del commento in `get_sito_alias_map` è obsoleto).
- **[[ACT_9025]]** (PR #6): `silver_t_stock` con `upper` (giacenze) + `silver_spedizioni_clean` mappa num→alfa da
  TABGEN (trasporti).

## Novita'
- **Giacenze ✅ RISOLTO** (validato E2E in DEV, run_date 2026-09-02): `logistica_giacenze` gate verde,
  `F_GIACENZE_DAILY` popolata, orphan 0. (Chiude anche il ramo giacenze della rimozione [[ACT_CND-01]], PR #5.)
- **Trasporti 🟠 PARZIALE**: orphan `MAG_SITO_COD` **100% → 69,8%**. I 5 siti del master agganciano; il residuo è
  spedizioni verso magazzini (`35,38,51,05,09`…) **assenti da `LU_SITO`** → **nodo di dominio** ([[OP-TRA-1]]):
  siti mancanti nel master (seed/dim) o magazzini/PDV esterni? **Serve decisione team** prima di chiudere il gate.
- **[[LL-025]]**: `get_sito_alias_map` fa `cast("int")` su `TGEN_CAMPO1_TAB="20.0"` → null → **mappa alias sempre
  vuota**. Bypassato nel notebook (cast double); **fix lib da fare sul wheel** (impatta `normalize_sito` con alias).
- Watermark spedizioni resettato/riaggiornato durante i test (gotcha noto): tornato a 2026-09-02.

## Doc aggiornati
- `acts/ACT_9025.md`, `lessons/LL-025.md` + INDEX, `05_open_points.md` (OP-TRA-1), `15_backlog_master.md` — nel **PR #6**.

## Stato dopo il push / prossimi passi
- **PR aperti**: #5 (ACT_CND-01 rimozione dead-code) e #6 (ACT_9025 fix sito) — a revisione team.
- **Per il team (decisioni)**: (a) confermare/chiudere il **residuo sito trasporti** (magazzini fuori dal master —
  OP-TRA-1); (b) **fix lib `get_sito_alias_map`** sul wheel (LL-025). Con (a) risolto, trasporti passa il gate.
- Giacenze pronto a gold. Carichi già verdi. Restano trasporti (dominio) e le altre wave.
