# Sprint 6.3 — Workflow Wave E & Validazione

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_6.md`](../milestones/fase_6.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti |
| **Obiettivo** | Workflow Wave E + validazione + doc |
| **Gg stimati / completati** | 5 / 3 |
| **% avanzamento** | ~60% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 18 gen → 22 gen 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** doc pronta; workflow da deployare e validazione compliance CE178 su dati reali ⏳.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 6.3.1 | Orchestrazione Wave E (CE178 in `logistica_carichi`, carrellisti in `logistica_prep_sped`) | 1 | 🔵 PARZ. 90% | deploy cloud pendente; placeholder `logistica_wave_e.yml` rimosso (ACT_9008) |
| 6.3.2 | Validazione funzionale CE178 e carrellisti | 2 | ⏳ PENDENTE | richiede PROD + compliance su dati reali |
| 6.3.3 | Documentazione Wave E | 2 | ✅ | `mapping_ce178.md`, `mapping_carrellisti.md` |
