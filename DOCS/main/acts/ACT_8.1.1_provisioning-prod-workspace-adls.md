# ACT_8.1.1 · Provisioning Databricks Workspace PROD + ADLS

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.1
**Sprint**: 8.1 — Shadow Mode Setup
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (utenza/subscription Azure PROD)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: —   **Blocca**: ACT_8.1.2, ACT_8.1.3 (e tutta la FASE 8)
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0003_uc_volume_landing]], [[0004_naming_ambienti_prod_stage]], [[0009_job_cluster_serverless]]   **OP collegati**: —

## Contesto e motivazione
Tutta la FASE 8 (shadow mode → cut-over) gira in PROD. Senza il workspace Databricks PROD e lo storage
ADLS provisionati non è possibile né deployare né attivare i workflow: è il **prerequisito assoluto e
bloccante** dell'intera fase (milestone `fase_8.md` §5, prerequisito **I-01**).

Il DEV è già completamente definito e validato: workspace `adb-3179436993731139.19.azuredatabricks.net`,
backend TF state su `rg-dev-dataplatform-00` / `stdevdataplatformweu00` / container `statefile`
([[12_checklist_infra_setup]] §A). Il PROD è lo **speculare** del DEV secondo la decisione D4
([[0004_naming_ambienti_prod_stage]]): cataloghi con suffisso `_prod` (`bronze_prod`, `silver_prod`,
`gold_prod`, `config_prod`), stage `_stage` **non** da configurare per questo rilascio, e i cataloghi
senza suffisso saranno eliminati. `_CATALOG_MAP["prod"]` è già cablato in `utils.py`; PROD non è però
ancora deployato.

## Obiettivo
Workspace Databricks PROD e account ADLS PROD provisionati e accessibili. Fatto = si può eseguire
`terraform apply` sul target prod (→ ACT_8.1.2) senza errori di accesso/risorse mancanti, e il preflight
`scripts/migration/preflight_databricks.sh` è verde su tutti i cataloghi target PROD.

## Analisi tecnica
- **Provisioning Azure**: subscription/resource group PROD, workspace Databricks PROD, account/container
  ADLS Gen2 PROD. Allineare naming e struttura al DEV (rif. FASE 0 — Fondamenta Infrastrutturali).
- **Cataloghi UC PROD**: verificare l'esistenza dei cataloghi `bronze_prod`/`silver_prod`/`gold_prod`/
  `config_prod`/`landing_prod` nel metastore Unity Catalog aziendale. Il Terraform brownfield **referenzia**
  i cataloghi (`data "databricks_catalog"`) e **fallisce** se non esistono (fail-safe): i cataloghi non li
  creiamo noi, li crea/espone il team DWH ([[11_devops_handoff_databricks]] §5.1).
- **Compute serverless** ([[0009_job_cluster_serverless]]): nessun `node_type_id`/VM da provisionare e
  **nessuna cluster policy** da creare (non si applicano al serverless — correzione [[ACT_9007]]). Requisito
  di piattaforma: il workspace deve avere **UC abilitato** ed essere in una **region che supporta il
  serverless**. Attribuzione costi via serverless usage policy → [[ACT_9013]].
- **Backend TF state PROD**: predisporre RG/Storage Account/container `statefile` per il target prod
  (secondo set di `terraform.tfvars`, oggi non attivo — [[11_devops_handoff_databricks]] §3 D4).
- **Prerequisiti d'accesso** (equivalenti PROD dei blocchi DEV in [[12_checklist_infra_setup]] §G):
  utenza Azure PROD (analoga ad A7, da PM), permessi UC gruppo engineer PROD (analogo D6/`Engineering-dev`),
  credenziali SFTP landing PROD (analogo C5). Nomi/gruppi PROD specifici: **da verificare** col cliente.
- **Coordinamento** con Reply/IT per accessi e IAM PROD; la review `terraform plan` con Ippazio precede
  l'apply (analoga ad A4 DEV).

## Sviluppo (diario)
- 2026-07-03 · attività non avviabile: in attesa provisioning infra PROD.

## Verifica
- Login al workspace PROD riuscito; container ADLS PROD raggiungibili.
- `preflight_databricks.sh --catalog-control config_prod` verde (autenticazione CLI + cataloghi target
  esistenti).
- `terraform plan --target prod` (o su `brownfield/` con tfvars prod) gira senza errori di
  autenticazione/risorse mancanti — pronto per ACT_8.1.2.

## Esito
— (bloccato da provisioning infra PROD)

## Follow-up
Nessuna se non applicabile. Se al provisioning emergono divergenze di naming PROD vs `_CATALOG_MAP["prod"]`
→ aprire ACT emergente 9000+.
