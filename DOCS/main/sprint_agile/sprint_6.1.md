# Sprint 6.1 — CE178 Silver & Gold

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
| **Obiettivo** | Tracciabilità lotti CE178 (silver + gold + conformità) |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 21 dic → 25 dic 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** Wave E CE178 completa; Bronze riusato da Sprint 2.1.5.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 6.1.1 | Analisi flusso CE178 (ciclo vita lotto) | 1 | ✅ | |
| 6.1.2 | Bronze `bronze_traccia_ce178` | — | ✅ | riuso da Sprint 2.1.5 |
| 6.1.3 | Silver `silver_tracciabilita_lotto` (flag_scaduto, gg a scadenza) | 2 | ✅ | |
| 6.1.4 | Gold `gold_f_tracciabilita_lotti` (QTA_RESIDUA, MERGE) | 2 | ✅ | |
| 6.1.5 | Vista conformità CE178 (lotti scaduti con residuo) | 2 | ✅ | |
