# Sprint 3.3 — Gold F_GIACENZE

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_3.md`](../milestones/fase_3.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 3 — Wave B: Giacenze (Stock) |
| **Obiettivo** | Gold F_GIACENZE_DAILY + datamart mensile + KPI |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 5 ott → 9 ott 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** F_GIACENZE_DAILY popolato (55k righe nel big re-run). Residuo: quadratura (3.3.6), cloud-dependent.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 3.3.1 | Analisi SP_LOAD_F_GIACENZE (grain, misure) | 1 | ✅ | |
| 3.3.2 | `gold_f_giacenze_daily` (replaceWhere per data_foto) | 2 | ✅ | |
| 3.3.3 | `gold_dm_giacenze_monthly` | 1 | ✅ | gold.logistica_dm |
| 3.3.4 | Vista `kpi_saturazione_magazzino` | 1 | ✅ | |
| 3.3.5 | Vista `kpi_aging_articoli` (30/60/90/180+) | 1 | ✅ | |
| 3.3.6 | Quadratura vs Oracle (QTA_DISPONIBILE) | 1 | 🔵 PARZ. 20% | richiede cloud+Oracle |
