# Sprint 0.3 — Connettività Sorgenti & Template Notebook

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_0.md`](../milestones/fase_0.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 0 — Fondamenta Infrastrutturali |
| **Obiettivo** | Strategia di ingestion, template notebook Bronze/Silver/Gold, logging standard |
| **Gg stimati / completati** | 7 / 7 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 13 lug → 17 lug 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** revisione architetturale recepita — l'ingestion **non** è JDBC diretto ma **landing CSV in push (SFTP)**. Le attività JDBC (0.3.1/0.3.2) sono ❌ non applicabili, sostituite dalla strategia landing.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 0.3.1 | ~~Test connettività JDBC Oracle → Databricks~~ | 1 | ❌ | Architettura rivista: landing CSV push |
| 0.3.2 | ~~Benchmark JDBC / sizing partitioning~~ | 1 | ❌ | Sostituito da throughput CSV landing |
| 0.3.3 | Decision matrix ingestion per tabella | 1 | ✅ | `DOCS/decision_matrix_ingestion.md` v2.0 |
| 0.3.4 | Template Bronze (CSV landing → Delta MERGE) | 1 | ✅ | schema-on-read per header, row_hash pruning |
| 0.3.5 | Template Silver (cleansing 1:1, MERGE upsert) | 1 | ✅ | julian_to_date, normalize_sito, MERGE null-safe |
| 0.3.6 | Template Gold Fact (lookup, surrogate_key_fallback) | 1 | ✅ | chiavi naturali, orphan-rate check |
| 0.3.7 | Logging & alerting standard (JSON, alert failure) | 1 | ✅ | logging_helper.py + email alert Workflows |

**Decisioni:** ingestion in push su landing → elimina secret scope Oracle, VNet, `oracledb` sul cluster (coerente con D5).
