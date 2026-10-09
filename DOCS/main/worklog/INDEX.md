# Worklog — indice (per push su `main`)

> ⚠️ **File generato.** Non modificare a mano: rigenerare con
> `python scripts/worklog/worklog_index.py`. Convenzioni in [README](README.md),
> decisione in [ADR-0024](../adr/0024_worklog_diario_push.md).

**Ultimo push:** [Pausa degli schedule dei 7 job dev del logistico + fix durevole negli YAML (LL-037)](2026-10-09-01_pausa-schedule-job-dev.md) · 2026-10-09 · monorepo `PR #22 @c81f753 (fix + doc) + PR esito`

**54 voci.** La prima riga (in alto) è il push più recente = **stato corrente**.

| Data | Push | Cosa | ACT | ADR | LL | OP |
|---|---|---|---|---|---|---|
| 2026-10-09 | `PR #22 @c81f753 (fix + doc) + PR esito` | [Pausa degli schedule dei 7 job dev del logistico + fix durevole negli YAML (LL-037)](2026-10-09-01_pausa-schedule-job-dev.md) | — | — | LL-037 | — |
| 2026-10-06 | `merge PR #18 #16 #14 #19 #20 + chiusura #6` | [Merge PR pendenti (#14 #16 #18 #19 #20), chiusura #6 superata, pulizia branch monorepo](2026-10-06-01_merge-pr-pendenti-pulizia-branch.md) | ACT_9029 ACT_9025 ACT_9026 | — | LL-033 LL-034 | OP-TRA-1 |
| 2026-10-02 | `PR dedicata (extract_and_send.sh + ACT/OP/README/worklog)` | [Extract+send sul relay: primo carico reale in logisticolanding (307 file, ~2,23 GB)](2026-10-02-03_extract-send-sul-relay.md) | ACT_OP-INF-4 | — | — | OP-INF-4 OP-07 OP-08 |
| 2026-10-02 | `aa6231b` | [Checklist infra 12 allineata a provisioning consegnato + collaudo relay OK](2026-10-02-02_allineamento-doc12-collaudo.md) | ACT_OP-INF-4 | — | — | OP-INF-4 |
| 2026-10-02 | `235474c` | [Collaudo relay OK — upload reale verificato su logisticolanding](2026-10-02-01_collaudo-relay-ok.md) | ACT_OP-INF-4 | — | — | OP-INF-4 OP-07 |
| 2026-10-01 | `fa2972a` | [Reply consegna il provisioning (container + SAS + UC); avvio collaudo](2026-10-01-05_reply-consegna-provisioning.md) | ACT_OP-INF-4 | — | — | OP-INF-4 |
| 2026-10-01 | `09b4832` | [Lezioni LL-035/LL-036 (ssh RHEL6→OpenSSH10) estratte da ACT_OP-INF-4](2026-10-01-04_lessons-ssh-ll035-ll036.md) | ACT_OP-INF-4 | ADR-0020 | LL-035 LL-036 | OP-INF-4 |
| 2026-10-01 | `a39e7a3` | [ACT dedicata relay odisrvcno3 + trigger ODI (recap attività)](2026-10-01-03_act-op-inf-4-relay.md) | ACT_OP-INF-4 ACT_9012 | — | — | OP-INF-4 |
| 2026-10-01 | `6d13af3` | [Convenzione path <env>/<sistema> + sender e trigger ODI multi-ambiente](2026-10-01-02_path-env-sistema-sender-odi.md) | ACT_9012 | — | — | OP-07 OP-INF-4 |
| 2026-10-01 | `9f727f7` | [Trigger A (ssh forced command) validato su odisrvcno1/2](2026-10-01-01_trigger-a-ssh-validato.md) | ACT_9012 | — | — | OP-INF-4 |
| 2026-09-30 | `44f88bb` | [Risposta finale a Reply + chiarita landing interim (Volume managed, non SFTP)](2026-09-30-01_risposta-finale-reply-landing-volume.md) | ACT_9012 | — | — | OP-INF-4 |
| 2026-09-29 | `config.yaml estrattore + worklog (PR dedicata)` | [Disabilitati 3 siti (laix, lfsx, lgsx) dalle estrazioni landing (ORA-12514, siti spenti)](2026-09-29-02_disabilitati-3-siti-estrazione.md) | — | — | — | — |
| 2026-09-29 | `3d1a58a` | [Reply conferma provisioning AzCopy + trigger A (open point ssh)](2026-09-29-01_reply-conferma-provisioning-azcopy.md) | ACT_9012 | — | — | OP-INF-4 |
| 2026-09-25 | `PR #14 (feat/act-9029) allineata a main + esito` | [Quadratura F_CARICO: estrattore validato + estrazione CDT_DW 22-23 Sett + confronto fase 1 (chiavi/colonne)](2026-09-25-04_quadratura-f-carico-estrazione-22-23.md) | ACT_9029 | — | — | Q-01 |
| 2026-09-25 | `doc-pass worklog (PR dedicata)` | [Giro completo giorno 24: estrazione+landing cloud + run 7/7 via MI (grant UC ok)](2026-09-25-03_giro-completo-24-via-mi.md) | — | — | LL-033 LL-032 LL-034 | OP-INF-3 |
| 2026-09-25 | `dcf4d24` | [Richiesta provisioning AzCopy inviata a Reply](2026-09-25-02_richiesta-provisioning-azcopy-reply.md) | ACT_9012 | — | — | OP-INF-4 |
| 2026-09-25 | `d32acf3` | [Relay AzCopy odisrvcno3 pronto (staging+NFS+AzCopy)](2026-09-25-01_relay-odisrvcno3-pronto.md) | — | ADR-0023 | — | OP-INF-4 |
| 2026-09-24 | `PR dedicata (silver_pesate.py + LL-034 + worklog + INDEX)` | [Fix duplicati F_CARICO: chiave naturale pesata senza DATA_BOLLA (silver_pesate) — LL-034](2026-09-24-01_fix-dup-fcarico-chiave-pesata.md) | — | — | LL-034 | OP-CAR-3 |
| 2026-09-23 | `PR dedicata (feat/act-9029)` | [Estrattore row-level CDT_DW.F_CARICO per quadratura a gradi (ACT_9029, Q-01)](2026-09-23-05_estrattore-f-carico-rowlevel.md) | ACT_9029 | — | — | Q-01 |
| 2026-09-23 | `PR doc (LL-033 + worklog)` | [Run 11→22 cloud DEV bloccato: la MI (run_as) non ha i grant UC sui dati (LL-033)](2026-09-23-04_run-1122-cloud-blocco-grant-mi.md) | — | — | LL-033 | — |
| 2026-09-23 | `PR dedicata (databricks.yml + LL-032 + worklog)` | [Permessi job DAB: CAN_MANAGE Group-Engineering-dev nel databricks.yml (target dev) — LL-032](2026-09-23-03_permessi-dab-can-manage-group-engineering-dev.md) | — | — | LL-032 | — |
| 2026-09-23 | `667bf00` | [OP-INF-4: host extract&send target su Windows](2026-09-23-03_op-inf-4-host-extract-send.md) | — | ADR-0023 | — | OP-INF-4 |
| 2026-09-23 | `c743f99` | [AzCopy: thread piattaforma concluso, decisioni (SAS + container)](2026-09-23-02_azcopy-thread-esito.md) | ACT_9012 | ADR-0023 | — | OP-07 |
| 2026-09-23 | `n/d (doc-pass, da pushare)` | [Decisioni ambienti: modello 4 livelli (ADR-0027) + auth CI = MI unica; naming stage; ACT_9028](2026-09-23-01_decisioni-4-ambienti-e-auth-ci.md) | ACT_9028 | ADR-0027 | LL-030 | OP-INF-3 |
| 2026-09-21 | `doc-pass runbook16 + worklog (PR dedicata)` | [Release GitLab workflows v0.1.7 (fix .cache LL-029) — verifica CI dev cliente](2026-09-21-02_release-gitlab-workflows-v017-verifica-ci.md) | — | — | LL-031 LL-030 LL-029 | OP-INF-3 |
| 2026-09-21 | `PR #10 (main @95651b2) + doc-pass (LL-030, OP-INF-3, worklog)` | [Incidente job duplicati CI (LL-030) + merge fix LL-029 su main (PR #10) + estrazioni locali 10→21](2026-09-21-01_incidente-duplicati-ci-e-estrazioni-locali.md) | — | — | LL-030 LL-029 | OP-INF-3 |
| 2026-09-10 | `n/d (solo DEV, non ancora pushato)` | [Run completo 09 set (7/7) + allineamento anagrafiche e load storico 03→08 (42/42 verde) + fix LL-029 .cache() serverless](2026-09-10-01_run-completo-09-e-storico-0308.md) | — | — | LL-029 | — |
| 2026-09-04 | `(main @6420869 → doc pass su branch docs/release-7su7-multirepo)` | [Release multi-repo: GitHub (4) + GitLab (lib v1.0.5, workflows v0.1.6) + doc pass (ADR-0026)](2026-09-04-02_release-multirepo-v105-v016.md) | ACT_9026 ACT_9027 ACT_CND-01 | ADR-0026 | LL-013 LL-025 LL-026 LL-027 LL-028 | OP-TRA-1 OP-CND-1 |
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

