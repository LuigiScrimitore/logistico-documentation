# Milestone — FASE 3: Wave B — Giacenze (Stock)

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F3_giacenze.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (3.1–3.4).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (22/26 gg) — T_STOCK OK locale; backfill/quadratura/BA pendenti

## 1. Executive summary (funzionale)
Fotografia giornaliera dello stock a magazzino: dalla catena di ubicazioni allo snapshot giacenze **F_GIACENZE_DAILY**, distinguendo picking vs scorte. Nel big re-run F_GIACENZE è passato da 0 a 55.231 righe.

## 2. Perimetro e sorgenti
Sistema **logistix**: `catena` (~158k/g), `catena_esterni` (~5.3k/g), `imbfmovim`. Sistema **cnd**: `t_stock` (snapshot ~150k). Anagrafica: `struttura_mag`.

## 3. Deliverable tecnici
**Bronze:** catena/catena_esterni SNAPSHOT, t_stock SNAPSHOT (CND), imbfmovim DELTA.
**Silver:** `catena_clean`, `catena_esterni_clean`, `catena_unificata` (UNION + dedup per chiave logica), `t_stock` (JOIN struttura_mag, picking vs scorte ST13/14), `logistica_curated.giacenze` (snapshot per DATA_FOTO), `giacenza_aggregata`.
**Gold:** `F_GIACENZE_DAILY` (snapshot per sito/ubicazione/articolo, replaceWhere DATA_FOTO), `gold_dm_giacenze_monthly`.
**Dimensioni:** LU_SITO, LU_TOPOGRAFIA, articolo.

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 3.1 | Bronze Giacenze | 🔵 PARZ. | [3.1](../sprint_agile/sprint_3.1.md) |
| 3.2 | Silver Giacenze | ✅ | [3.2](../sprint_agile/sprint_3.2.md) |
| 3.3 | Gold F_GIACENZE | 🔵 PARZ. | [3.3](../sprint_agile/sprint_3.3.md) |
| 3.4 | Workflow & Validazione Giacenze | 🔵 PARZ. | [3.4](../sprint_agile/sprint_3.4.md) |

## 5. Data Quality & quadratura
Q-02 quadratura F_GIACENZE (QTA_DISPONIBILE per data_foto) vs Oracle — su cloud. Check R-05: 0 righe per >2 gg consecutivi = indagare.

## 6. Punti risolti
- Fix CATENA: UNION per chiave logica, non su tupla intera.
- **OP-29** — ordering fisiologico: chiuso come comportamento locale atteso (su Databricks il DAG garantisce l'ordine catena_unificata → t_stock).

## 7. Punti aperti
- **ST-01/ST-02** — `VAL_STOCK_*` a 0 (sorgente stock valorizzato assente dall'as-is): da identificare la sorgente reale.
- Quadratura e backfill — richiedono cloud.

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Valorizzazione economica dello stock: fuori scope finché non si identifica la sorgente valorizzata.

## 9. Sviluppi futuri
- Identificazione sorgente `VAL_STOCK` per la valorizzazione.
- Quadratura automatica su Databricks.

## 10. Riferimenti
`../02_pipeline_mapping.md` §7 "Giacenze", `../05_open_points.md` (OP-29), `../06_backlog.md` (ST-01/02), `../sprint_agile/` (3.1-3.4).
