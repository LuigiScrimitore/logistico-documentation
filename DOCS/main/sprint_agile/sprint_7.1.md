# Sprint 7.1 — Aggregati Mensili DataMart

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
| **Obiettivo** | DataMart mensili (inbound, stock, outbound, produttività) |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% (deploy workflow escluso) |
| **Stato** | ✅ COMPLETO (offline) |
| **Data inizio → fine** | 25 gen → 29 gen 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** datamart completi in `gold.logistica_dm`. Residuo: deploy workflow datamart (7.1.6).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 7.1.1 | Analisi aggregati Oracle CDT_DW (A_*) | 1 | ✅ | |
| 7.1.2 | `gold_dm_inbound_mensile` (peso/QTA, P90 lead_time) | 1 | ✅ | |
| 7.1.3 | `gold_dm_stock_mensile` | 1 | ✅ | |
| 7.1.4 | `gold_dm_outbound_mensile` (trasporti+spedizioni) | 1 | ✅ | |
| 7.1.5 | `gold_dm_produttivita_mensile` (operatore/sito) | 1 | ✅ | |
| 7.1.6 | Workflow `logistica_datamart` (fan-out, 06:00) | 2 | 🔵 PARZ. 90% | deploy cloud pendente |
