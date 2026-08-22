# Sprint 4.1 — Bronze Prep Spedizioni

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
| **Obiettivo** | Bronze prep sped (liste, bolle, riepiloghi, cartellino) |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 19 ott → 23 ott 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** Bronze completi; fix chiave lettura CSV per header (OP-30) e MERGE null-safe su BOL_NRO_RIGA. Residuo: backfill cartellino (4.1.6).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 4.1.1 | Analisi sorgenti (STORICO_LISTE/BOLLE, RIEPILOGHI, CARTELLINO) | 1 | ✅ | `mapping_prep_spedizioni.md` |
| 4.1.2 | `bronze_storico_liste` (DELTA_MERGE + row_hash) | 1 | ✅ | lettura per header (OP-30) |
| 4.1.3 | `bronze_storico_bolle_testate` | 1 | ✅ | |
| 4.1.4 | `bronze_storico_bolle_righe` | 1 | ✅ | MERGE null-safe `<=>` |
| 4.1.5 | `bronze_storico_riepiloghi` | 1 | ✅ | |
| 4.1.6 | `bronze_cartellino` + backfill | 1 | 🔵 PARZ. 20% | backfill richiede ADLS |
| 4.1.7 | Workflow Bronze Prep Sped | 1 | ✅ | |
