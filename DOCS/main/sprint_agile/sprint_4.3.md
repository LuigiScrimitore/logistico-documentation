# Sprint 4.3 — Gold F_PREP_SPED

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_4.md`](../milestones/fase_4.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 4 — Wave C: Preparazione Spedizioni (Picking) |
| **Obiettivo** | Gold F_PREP_SPED (regola 30 min), datamart turno/sito, quadratura |
| **Gg stimati / completati** | 8 / 7 |
| **% avanzamento** | ~88% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 2 nov → 6 nov 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** F_PREP_SPED 0.0% orphan, regola 30 min implementata (9 test). Residuo: quadratura (4.3.6). Schema silver target rinominato in `logistica_curated`.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 4.3.1 | Analisi SP_LOAD_F_PREP_PROD_OPER (grain, regola 30min) | 1 | ✅ | |
| 4.3.2 | Regola 30 min attrezzaggio (Window, rank=1) | 1 | ✅ | 9 test verdi |
| 4.3.3 | `silver_prep_prep_sped` (join uniche⋈catena, dedup) | 2 | ✅ | tiebreaker SEQ_PREL_PREP (OP-33 da chiarire BA) |
| 4.3.4 | `gold_f_prep_sped` (lookup dim, 0.0% orphan) | 2 | ✅ | null_val="ND" |
| 4.3.5 | `gold_dm_turno_prep_sito` | 1 | ✅ | |
| 4.3.6 | Quadratura vs Oracle (COLLI_PREPARATI, ORE_PRODUTTIVE) | 1 | 🔵 PARZ. 20% | richiede cloud+Oracle |

**Punti aperti:** OP-33 (tiebreaker dedup da validare con BA).
