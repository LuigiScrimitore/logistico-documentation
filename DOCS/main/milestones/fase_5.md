# Milestone — FASE 5: Wave D — Trasporti (Outbound)

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F5_trasporti.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (5.1–5.4).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (23/28 gg) — F_TRASPORTO/F_ORDINI OK locale; quadratura/BA pendenti

## 1. Executive summary (funzionale)
Spedizione in uscita: dagli ordini e spedizioni al fact **F_TRASPORTO** (grana bolla) e **F_ORDINI**, con aggancio vettore/corriere e calcolo costo a fasce di peso.

## 2. Perimetro e sorgenti
Sistema **track**: `SPEDIZIONI`, `vettori`. Sistema **cdt_estr_raw**: `AUTOMEZZI`. Sistema **cnd**: `t_trasp_mtv`. Ordini pendenti da `sto_tes_carichi` (logistix).

## 3. Deliverable tecnici
**Silver:** `vettori_track_clean`, `automezzi_clean`, `spedizioni_clean`, `ordine` (filtro pendenti), `s_trasp_mtv`, `logistica_curated.trasporto` (JOIN + UNION CONS/TRANSITO), `logistica_curated.ordini`.
**Gold:** `F_TRASPORTO` (grana bolla, vettore/corriere agganciato), `F_ORDINI` (QTA_MANCANTE, FILL_RATE, flag_swapped).

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 5.1 | Bronze Trasporti | 🔵 PARZ. | [5.1](../sprint_agile/sprint_5.1.md) |
| 5.2 | Silver Trasporti | ✅ | [5.2](../sprint_agile/sprint_5.2.md) |
| 5.3 | Gold F_ORDINI & F_TRASPORTO | 🔵 PARZ. | [5.3](../sprint_agile/sprint_5.3.md) |
| 5.4 | KPI Trasporti & Workflow | 🔵 PARZ. | [5.4](../sprint_agile/sprint_5.4.md) |

## 5. Regole di business chiave
- **Costo trasporto a fasce peso** (+20% fallback).
- F_TRASPORTO a grana bolla → **non porta** quantità/costo aggregati (deliberato): `QTA_TRASPORTATA_TOT` e `COSTO_STIMATO_EUR_TOT` restano NULL in `A_OUTBOUND_MENSILE` finché mancano i listini corrieri.
- Fill-down vettore con `first_value(ignore_nulls)` (no MAX arbitrario).

## 6. Punti risolti
- **OP-26** — F_TRASPORTO da SPEDIZIONI@TRACK via landing (non JDBC).
- Rami secchi rimossi (RS-03/06/08).

## 7. Punti aperti
- **Listini corrieri assenti** → costi trasporto non valorizzati (dipendenza esterna).
- **OP-31** 🟠 — semi-join `ESTRAI_SPEDIZIONI` (CDC) vs finestra piena su `SP_DATABOLLA` (da validare su delta multipli).
- Quadratura e validazione BA — richiedono cloud/PROD.

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Valorizzazione economica del trasporto: **fuori scope** finché il cliente non fornisce i listini corrieri.

## 9. Sviluppi futuri
- Integrazione listini corrieri → valorizzazione costi e `A_OUTBOUND_MENSILE` completo.
- Validazione CDC `ESTRAI_SPEDIZIONI` su delta reali.

## 10. Riferimenti
`../02_pipeline_mapping.md` §7 "Trasporti", `../05_open_points.md` (OP-26/31), `../06_backlog.md` §5d, `../sprint_agile/` (5.1-5.4).
