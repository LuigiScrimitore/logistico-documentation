# Worklog — indice (per push su `main`)

> ⚠️ **File generato.** Non modificare a mano: rigenerare con
> `python scripts/worklog/worklog_index.py`. Convenzioni in [README](README.md),
> decisione in [ADR-0024](../adr/0024_worklog_diario_push.md).

**Ultimo push:** [Run E2E 7 job DEV: da 1/7 a 7/7 verde (fix serverless/ANSI + CND + canonico sito)](2026-09-04-01_run7job-7su7-verde.md) · 2026-09-04 · monorepo `(PR #7 feat/act-9026-dim-sito-slogistix)`

**26 voci.** La prima riga (in alto) è il push più recente = **stato corrente**.

| Data | Push | Cosa | ACT | ADR | LL | OP |
|---|---|---|---|---|---|---|
| 2026-09-04 | `(PR #7 feat/act-9026-dim-sito-slogistix)` | [Run E2E 7 job DEV: da 1/7 a 7/7 verde (fix serverless/ANSI + CND + canonico sito)](2026-09-04-01_run7job-7su7-verde.md) | ACT_9027 ACT_9026 ACT_CND-01 | — | LL-027 LL-028 LL-021 LL-022 LL-026 | OP-TRA-1 |
| 2026-09-03 | `8377bfb (PR #7)` | [dim_sito da S_LOGISTIX+WL1: orphan sito trasporti = 0 (ACT_9026) + fix wheel LL-025/LL-026](2026-09-03-03_dim-sito-slogistix-orphan-trasporti-zero.md) | ACT_9026 | — | LL-025 LL-026 | OP-TRA-1 |
| 2026-09-03 | `bae018f` | [Fix sito canonico alfabetico: giacenze verde, trasporti parziale (OP-TRA-1) + LL-025](2026-09-03-02_fix-sito-canonico.md) | ACT_9025 | — | LL-025 | OP-TRA-1 |
| 2026-09-03 | `e5edcdc` | [E2E giacenze/trasporti: ACT_9024 validato; blocco sito sistemico (OP-TRA-1)](2026-09-03-01_e2e-giacenze-trasporti-sito.md) | ACT_9024 ACT_ST-01 | — | LL-021 | OP-TRA-1 |
| 2026-09-02 | `eef96a9` | [Formalizza follow-up: ACT_9023 cleanup pesata + OP-INF-3 modello dev/qa/prod](2026-09-02-05_formalizza-followup.md) | ACT_9023 | — | — | OP-INF-3 |
| 2026-09-02 | `2d28898` | [Capitalizzazione: LL-022/023/024 + ACT_9019/9021/9022 (doc-sync dei fix mergiati)](2026-09-02-04_capitalizzazione-lezioni.md) | ACT_9019 ACT_9020 ACT_9021 ACT_9022 | — | LL-022 LL-023 LL-024 | OP-08 |
| 2026-09-02 | `27590e7` | [Sandbox self-deploy (root_path home) + fix JDN + extractor ignore-odi-flag; carichi E2E verde](2026-09-02-03_sandbox-selfdeploy-e2e-carichi.md) | ACT_9020 | — | — | — |
| 2026-09-02 | `45f8224` | [Carichi E2E verde su dato reale; dim_refresh 17/17; aperta ACT_CND-01 (bronze cnd)](2026-09-02-02_carichi-e2e-verde.md) | ACT_CND-01 | ADR-0025 | LL-020 LL-021 | OP-CND-1 |
| 2026-09-02 | `11e1b11` | [DQ finding carichi = watermark; fix partitionOverwriteMode (serverless) + prep massa critica](2026-09-02-01_massa-critica-prep.md) | — | ADR-0025 | LL-020 LL-021 | — |
| 2026-09-01 | `efa616b` | [Catena carichi VERDE end-to-end (bronze->silver->gold) su serverless con dati reali](2026-09-01-12_catena-carichi-verde-e2e.md) | — | ADR-0025 | LL-020 LL-021 | — |
| 2026-09-01 | `0794b57` | [Fix serverless carichi committati + base catena gold (landing_ingestion/dim_refresh preparati)](2026-09-01-11_fix-serverless-carichi.md) | — | ADR-0025 | LL-020 LL-021 | — |
| 2026-09-01 | `n/d (docs)` | [Smoke test carichi DEV: bronze+silver verdi E2E su dati reali](2026-09-01-10_smoke-test-carichi.md) | — | ADR-0025 | LL-020 LL-021 | — |
| 2026-09-01 | `1b685f6` | [Fix wrapper seed: parametri lista (string[]) + nota versione CLI runbook](2026-09-01-09_fix-wrapper-param-liste.md) | — | — | — | — |
| 2026-09-01 | `8541a4e` | [Runbook 17: chiarita install CLI (winget ok, pip legacy deprecato)](2026-09-01-08_fix-runbook-cli-install.md) | — | — | — | — |
| 2026-09-01 | `3cbac76` | [Wrapper PowerShell seed_landing_dev (estrai->copia->archivia)](2026-09-01-07_wrapper-seed-landing.md) | — | — | — | — |
| 2026-09-01 | `8ea19bf` | [Runbook 17: seed manuale landing DEV (workaround pre-AzCopy)](2026-09-01-06_runbook-seed-landing-manuale.md) | — | — | — | OP-GIA-1 OP-QDR-1 |
| 2026-09-01 | `432d32e` | [Infra DEV completa: apply v0.1.6 verde (6 grants), ACT_0.1.6 chiuso](2026-09-01-05_apply-infra-dev-completo.md) | ACT_0.1.6 | — | — | — |
| 2026-09-01 | `6ba1223` | [Hook pre-push per gli INDEX generati (worklog, lessons)](2026-09-01-04_pre-push-hook.md) | — | ADR-0024 | — | — |
| 2026-09-01 | `c8afe89` | [Fix nome gruppo engineer (Group-Engineering-dev) -> OP-INF-2 chiuso, v0.1.6](2026-09-01-03_fix-nome-gruppo-engineering.md) | ACT_0.1.6 | — | — | OP-INF-2 |
| 2026-09-01 | `435b27d` | [Introdotto il worklog (ADR-0024)](2026-09-01-02_worklog-introdotto.md) | — | ADR-0024 | — | — |
| 2026-09-01 | `4d75de3` | [Apply infra DEV parziale — grant MI ottenuto, gruppo Engineering-dev non risolto](2026-09-01-01_apply-infra-parziale.md) | ACT_0.1.6 | — | LL-019 | OP-INF-1 OP-INF-2 |
| 2026-08-31 | `9fac961` | [Backend AzCopy per il send verso landing](2026-08-31-03_backend-azcopy.md) | ACT_9012 | ADR-0023 | — | — |
| 2026-08-31 | `a37424a` | [Inviata richiesta accesso container AzCopy (§F.2)](2026-08-31-02_richiesta-container-azcopy.md) | ACT_9012 | — | — | — |
| 2026-08-31 | `3fc43a2` | [ADR-0023 — trasporto landing via AzCopy (non SFTP)](2026-08-31-01_adr-0023-azcopy.md) | ACT_9012 | ADR-0023 | — | — |
| 2026-08-28 | `4894942` | [ADR-0022 — auth CI/CD via Managed Identity (no secret)](2026-08-28-02_adr-0022-auth-msi.md) | ACT_0.1.6 ACT_9018 | ADR-0022 | — | — |
| 2026-08-28 | `cc2505d` | [Allineamento doc post multi-repo deploy (auth secret -> MSI)](2026-08-28-01_doc-sync-multirepo-deploy.md) | — | — | — | OP-INF-1 |

