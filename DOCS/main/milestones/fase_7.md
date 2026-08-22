# Milestone — FASE 7: KPI Aggregati & Reporting

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (7.1–7.3).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (12/19 gg) — DataMart + KPI views OK; MicroStrategy/tuning/validazione BA pendenti

## 1. Executive summary (funzionale)
Strato di **reporting**: aggregati mensili (DataMart `A_*`), viste KPI per il business e connettività MicroStrategy. È la fase che rende i dati logistici consumabili dagli utenti finali.

## 2. Perimetro
DataMart da tutte le wave (A–E). 10 SQL KPI views (chiavi naturali v2.0). Connettore MicroStrategy → Databricks SQL Warehouse.

## 3. Deliverable tecnici
**DataMart (`gold.logistica_dm`)** — 6/6 notebook OK sul run 2026-06-19:

| Notebook | Sorgente | Output |
|----------|----------|--------|
| `gold_dm_giacenze_monthly` | `F_GIACENZE_DAILY` | `A_GIACENZE_MONTHLY` (graceful NO_DATA se mese vuoto) |
| `gold_a_stock_mensile` | `A_GIACENZE_MONTHLY` | `A_STOCK_MENSILE` (DM→DM passthrough) |
| `gold_a_inbound_mensile` | `F_CARICO` | `A_INBOUND_MENSILE` |
| `gold_a_outbound_mensile` | `F_ORDINI ⋈ F_TRASPORTO` | `A_OUTBOUND_MENSILE` (QTA/COSTO TOT NULL — F_TRASPORTO a grana bolla, vedi Fase 5) |
| `gold_a_produttivita_mensile` | `F_TURNO_PREP_SITO` | `A_PRODUTTIVITA_MENSILE` |
| `gold_dm_turno_prep_sito` | `F_TURNO_PREP_SITO` | `A_TURNO_PREP_SITO` |

**KPI:** 10 viste SQL (`sql/kpi/kpi_*.sql`, SparkSQL consentito), ottimizzazione Gold (`OPTIMIZE + ZORDER + ANALYZE`).
**Reporting:** connettore MicroStrategy → Databricks SQL Warehouse (M-01/M-03), tuning warehouse, prototipo dashboard (4 aree KPI).
**Doc:** Pipeline Mapping SSOT (`02_pipeline_mapping.md`).
**Precedenza:** aggregati **per ultimi** (leggono i fact), phase ordering nel DAG.

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 7.1 | Aggregati Mensili DataMart | ✅ | [7.1](../sprint_agile/sprint_7.1.md) |
| 7.2 | MicroStrategy & Ottimizzazione Query | 🔵 PARZ. | [7.2](../sprint_agile/sprint_7.2.md) |
| 7.3 | Validazione KPI End-to-End | 🔵 PARZ. | [7.3](../sprint_agile/sprint_7.3.md) |

## 5. Regole & decisioni
- KPI views su **chiavi naturali** (v2.0, no surrogate ID).
- `A_OUTBOUND_MENSILE`: misure costo/quantità trasporto NULL finché mancano i listini corrieri (vedi Fase 5).

## 6. Punti risolti
- Pipeline Mapping SSOT creato e validato su run reale.
- Ottimizzazione tabelle Gold (OPTIMIZE/ZORDER/ANALYZE) pronta.
- **Consistenza aggregati vs fact (FASE 5/6, 2026-07-04):** verificati tutti i 6 aggregati A_*. `gold_a_inbound_mensile` era rotto (referenziava colonne del vecchio F_CARICO grain riga-dettaglio) → **riallineato a v4.0** (grain etichetta). La vista KPI `kpi_lead_time_fornitore` → riscritta come `kpi_volumi_inbound_fornitore` sulle nuove colonne. Gli altri 5 aggregati OK; quadratura F_CARICO OK; `run_all_gold.py` ordina correttamente (aggregati dopo i fact).

## 7. Punti aperti
- **`kpi_qualita_ricevimento` bloccata** — le misure di scarto non esistono più post grain-etichetta; CREATE commentato, dipende da **OP-CAR-3** (quantità ordinata).
- Connessione MicroStrategy, tuning SQL Warehouse, dashboard — richiedono **SQL Warehouse cloud attivo**.
- **V-07/V-08** — validazione KPI E2E con BA + sign-off business (richiede PROD/BA).
- Performance baseline su cloud PROD.

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Misure economiche outbound: escluse finché non arrivano i listini corrieri.
- Surrogate key nelle viste KPI: rimandate (chiavi naturali per ora).

## 9. Sviluppi futuri
- Completamento dashboard MicroStrategy e tuning warehouse in PROD.
- Sign-off KPI formale con il business.

## 10. Riferimenti
`../02_pipeline_mapping.md`, `../06_backlog.md` (V-07/08, D-04), `../sprint_agile/` (7.1-7.3).
