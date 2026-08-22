# Sprint 4.5 — Edge Cases Prep Spedizioni

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
| **Obiettivo** | Edge case picking + stress test idempotenza |
| **Gg stimati / completati** | 5 / 3 |
| **% avanzamento** | ~60% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 16 nov → 20 nov 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** edge case gestiti in codice; lo stress test idempotenza (4.5.4) richiede PROD con storico su ADLS.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 4.5.1 | Operatori non in DIM_OPERATORE (sentinel ND/−1) | 1 | ✅ | surrogate_key_fallback |
| 4.5.2 | Bolle annullate (escluse da fact, in KPI) | 1 | ✅ | `kpi_bolle_annullate` |
| 4.5.3 | Turni a cavallo di mezzanotte (per data_riepilogo) | 1 | ✅ | regola documentata |
| 4.5.4 | Stress test idempotenza (30 gg backfill + re-run) | 2 | ⏳ PENDENTE | richiede PROD + storico ADLS |
