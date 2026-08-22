# Sprint 5.2 — Silver Trasporti

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
| **Obiettivo** | Silver trasporti (prep_trasporto/ordini, spedizioni clean, costo a fasce) |
| **Gg stimati / completati** | 8 / 8 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 30 nov → 4 dic 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** silver completo. Fix fill-down vettore con `first_value(ignore_nulls)` (no MAX arbitrario). Schema silver target = `logistica_curated`.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 5.2.1 | Analisi T_ORDINI, T_TRASP_* (join, misure) | 1 | ✅ | |
| 5.2.2 | `silver_prep_trasporto` (LEAD_TIME, fill-down vettore) | 2 | ✅ | first_value ignore_nulls |
| 5.2.3 | `silver_prep_ordini` (testate⋈righe, flag urgente) | 2 | ✅ | |
| 5.2.4 | `silver_spedizioni_clean` (dedup, normalize_sito) | 1 | ✅ | |
| 5.2.5 | Costo trasporto a fasce peso (+20% fallback) | 1 | ✅ | |
| 5.2.6 | DQ Silver Trasporti (LEAD_TIME ≥ 0) | 1 | ✅ | |
