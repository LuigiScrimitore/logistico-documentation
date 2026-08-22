# Sprint 1.1 — Dimensione Calendario & Strutture Merceologiche

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_1.md`](../milestones/fase_1.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 1 — Master Data & Dimensioni |
| **Obiettivo** | DIM calendario (2018–2030) e struttura merceologica |
| **Gg stimati / completati** | 5 / 5 |
| **% avanzamento** | ~95% (1.1.3 first-run cloud pendente) |
| **Stato** | ✅ COMPLETO (offline) |
| **Data inizio → fine** | 20 lug → 24 lug 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** dimensioni pronte e testate offline; unico residuo il first-run cloud di 1.1.3 (dipende da FASE 0).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 1.1.1 | DIM_CALENDARIO (PySpark, Gauss Pasqua, 2018–2030) | 2 | ✅ | 15 test; ISO week, trimestre, festività IT |
| 1.1.2 | DIM_MESE/TRIMESTRE/ANNO (attributi calendario) | 1 | ✅ | inclusi in dim_calendario |
| 1.1.3 | DIM_STRUTTURA_MERCEOLOGICA (5 livelli da CDT_DW) | 1 | 🔵 PARZ. 90% | notebook pronto; first-run cloud pendente |
| 1.1.4 | Test DQ Calendario | 1 | ✅ | 15 test pytest verdi |
