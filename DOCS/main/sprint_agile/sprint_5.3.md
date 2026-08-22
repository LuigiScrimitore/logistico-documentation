# Sprint 5.3 — Gold F_ORDINI & F_TRASPORTO

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
| **Obiettivo** | Gold F_ORDINI, F_TRASPORTO, gestione swap, quadratura |
| **Gg stimati / completati** | 8 / 6 |
| **% avanzamento** | ~75% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 7 dic → 11 dic 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** fact completi (F_TRASPORTO 23k nel big re-run). Residuo: quadratura (5.3.4).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 5.3.1 | `gold_f_ordini` (QTA_MANCANTE, FILL_RATE, flag_swapped) | 2 | ✅ | |
| 5.3.2 | `gold_f_trasporto` (lookup DIM_CORRIERE, costo/lead_time) | 2 | ✅ | |
| 5.3.3 | Gestione Swap (FLAG_SWAPPED, link ordine sostituto) | 2 | ✅ | |
| 5.3.4 | Quadratura vs Oracle (QTA_CONSEGNATA, COSTO_EUR) | 2 | 🔵 PARZ. 20% | richiede cloud+Oracle |
