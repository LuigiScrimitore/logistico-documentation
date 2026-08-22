# Sprint 8.1 — Shadow Mode Setup

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
| **Obiettivo** | Provisioning PROD, deploy, attivazione workflow, quadratura automatica |
| **Gg stimati / completati** | 5 / 1 |
| **% avanzamento** | ~20% |
| **Stato** | 🔵 PARZIALE (bloccato da infra PROD) |
| **Data inizio → fine** | 15 feb → 19 feb 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** logica quadratura e runbook abbozzati offline. Tutto il resto **bloccato dal provisioning PROD** (prerequisito assoluto).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 8.1.1 | Provisioning Databricks Workspace PROD + ADLS | 1 | ⏳ | prerequisito bloccante |
| 8.1.2 | Deploy PROD (`terraform apply`, DAB `--target prod`) | 1 | ⏳ | |
| 8.1.3 | Attivazione workflow PROD + backfill storico | 1 | ⏳ | |
| 8.1.4 | Quadratura automatica giornaliera Oracle vs Databricks | 1 | 🔵 PARZ. 50% | logica scritta; richiede shadow mode |
| 8.1.5 | Runbook operativo PROD | 1 | 🔵 PARZ. 50% | bozza `DOCS/runbook.md` |
