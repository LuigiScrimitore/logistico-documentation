# Sprint 3.1 — Bronze Giacenze

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
| **Obiettivo** | Bronze giacenze (catena, catena_esterni, t_stock, struttura_mag) |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 21 set → 25 set 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** Bronze completi (snapshot dynamic partition overwrite). Residui: backfill (3.1.5) e deploy workflow (3.1.6), cloud-dependent.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 3.1.1 | Analisi snapshot giacenze (CATENA/ESTERNI, T_STOCK, STRUTTURA_MAG) | 1 | ✅ | WL2_CATENA = CATENA UNION ESTERNI |
| 3.1.2 | `bronze_catena` + `bronze_catena_esterni` (SNAPSHOT) | 1 | ✅ | dynamic partition overwrite/giorno |
| 3.1.3 | `bronze_t_stock` (CND/STAT, MERGE) | 1 | ✅ | |
| 3.1.4 | `bronze_struttura_mag` (FULL) | 1 | ✅ | |
| 3.1.5 | Backfill storico giacenze | 1 | 🔵 PARZ. 20% | richiede cloud+ADLS |
| 3.1.6 | Workflow Bronze Giacenze (03:00) | 2 | 🔵 PARZ. 90% | deploy cloud pendente |
