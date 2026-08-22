# Sprint 0.2 — GitLab CI/CD & Databricks Asset Bundles

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
| **Obiettivo** | CI/CD GitLab, Databricks Asset Bundles, libreria `logistica_utils` |
| **Gg stimati / completati** | 5 / 5 |
| **% avanzamento** | 100% |
| **Stato** | ✅ COMPLETO |
| **Data inizio → fine** | 6 lug → 10 lug 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** sprint completato offline. Il deploy effettivo su cloud dipende dai prerequisiti dello Sprint 0.1 (subgroup GitLab, workspace). La pipeline CI/CD andrà adattata ai **3 repo** del subgroup `logistico` (multi-repo, non mono-repo).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 0.2.1 | Struttura repository GitLab (layout, .gitignore, branch protection) | 1 | ✅ | notebooks/, workflows/, tests/, lib/, infra/terraform/ |
| 0.2.2 | Databricks Asset Bundles (`databricks.yml` dev) | 1 | ✅ | job reference + variabili catalog/schema per ambiente |
| 0.2.3 | Pipeline GitLab CI — stage DEV (validate + deploy-dev) | 1 | ✅ | `.gitlab-ci.yml`: validate, test, deploy-dev |
| 0.2.4 | Pipeline GitLab CI — gate PROD (manual approval) | 1 | ✅ | Gate manuale su merge a main |
| 0.2.5 | Libreria `logistica_utils` (6 moduli, 64 test) | 1 | ✅ | secret_helper, logging, delta, dq, utils, storage; wheel |

## Note di adattamento (per il deploy cloud)
- `databricks.yml`: compute serverless (D 2026-07-03).
- Struttura da riportare sui 3 repo: `logistico-infrastructure` (terraform), `logistico-workflows` (notebooks+DAB), `logistico-lib` (wheel).
- Secret CI/CD: solo auth (`ARM_*` + `DATABRICKS_TOKEN`), meccanismo in def. con Technology.
