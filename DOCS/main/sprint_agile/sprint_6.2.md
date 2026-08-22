# Sprint 6.2 — Carrellisti Bronze-Silver-Gold

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
| **Obiettivo** | Missioni/sessioni carrellisti → F_TURNO |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 11 gen → 15 gen 2027 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** completo. Risolti OP-14 (DETTAGLIO_CARR e IMBFMOVIM distinti) e OP-15 (unione in dim_operatore).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 6.2.1 | Analisi sorgenti (DETTAGLIO_CARR, CARTELLINO, IMBFMOVIM) | 1 | ✅ | OP-14 risolto |
| 6.2.2 | Bronze `bronze_dettaglio_carr` + `bronze_imbfmovim` | 1 | ✅ | OP-15 risolto |
| 6.2.3 | Silver `silver_missione_carrellista` (durata, tipo) | 1 | ✅ | |
| 6.2.4 | Silver `silver_sessione_carrellista` (ORE_PRODUTTIVE) | 2 | ✅ | MAX(SUM(dur)-30,0)/60 |
| 6.2.5 | Gold `gold_f_movimentazione_carrellisti` (grana giornaliera, replaceWhere) | 1 | ✅ | |
| 6.2.6 | Vista KPI carrellisti (missioni/ora, % produttivo) | 1 | ✅ | |
