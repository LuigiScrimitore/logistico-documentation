# Sprint 7.2 — MicroStrategy & Ottimizzazione Query

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_7.md`](../milestones/fase_7.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 7 — KPI Aggregati & Reporting |
| **Obiettivo** | Connettore MicroStrategy, ottimizzazione Gold, 10 KPI views |
| **Gg stimati / completati** | 7 / 3 |
| **% avanzamento** | ~43% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 1 feb → 5 feb 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** viste KPI e script OPTIMIZE pronti; tutto ciò che tocca MicroStrategy/SQL Warehouse (7.2.1/7.2.4/7.2.5) richiede il cloud attivo.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 7.2.1 | Connettore MicroStrategy → Databricks SQL Warehouse | 2 | 🔵 PARZ. 20% | richiede SQL Warehouse cloud |
| 7.2.2 | Ottimizzazione Gold (OPTIMIZE + ZORDER + ANALYZE) | 1 | ✅ | `sql/optimize/gold_optimize_tables.sql` |
| 7.2.3 | 10 SQL KPI views (chiavi naturali v2.0) | 2 | ✅ | `sql/kpi/kpi_*.sql` |
| 7.2.4 | Tuning SQL Warehouse (size, auto-suspend) | 1 | 🔵 PARZ. 20% | richiede cloud |
| 7.2.5 | Prototipo dashboard Logistica (4 aree KPI) | 1 | 🔵 PARZ. 20% | richiede cloud |
