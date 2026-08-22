# ACT_7.2.5 · Prototipo dashboard Logistica (4 aree KPI)

**Status**: in-progress
**Type**: feature
**Origin**: sprint 7.2
**Sprint**: 7.2 — MicroStrategy & Ottimizzazione Query
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (richiede cloud)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_7.2.1 (connettore MicroStrategy), ACT_7.2.3 (viste KPI)   **Blocca**: —
**ADR collegate**: —   **Doc collegati**: `13_registro_rename_gold_microstrategy.md`   **OP collegati**: —

## Contesto e motivazione
Prototipo di dashboard Logistica su MicroStrategy che copra le 4 aree KPI (inbound, stock, outbound,
produttività), come vetrina del reporting sopra i DataMart (`A_*`) e le viste KPI (`kpi_*`). Serve il connettore
MicroStrategy (ACT_7.2.1) e il warehouse cloud attivi → bloccata offline.

## Obiettivo
Dashboard prototipo con le 4 aree KPI alimentata dalle viste KPI Gold (`gold_prod.logistica.kpi_*`).
Fatto = dashboard visualizza le 4 aree con dati reali dal SQL Warehouse.

## Analisi tecnica
Consumatore delle 10 viste KPI ([[ACT_7.2.3_kpi-views-chiavi-naturali]], file `sql/kpi/gold_kpi_*.sql`) via connettore
MicroStrategy ([[ACT_7.2.1_connettore-microstrategy-sql-warehouse]]). Richiede cloud. Mappatura suggerita
**4 aree → viste** (naming reale):

| Area dashboard | Viste KPI (`gold_prod.logistica.kpi_*`) | DataMart / fact sorgente |
|----------------|------------------------------------------|--------------------------|
| **Inbound** | `kpi_volumi_inbound_fornitore` (ex `kpi_lead_time_fornitore`), `kpi_qualita_ricevimento` | `A_INBOUND_MENSILE` (v4.0, ammanco in pezzi) |
| **Stock** | `kpi_saturazione_magazzino`, `kpi_aging_articoli` | `F_GIACENZE_DAILY`, `A_GIACENZE_MONTHLY`/`A_STOCK_MENSILE` |
| **Outbound** | `kpi_fill_rate`, `kpi_costo_trasporto`, `kpi_resa_corrieri`, `kpi_bolle_annullate` | `A_OUTBOUND_MENSILE`, `F_ORDINI`/`F_TRASPORTO` |
| **Produttività** | `kpi_produttivita_operatore`, `kpi_efficienza_sito_prep` | `A_PRODUTTIVITA_MENSILE`, `F_PREP_SPED` (cartoni/quintali, OP-27) |

Note reali sui dati esposti: la produttività è **cartoni/ora** (non colli/ora, non disponibili); alcuni KPI hanno
misure NULL/placeholder finché mancano dati sorgente (es. costo trasporto reale — listini corrieri, [[adr/0013_scope_trasporti_mtv]];
`A_OUTBOUND` misure costo/qtà NULL, cfr. `milestones/fase_7.md` §5). Attenzione ai rename 🔴 DA RECEPIRE nel modello MSTR
(`13_registro_rename_gold_microstrategy` §B/C) prima di cablare metriche/attributi sugli attributi/nomi vecchi.

## Sviluppo (diario)
- 2026-07-03 · avanzamento 20%: layout/aree definiti; realizzazione bloccata su cloud.

## Verifica
Dashboard renderizza le 4 aree KPI con valori coerenti con Gold/DataMart (spot-check di ogni area vs `SELECT` diretto
sulle viste sul warehouse).

## Esito
— (richiede cloud)

## Follow-up
Nessuna al momento.
