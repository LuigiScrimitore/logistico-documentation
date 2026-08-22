# Sprint 7.3 — Validazione KPI End-to-End

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
| **Obiettivo** | Validazione KPI E2E con BA + sign-off + baseline performance |
| **Gg stimati / completati** | 5 / 2 |
| **% avanzamento** | ~40% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 8 feb → 12 feb 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** pipeline mapping SSOT completo; validazione e sign-off con BA ⏳ non avviabili offline.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 7.3.1 | Sessione validazione KPI con BA/Key User (3 mesi vs Oracle) | 2 | ⏳ PENDENTE | richiede PROD + BA |
| 7.3.2 | Approvazione KPI da business (sign-off) | 1 | ⏳ PENDENTE | dipende da 7.3.1 |
| 7.3.3 | Performance baseline (E2E vs finestra batch Oracle) | 1 | 🔵 PARZ. 20% | baseline locale ok; misura cloud pendente |
| 7.3.4 | Pipeline Mapping SSOT (`02_pipeline_mapping.md`) | 1 | ✅ | validato su run reale |
