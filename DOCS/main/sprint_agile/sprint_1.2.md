# Sprint 1.2 — Dimensioni Articoli, Fornitori, Punti Vendita

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
| **Obiettivo** | DIM articolo/fornitore/PDV (bronze→silver→gold) |
| **Gg stimati / completati** | 7 / 6 |
| **% avanzamento** | ~86% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 27 lug → 31 lug 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** logica silver/gold completa; il residuo è il first-run bronze (1.2.1) che richiede la landing ADLS attiva.
**Blocco:** 1.2.1 dipende dalla landing zone attiva (FASE 0 / SFTP).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 1.2.1 | Bronze anagrafiche (ART_RADICI, FORNITORI, T_PDV) via landing | 1 | 🔵 PARZ. 20% | notebook scritto; first-run richiede ADLS |
| 1.2.2 | Silver DIM_ARTICOLO (dedup, SCD1) | 1 | ✅ | MERGE INTO silver.logistica |
| 1.2.3 | Silver DIM_FORNITORE | 1 | ✅ | |
| 1.2.4 | Silver DIM_PDV | 1 | ✅ | |
| 1.2.5 | Gold DIM_ARTICOLO (JOIN merceologica 5 livelli, SCD1) | 1 | ✅ | lookup Retail master opzionale (OP-02) |
| 1.2.6 | Gold DIM_FORNITORE, DIM_PDV | 1 | ✅ | |
| 1.2.7 | Test DQ anagrafiche | 1 | ✅ | 25 test |

**Punti aperti:** OP-02 (aggancio anagrafiche master Retail su Gold) — join master oggi opzionale/commentata; le `LU_*` stanno in `bronze_dev.condiviso` (D2).
