# Sprint 2.3 — Gold F_CARICO

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_2.md`](../milestones/fase_2.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 2 — Wave A: Carichi (Inbound) |
| **Obiettivo** | Gold F_CARICO (grain etichetta), LAD handler, quadratura |
| **Gg stimati / completati** | 7 / 5 |
| **% avanzamento** | ~71% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 7 set → 11 set 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** F_CARICO 0.0% orphan in locale. Residui: quadratura vs Oracle (2.3.4) e deploy workflow (2.3.5), cloud-dependent. Grain rivisto a **etichetta** (catena WL_CARICO); PES_CARICO da anagrafica articolo (non da pesata).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 2.3.1 | Analisi SP_LOAD_F_CARICO (grain, misure, join) | 1 | ✅ | |
| 2.3.2 | `gold_f_carico` (join silver, lookup dim, fallback) | 2 | ✅ | 0.0% orphan; CORRIERE_COD rimosso |
| 2.3.3 | Late-Arriving Dimensions handler | 1 | ✅ | `gold_late_arriving_handler` |
| 2.3.4 | Quadratura Gold vs Oracle (PESO_NETTO, QTA_RICEVUTA) | 2 | 🔵 PARZ. 20% | SQL scritto; richiede cloud+Oracle |
| 2.3.5 | Aggiornamento workflow Bronze→Silver→Gold→DQ | 1 | 🔵 PARZ. 90% | deploy cloud pendente |

**Punti aperti:** OP-CAR-3 (distribuzione QTA_ORD_FORN da WL4), OP-CAR-5 (design grain pesata INNER vs catena — sessione dedicata).
