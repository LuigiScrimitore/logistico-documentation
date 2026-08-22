# Sprint 8.2 — Shadow Mode Run 10+ gg

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
| **Obiettivo** | Run shadow mode ≥ 10 gg, monitoraggio quadrature, report sign-off |
| **Gg stimati / completati** | 10 / 1 |
| **% avanzamento** | ~10% |
| **Stato** | 🔵 PARZIALE (bloccato da 8.1) |
| **Data inizio → fine** | 22 feb → 26 feb 2027 (+ run esteso) |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** template report pronto; esecuzione dipende da shadow mode attivo (8.1). Target: delta ≤ 0.1% su ≥ 95% giorni.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 8.2.1 | Monitoraggio giornaliero quadrature (log anomalie) | 4 | ⏳ | target ≥ 95% gg delta ≤ 0.1% |
| 8.2.2 | Risoluzione anomalie (fix + redeploy CI/CD) | 4 | ⏳ | |
| 8.2.3 | Stress test finestra batch (ritardo sorgente) | 1 | ⏳ | |
| 8.2.4 | Report finale Shadow Mode (sign-off) | 1 | 🔵 PARZ. 50% | template pronto |
