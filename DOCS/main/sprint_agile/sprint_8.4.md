# Sprint 8.4 — Cut-Over & Stabilizzazione Post-Live

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
| **Obiettivo** | Esecuzione cut-over, presidio post-live, spegnimento ODI, retrospettiva |
| **Gg stimati / completati** | 7 / 0 |
| **% avanzamento** | 0% |
| **Stato** | ⏳ PENDENTE |
| **Data inizio → fine** | 8 mar → 12 mar 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** attività finali di go-live, tutte dipendenti dal completamento e approvazione dello shadow mode.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 8.4.1 | Esecuzione Cut-Over (step by step, timestamp/responsabile) | 1 | ⏳ | |
| 8.4.2 | Verifica post-cut-over D+0, D+1 (monitoring 4h) | 2 | ⏳ | |
| 8.4.3 | Supporto utenti D+1→D+5 (presidio, bug fixing) | 2 | ⏳ | |
| 8.4.4 | Spegnimento flusso Oracle ODI (disabilita, non elimina) | 1 | ⏳ | |
| 8.4.5 | Retrospettiva + documentazione finale | 1 | 🔵 PARZ. 30% | bozza in `docs/Archive/` |
