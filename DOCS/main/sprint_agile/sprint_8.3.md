# Sprint 8.3 — Preparazione Cut-Over

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_8.md`](../milestones/fase_8.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 8 — Shadow Mode, Validazione & Cut-Over |
| **Obiettivo** | Rollback plan, cut-over plan, comunicazione utenti, permessi PROD |
| **Gg stimati / completati** | 5 / 2 |
| **% avanzamento** | ~40% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 1 mar → 5 mar 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** bozze piani pronte (`piani/cutover_plan.md`, `piani/rollback_plan.md`); finalizzazione e approvazione dipendono dall'esito shadow mode.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 8.3.1 | Rollback Plan approvato | 1 | 🔵 PARZ. 50% | bozza `piani/rollback_plan.md` |
| 8.3.2 | Cut-Over Plan dettagliato (sequenza, timing) | 2 | 🔵 PARZ. 50% | bozza `piani/cutover_plan.md` |
| 8.3.3 | Comunicazione utenti finali (finestra < 2h) | 1 | 🔵 PARZ. 50% | template pronto |
| 8.3.4 | Verifica permessi PROD (MicroStrategy su gold_prod) | 1 | ⏳ | |
