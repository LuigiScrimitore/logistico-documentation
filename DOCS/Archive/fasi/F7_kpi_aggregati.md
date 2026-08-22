# FASE 7 — KPI Aggregati & Reporting

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** — | **Stato:** 🔵 aggregati A_* OK (26/26 run 2026-06-19); reporting su cloud

## 1. Obiettivo & scope
Costruire gli **aggregati mensili `A_*`** (DataMart) dai fact e le **view KPI** per il reporting
MicroStrategy. Ultimo layer della catena (legge i fact, precedenza finale).

## 2. Sorgenti (fact Gold)
`F_CARICO`, `F_ORDINI`, `F_TRASPORTO`, `F_TURNO_PREP_SITO`, `F_GIACENZE_DAILY`, `A_GIACENZE_MONTHLY`.

## 3. Gold DataMart (`gold_<env>.logistica_dm`)
| Notebook | Sorgente | Output | Note |
|---|---|---|---|
| `gold_dm_giacenze_monthly` | `F_GIACENZE_DAILY` | `A_GIACENZE_MONTHLY` | graceful NO_DATA se mese vuoto |
| `gold_a_stock_mensile` | `A_GIACENZE_MONTHLY` | `A_STOCK_MENSILE` | DM→DM passthrough |
| `gold_a_inbound_mensile` | `F_CARICO` | `A_INBOUND_MENSILE` | |
| `gold_a_outbound_mensile` | `F_ORDINI ⋈ F_TRASPORTO` | `A_OUTBOUND_MENSILE` | QTA/COSTO TOT NULL (F_TRASPORTO a grana bolla — vedi F5) |
| `gold_a_produttivita_mensile` | `F_TURNO_PREP_SITO` | `A_PRODUTTIVITA_MENSILE` | |
| `gold_dm_turno_prep_sito` | `F_TURNO_PREP_SITO` | `A_TURNO_PREP_SITO` | |

## 4. Reporting
View KPI in `sql/kpi/` (10 view, SparkSQL consentito — Gap #8b). Connettore MicroStrategy → Databricks
SQL Warehouse (M-01/M-03).

## 5. Data Quality
- Precedenza: aggregati **per ultimi** (leggono i fact). Phase ordering nel DAG.
- Sorgenti aggregati verificate/corrette in `../02_pipeline_mapping.md` (erano stale).

## 6. Open points di fase
- `A_OUTBOUND_MENSILE`: quantità/costo trasportato NULL finché non disponibili listini corrieri (vedi F5).
- V-07/V-08: validazione + sign-off KPI con BA/Key User (blocca approvazione finale, su cloud).
- M-01/M-02/M-03: connettore + tuning SQL Warehouse + dashboard (richiedono cloud).

## 7. Stato & dipendenze
6/6 notebook DM OK sul run 2026-06-19. Dipende da tutte le wave fact (2-6). Reporting dipende da FASE 0
(SQL Warehouse cloud).

## 8. Riferimenti
`../06_backlog.md` §5e (FASE 5 DM) e §5e MicroStrategy, `../04_piano_sviluppo.md` FASE 7, `sql/kpi/`.
