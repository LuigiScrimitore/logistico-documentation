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

**Note di sprint:** sprint completato offline. Il deploy effettivo su cloud dipende dai prerequisiti dello Sprint 0.1 (subgroup GitLab, workspace). **Aggiornamento 2026-08-22**: lo split multi-repo è stato **eseguito** — 4 repo su GitHub (SoT) e pilot `logistico-lib` completato sul GitLab cliente (CI verde + wheel nel Package Registry). Vedi [[ACT_9011]] (split) e [[ACT_9017]] (tooling `split_to_multirepo.py` / `promote_to_gitlab.py`). La CI/CD di questo sprint è quindi confluita nei `.gitlab-ci.yml` per-repo generati.

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 0.2.1 | Struttura repository GitLab (layout, .gitignore, branch protection) | 1 | ✅ | notebooks/, workflows/, tests/, lib/, infra/terraform/ |
| 0.2.2 | Databricks Asset Bundles (`databricks.yml` dev) | 1 | ✅ | job reference + variabili catalog/schema per ambiente |
| 0.2.3 | Pipeline GitLab CI — stage DEV (validate + deploy-dev) | 1 | ✅ | `.gitlab-ci.yml`: validate, test, deploy-dev |
| 0.2.4 | Pipeline GitLab CI — gate PROD (manual approval) | 1 | ✅ | Gate manuale su merge a main |
| 0.2.5 | Libreria `logistica_utils` (6 moduli, 64 test) | 1 | ✅ | secret_helper, logging, delta, dq, utils, storage; wheel |

## Note di adattamento (per il deploy cloud)
- `databricks.yml`: compute serverless (D 2026-07-03). **NB**: consolidamento dei due `databricks.yml` in
  `logistico-workflows` ancora aperto → [[ACT_9018]].
- Struttura riportata sui repo (eseguito, ACT_9011): `logistico-infrastructure` (terraform),
  `logistico-workflows` (notebooks+DAB), `logistico-lib` (wheel), `logistico-documentation` (solo GitHub).
- Secret CI/CD: solo auth (`ARM_*` + `DATABRICKS_TOKEN`), variabili masked per-repo (ADR-0005). Runner: group
  runner `azure-runner` del subgroup (i job vanno taggati → [[LL-011]]); CA aziendale nel container → [[LL-012]].
