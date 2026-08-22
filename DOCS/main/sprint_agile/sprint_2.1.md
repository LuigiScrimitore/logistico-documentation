# Sprint 2.1 — Bronze Carichi

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_2.md`](../milestones/fase_2.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 2 — Wave A: Carichi (Inbound) |
| **Obiettivo** | Bronze carichi (testate, righe, pesate, CE178) 22 siti |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 24 ago → 28 ago 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** notebook Bronze completi e testati in locale; residui = backfill storico (2.1.6) e deploy workflow (2.1.7), cloud-dependent.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 2.1.1 | Analisi sorgenti (STO_TES/RIGHE_CARICO, PESATE, TRACCIACE178) | 1 | ✅ | `DOCS/Archive/mapping_carichi.md` |
| 2.1.2 | `bronze_sto_tes_carichi` (22 siti, DELTA_MERGE + row_hash) | 1 | ✅ | chiave null-safe `<=>` |
| 2.1.3 | `bronze_sto_righe_carico` | 1 | ✅ | |
| 2.1.4 | `bronze_pesate` | 1 | ✅ | |
| 2.1.5 | `bronze_traccia_ce178` | 1 | ✅ | riusato in Wave E |
| 2.1.6 | Backfill storico (22 db-link LOGISTIX) | 1 | 🔵 PARZ. 20% | script pronto; richiede cloud+ADLS |
| 2.1.7 | Workflow `logistica_carichi` (task chain + retry) | 1 | 🔵 PARZ. 90% | YML scritto; deploy cloud pendente |
