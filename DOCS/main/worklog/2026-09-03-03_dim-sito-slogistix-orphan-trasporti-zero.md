---
data: 2026-09-03
titolo: "dim_sito da S_LOGISTIX+WL1: orphan sito trasporti = 0 (ACT_9026) + fix wheel LL-025/LL-026"
autore: Francesco Foconi
push_monorepo: "8377bfb (PR #7)"
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9026]
adr: []
lesson: [LL-025, LL-026]
op: [OP-TRA-1]
---

## Cosa e' stato fatto
- **[[ACT_9026]]**: risolto in via **definitiva** l'orphan sito dei trasporti (era 100%→69,8% dopo [[ACT_9025]]).
  Root cause: `dim_sito`/`LU_SITO` era costruita da `struttura_mag` (**5 siti**, `SITO_DESC` null), mentre le
  transazionali referenziano ~18 siti. I "fuori-master" erano **siti reali**, non errori.
- Anagrafica autoritativa = **S_LOGISTIX** (22 siti attivi + descrizione); codice numerico per ogni sito via
  **WL1_MAG_SITO_STORICO** (`MAG_SITO_COD_ORIG`, filtro correnti+attivi `DATFIN_VALID=99999999 AND ATTIVO=1`,
  mapping univoco verificato: 0 ambiguità, copertura spedizioni 18/18).

## Novita'
- **Trasporti ✅ RISOLTO** (validato DEV, run_date 2026-09-02): cross-check `ordine`/`spedizioni_clean` vs `dim_sito`
  → **orphan sito = 0** (ordine 5/5 ok, spedizioni 18/18 ok). Prima restavano 5 codici alfabetici orphan per lato.
- Nuove sorgenti in landing/bronze: `s_logistix` (22) + `wl1_mag_sito_storico` (60) — config `cdt_estr_raw`,
  2 bronze notebook, 2 task in `logistica_landing_ingestion`.
- `silver_dim_sito` v4.0.0: build da `S_LOGISTIX ⋈ WL1` → `SITO_COD` numerico + `SITO_DESC` reale (+ `SITO_COD_ALFA`
  LGAX e `SITO_COD_MAG` 0020A come riferimento). `gold_dim_sito` porta la `SITO_DESC` reale.
- **[[LL-025]]** (fix lib sul **wheel**): `get_sito_alias_map` ora costruisce la mappa **completa** da S_LOGISTIX+WL1
  (+ fallback TABGEN) e casta **double** (non int) → risolve gli alias alfabetici (`LGAX/LONX/LCAX/LSLX/LGCX`).
  Wheel ribuildato e caricato sul Volume `_wheels`.
- **[[LL-026]]** (nuova): `full_refresh` deve fare **OVERWRITE**, non merge. Il remap di `SITO_COD` (in chiave)
  lasciava righe stale duplicate (alfa+num, stessi conteggi). Fix su `silver_ordini`, `silver_trasporti`
  (aggiunto widget full_refresh), `silver_spedizioni_clean`.
- `spedizioni_clean` **non** modificato nella logica sito: già numerico via `normalize_sito`; bastava la alias-map.

## Doc aggiornati
- `acts/ACT_9026.md` (done), `lessons/LL-025.md` + `LL-026.md` + INDEX rigenerato, `05_open_points.md`
  (OP-TRA-1 ✅ chiuso). Tutto nel **PR feat/act-9026-dim-sito-slogistix**.

## Stato dopo il push / prossimi passi — INDICAZIONI TEAM
- **⚠️ Conflitto con PR #6 ([[ACT_9025]], aperto)**: PR #6 risolveva i trasporti col canonico **alfabetico**
  (mappa num→alfa in `spedizioni_clean`, solo 5 siti TABGEN → parziale) e con un **workaround in-notebook** del bug
  lib. ACT_9026 **supera la parte trasporti di PR #6** (canonico **numerico**, 22 siti, orphan 0, coerente con
  `ordine`/`trasporti` che già usano `normalize_sito`) e **corregge il bug lib alla radice** (wheel, LL-025).
  → Raccomandazione: **ridurre PR #6 alla sola parte giacenze** (`silver_t_stock` upper, indipendente e valida);
  scartare la modifica trasporti a `spedizioni_clean` (entrambi i PR toccano quel file: tenere la mia versione
  numerica + overwrite). La giacenze resta canonico **alfabetico** (F_CARICO), i trasporti **numerico**: due fact,
  due canonici, stessa anagrafica autoritativa S_LOGISTIX.
- **Follow-up**: `dim_sito` ora espone anche `SITO_COD_ALFA`/`SITO_COD_MAG` → se giacenze necessita di una
  `LU_SITO` alfabetica, si può estendere `gold_dim_sito` senza nuove sorgenti (punto di riconciliazione).
- **Non-regressione giacenze**: `dim_sito` era già numerico (ora solo più completo); giacenze aggancia via ramo
  alfabetico (catena↔struttura_mag), non via `LU_SITO` numerico → non impattato. Da confermare al prossimo run.
- `trasporto`/mtv/gold non materializzati in DEV a questo run_date: al prossimo run useranno wheel+overwrite.
