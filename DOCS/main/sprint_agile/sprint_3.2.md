# Sprint 3.2 — Silver Giacenze

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_3.md`](../milestones/fase_3.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 3 — Wave B: Giacenze (Stock) |
| **Obiettivo** | Silver giacenze (catena unificata, struttura_mag clean, t_stock) |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 28 set → 2 ott 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** silver completo. Fix chiave: CATENA UNION per chiave logica (non su tupla intera). OP-29 (ordering fisiologico locale) OK su DAG Databricks.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 3.2.1 | Analisi SP_STOCK_* (normalizzazione UM, dedup) | 1 | ✅ | dedup per chiave logica con precedenza |
| 3.2.2 | `silver_catena_unificata` (CATENA+ESTERNI, dedup) | 2 | ✅ | pattern WL2_CATENA corretto |
| 3.2.3 | `silver_struttura_mag_clean` | 1 | ✅ | |
| 3.2.4 | `silver_t_stock` (join catena ↔ struttura_mag) | 2 | ✅ | OP-29 fisiologico |
| 3.2.5 | DQ Silver Giacenze (QTA ≥ 0, coerenza) | 1 | ✅ | |
