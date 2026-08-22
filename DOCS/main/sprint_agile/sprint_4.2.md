# Sprint 4.2 — Silver Prep Spedizioni: Normalizzazione

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
| **Obiettivo** | Silver prep sped (clean + uniche pattern #2 + watermark pilota) |
| **Gg stimati / completati** | 8 / 8 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 26 ott → 30 ott 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** OP-30 validato (clean incrementale + pattern #2 chiavi-impattate). Watermark OP-35 pilota ALL_OK.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 4.2.1 | Analisi SP_AGG_ANAG_PREP_SPED 3A/4A | 1 | ✅ | |
| 4.2.2 | `silver_storico_liste_clean` (MERGE incrementale) | 1 | ✅ | OP-30 clean incrementale |
| 4.2.3 | `silver_storico_bolle_clean` | 1 | ✅ | BOL_NRO_RIGA esclusa da not_null |
| 4.2.4 | `silver_storico_liste_uniche` (GROUP BY 8 chiavi) | 1 | ✅ | OP-30 pattern #2 |
| 4.2.5 | `silver_storico_bolle_uniche` (GROUP BY) | 1 | ✅ | DQ S7 fisiologico |
| 4.2.6 | `silver_catena_unificata` (dedup per chiave) | 1 | ✅ | |
| 4.2.7 | DQ Silver Prep Spedizioni | 1 | ✅ | |
| 4.2.8 | Watermark OP-35 pilota su liste_clean | 1 | ✅ | ALL_OK (2026-06-14) |
