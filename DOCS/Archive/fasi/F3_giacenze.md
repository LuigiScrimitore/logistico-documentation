# FASE 3 — Wave B: Giacenze (Stock)

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** B | **Stato:** 🔵 T_STOCK OK locale; backfill/quadratura pendenti

## 1. Obiettivo & scope
Fotografia giornaliera dello stock a magazzino: dalla catena di ubicazioni allo snapshot giacenze
(`F_GIACENZE_DAILY`), distinguendo picking vs scorte.

## 2. Sorgenti
Sistema **logistix**: `catena` (~158k/g), `catena_esterni` (~5.3k/g), `imbfmovim`. Sistema **cnd**:
`t_stock` (snapshot ~150k). Anagrafica: `struttura_mag`.

## 3. Bronze
`catena`/`catena_esterni` in **SNAPSHOT**; `imbfmovim` DELTA_MERGE; `t_stock` SNAPSHOT (CND) — filtrare
`_bronze_load_date = run_date`.

## 4. Silver
| Notebook | Target | Note |
|---|---|---|
| `silver_catena_clean` | `logistica.catena_clean` | sito canonico, date, ART_RADICE/VAR, SNAPSHOT append |
| `silver_catena_esterni_clean` | `logistica.catena_esterni_clean` | idem |
| `silver_catena_unificata` | `logistica.catena_unificata` | UNION + dedup ST15 (ambiguità), SNAPSHOT overwrite |
| `silver_t_stock` | `logistica.t_stock` | JOIN `struttura_mag`, aggregazione picking vs scorte (ST13/14) |
| `silver_prep_giacenze` | `logistica_curated.giacenze` | dedup, SNAPSHOT overwrite per DATA_FOTO |
| `silver_giacenze_aggregata` | `logistica.giacenza_aggregata` | GROUP BY MAG_COD + DATA_FOTO |

## 5. Gold
| Notebook | Target | Grain |
|---|---|---|
| `gold_f_giacenze_daily` | `logistica.F_GIACENZE_DAILY` | snapshot giornaliero per (sito, ubicazione/articolo), replaceWhere DATA_FOTO |

## 6. Dimensioni agganciate
`LU_SITO`, `LU_TOPOGRAFIA` (cella), articolo. Orphan gestito con sentinel/`ND`.

## 7. Data Quality & quadratura
Q-02 quadratura `F_GIACENZE` (QTA_DISPONIBILE per data_foto) vs Oracle — eseguibile su cloud.
Check R-05: 0 righe scritte per >2 gg consecutivi = indagare.

## 8. Open points di fase
- **OP-29** 🔵 ordering fisiologico locale: `silver_t_stock` legge la `catena_unificata` del giorno prima;
  in locale (ordine alfabetico) può dare 0 righe. Su Databricks il DAG garantisce l'ordine. Non è un bug.
- **OP-CAR-1 / ST-01/ST-02**: `VAL_STOCK_*` a 0 (sorgente stock valorizzato assente dall'as-is) — da
  identificare la sorgente reale.

## 9. Stato & dipendenze
T_STOCK OK in locale; quadratura e backfill richiedono cloud. Dipende da FASE 1 (dim_sito/topografia) e
dall'ordine `catena_unificata` → `t_stock`.

## 10. Riferimenti
`../02_pipeline_mapping.md` §7 "Giacenze", `../05_open_points.md` (OP-29), `../06_backlog.md` (ST-01/02).
