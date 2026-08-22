# Sprint 5.4 — KPI Trasporti & Workflow

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_5.md`](../milestones/fase_5.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 5 — Wave D: Trasporti (Outbound) |
| **Obiettivo** | KPI trasporti + workflow + validazione BA |
| **Gg stimati / completati** | 5 / 3 |
| **% avanzamento** | ~60% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 14 dic → 18 dic 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** viste KPI pronte; residui deploy workflow e validazione BA (⏳).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 5.4.1 | Vista `kpi_fill_rate` | 1 | ✅ | |
| 5.4.2 | Vista `kpi_costo_trasporto` (costo/KG, /M3, /ordine) | 1 | ✅ | |
| 5.4.3 | Vista `kpi_resa_corrieri` | 1 | ✅ | |
| 5.4.4 | Workflow `logistica_trasporti` (05:00) | 1 | 🔵 PARZ. 90% | deploy cloud pendente |
| 5.4.5 | Validazione funzionale trasporti con BA | 1 | ⏳ PENDENTE | richiede PROD + BA |
