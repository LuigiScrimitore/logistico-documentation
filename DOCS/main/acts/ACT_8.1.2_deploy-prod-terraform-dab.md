# ACT_8.1.2 · Deploy PROD (terraform apply, DAB --target prod)

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.1
**Sprint**: 8.1 — Shadow Mode Setup
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (dipende da provisioning PROD)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.1   **Blocca**: ACT_8.1.3, ACT_8.3.4
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0009_job_cluster_serverless]], [[0016_multi_repo_gitlab]], [[0001_config_dev_control_catalog]], [[0002_bronze_condiviso_lu]], [[0003_uc_volume_landing]]   **OP collegati**: —

## Contesto e motivazione
Con il workspace PROD disponibile (ACT_8.1.1), l'infra (schemi UC, Volume landing, grants, cluster policy)
e i bundle Databricks Asset Bundle vanno materializzati in PROD. È lo step che porta codice e risorse dal
repo all'ambiente PROD, replicando su target `_prod` quanto già validato in DEV
([[11_devops_handoff_databricks]] FASI A e B).

## Obiettivo
Infra e bundle deployati in PROD: `terraform apply` (brownfield, target prod) completato e DAB deployato
con `--target prod`. Fatto = schemi UC/Volume/grants/policy e job/workflow presenti nel workspace PROD,
pronti per l'attivazione (→ ACT_8.1.3).

## Analisi tecnica
- **Terraform brownfield** (`infra/terraform/brownfield/`, [[11_devops_handoff_databricks]] §5.1):
  - referenzia i cataloghi PROD esistenti (`data "databricks_catalog"`; plan fallisce se mancano);
  - crea gli schemi: `bronze_prod.logistica`, `bronze_prod.condiviso` (D2, [[0002_bronze_condiviso_lu]]),
    `silver_prod.logistica`, `silver_prod.logistica_curated`, `gold_prod.logistica`, `gold_prod.logistica_dm`,
    `config_prod.logistica_etl` (watermark, D1 [[0001_config_dev_control_catalog]]);
  - Volume landing `landing_prod.logistica.files` (D3, [[0003_uc_volume_landing]]);
  - compute: **nessuna cluster policy** (serverless — [[0009_job_cluster_serverless]]; la vecchia policy è
    stata rimossa con [[ACT_9007]]). Verificare invece che il `bundle validate/deploy` risolva il wheel
    dichiarato in `environments.spec.dependencies` e che i job partano su serverless;
  - **grants**: gruppo engineer PROD (equivalente `Engineering-dev`); **reader grant condizionale**
    (`enable_reader_grants`) → da abilitare per il gruppo analisti/MicroStrategy quando esiste (A5, nesso
    con ACT_8.3.4).
  - Backend `azurerm` e `terraform.tfvars` con i **valori PROD** (secondo set, oggi non compilato — da
    predisporre; i nomi RG/SA PROD sono **da verificare**).
- **Sequenza deploy** (analoga a DEV, [[11_devops_handoff_databricks]] §4):
  `preflight_databricks.sh --catalog-control config_prod` → `terraform init` → `terraform plan`
  → **review con Ippazio** → `terraform apply` → `databricks bundle validate/deploy -t prod`.
- **DAB / workflow** (`infra/databricks_bundle/`, `databricks.yml` + `resources/`, KIT-06 [[14_release_kit]] §3.D):
  target `prod` con default risolti (landing Volume, `siti` per area), job cluster serverless, tag di costo
  KIT-05 (`business_unit=logistica`, `pipeline=…`, `wave=…`, [[0015_tuning_cloud_non_trasferibile]] per il
  sizing da ri-tarare). Verificare che host/secret PROD siano configurati (secret **solo auth**:
  `ARM_*` + `DATABRICKS_HOST/TOKEN`, [[0005_no_secret_oracle_export_landing]] — niente secret Oracle).
- **Guardrail** ([[11_devops_handoff_databricks]] §6): usare **solo** `brownfield/` (NON il root module né
  `modules/unity_catalog`/`networking` greenfield); non committare `terraform.tfvars`/token.

## Sviluppo (diario)
- 2026-07-03 · in attesa di ACT_8.1.1.

## Verifica
- `terraform plan` PROD mostra **solo** schemi/Volume/grants/policy (nessun catalog creato); `terraform apply`
  senza errori.
- `databricks bundle validate -t prod` OK; `databricks bundle deploy -t prod` OK; job/workflow visibili nel
  workspace PROD.
- Smoke-test fondamenta (KIT-12, [[14_release_kit]] §5): create/drop tabella dummy per schema + verifica
  grant read/write.

## Esito
— (bloccato)

## Follow-up
Al gate CI/CD PROD: cablare i secret auth nelle variabili di progetto GitLab (analogo C4 DEV). Reader-grant
MicroStrategy: coordinare con ACT_8.3.4.
