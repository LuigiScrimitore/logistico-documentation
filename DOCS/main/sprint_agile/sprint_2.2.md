# Sprint 2.2 — Silver Carichi

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
| **Obiettivo** | Silver carichi (clean testate/dettagli, pesate, CE178) |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% (deploy workflow escluso) |
| **Stato** | ✅ COMPLETO (offline) |
| **Data inizio → fine** | 31 ago → 4 set 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** silver completo. Risolto OP-12 (art_radice/variante derivata in Silver per troncamento).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 2.2.1 | Analisi trasformazioni CDT_SA → Spark | 1 | ✅ | |
| 2.2.2 | `silver_carichi_testate` (julian_to_date, normalize_sito, MERGE) | 1 | ✅ | |
| 2.2.3 | `silver_carichi_dettagli` (dedup, art_radice/variante) | 1 | ✅ | OP-12 risolto |
| 2.2.4 | `silver_pesate` (DQ flag peso negativo) | 1 | ✅ | |
| 2.2.5 | `silver_traccia_ce178` (dedup, parsing lotto/scadenza) | 1 | ✅ | |
| 2.2.6 | Suite test DQ Silver Carichi | 1 | ✅ | 15 test |
| 2.2.7 | Aggiornamento workflow con task Silver | 1 | 🔵 PARZ. 90% | deploy cloud pendente |
