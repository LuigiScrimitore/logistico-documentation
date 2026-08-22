# Sprint 5.1 — Bronze Trasporti

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
| **Obiettivo** | Bronze trasporti (spedizioni@TRACK, MTV, PDV, vettori, automezzi) |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 23 nov → 27 nov 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** Bronze completi. Risolto OP-26 (F_TRASPORTO da SPEDIZIONI@TRACK via landing, non JDBC). Residuo: backfill + deploy (5.1.7).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 5.1.1 | Analisi sorgenti (SPEDIZIONI@TRACK, T_TRASP_MTV, T_PDV, T_VETTORI) | 1 | ✅ | OP-26 risolto |
| 5.1.2 | `bronze_spedizioni` (via landing, DELTA_MERGE) | 1 | ✅ | |
| 5.1.3 | `bronze_t_trasp_mtv` (CND/STAT) | 1 | ✅ | |
| 5.1.4 | `bronze_t_pdv` (full anagrafica) | 1 | ✅ | |
| 5.1.5 | `bronze_t_vettori` (full anagrafica) | 1 | ✅ | |
| 5.1.6 | `bronze_automezzi` | 1 | ✅ | |
| 5.1.7 | Backfill + Workflow Bronze Trasporti (05:00) | 1 | 🔵 PARZ. 20% | script+YML pronti; richiede cloud |
