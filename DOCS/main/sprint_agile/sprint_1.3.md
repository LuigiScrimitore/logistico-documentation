# Sprint 1.3 — Dimensioni Logistiche (Siti, Operatori, Corrieri, Topografia)

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
| **Obiettivo** | DIM logistiche (sito, operatore, corriere, topografia) + workflow dim_refresh |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 17 ago → 21 ago 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** dimensioni complete; residui = first-run bronze (1.3.1) e deploy workflow (1.3.7), entrambi cloud-dependent. Risolto OP-28 (recovery dim_operatore da storico_liste).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 1.3.1 | Bronze siti (TABGEN nro_tab=7), operatori, corrieri via landing | 1 | 🔵 PARZ. 20% | first-run richiede ADLS |
| 1.3.2 | Silver DIM_SITO_LOGISTICO (normalize_sito + alias da TABGEN) | 1 | ✅ | utility `normalize_sito()` |
| 1.3.3 | Silver DIM_OPERATORE (recovery legacy 3A/4A da storico_liste) | 1 | ✅ | OP-28 risolto; membro ND |
| 1.3.4 | Silver DIM_CORRIERE | 1 | ✅ | |
| 1.3.5 | Silver DIM_TOPOGRAFIA_MAGAZZINO (4 livelli) | 1 | ✅ | |
| 1.3.6 | Gold DIM_SITO/OPERATORE/CORRIERE/TOPOGRAFIA | 1 | ✅ | surrogate_key_fallback null="ND" |
| 1.3.7 | Workflow `logistica_dim_refresh` (01:00) | 1 | 🔵 PARZ. 90% | YML scritto; deploy cloud pendente |
