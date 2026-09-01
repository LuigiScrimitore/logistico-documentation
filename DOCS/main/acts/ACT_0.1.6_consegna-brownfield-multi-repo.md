# ACT_0.1.6 · Consegna Terraform `brownfield/` in multi-repo GitLab

**Status**: ✅ done (2026-09-01 — `apply` v0.1.6 verde: 8 schemi + Volume landing + 6 grants `Group-Engineering-dev` in DEV; 0 destroy)
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 1   **Blocco**: 🟢 sbloccato — resta solo l'esecuzione dell'`apply` (gate manuale in CI, [[ACT_8.1.2]])
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: ACT_0.1.1, ACT_0.1.2 (codice risorse), [[ACT_9011]] (split → repo `logistico-infrastructure`)   **Blocca**: apply infra (0.1.1/0.1.2/0.1.3/0.1.7)
**ADR collegate**: ADR-0016 (multi-repo GitLab), ADR-0004 (naming ambienti)   **OP collegati**: —

## Contesto e motivazione
Il root module greenfield `infra/terraform/` è **deprecato**: in brownfield si applica solo l'overlay
`infra/terraform/brownfield/`. La consegna del codice segue la scelta **multi-repo** (ADR-0016): non un
mono-repo importato con `git_monorepo_import.sh` (ora obsoleto), ma tre repo nel subgroup GitLab
`logistico`. Senza subgroup + repo creati e state backend agganciato, nessun `apply` è possibile → questa
ACT sblocca l'esecuzione di tutta la Fase 0.

## Obiettivo
`brownfield/` versionato nei repo `logistico`, backend `azurerm` funzionante, `terraform init && plan`
verde in DEV, MR revisionata con Reply. Fatto = pronti per `apply`.

## Analisi tecnica
- Applicare **solo** `infra/terraform/brownfield/` (greenfield `infra/terraform/` deprecato).
- Backend `azurerm` già compilato coi valori DEV reali: RG `rg-dev-dataplatform-00`, storage
  `stdevdataplatformweu00`, container `statefile`.
- Multi-repo (ADR-0016): `logistico-infrastructure`, `logistico-workflows`, `logistico-lib` nel subgroup
  `logistico`. `git_monorepo_import.sh` **obsoleto**, non usarlo.

## Autenticazione DEV — Managed Identity (risposta team 2026-08-27)
Il team ha scelto **Managed Identity** per autenticarsi ad Azure/Databricks dal runner GitLab: **niente
`client_secret`, niente token Databricks**. Il runner Azure (`vm-prod-devops-00`) ha una MI user-assigned; TF
la usa via `ARM_USE_MSI=true`. Backend `azurerm` (`use_azuread_auth=true`) e provider azurerm autenticano con
la MI; il provider `databricks` con `azure_use_msi = true` (aggiunto in `main.tf`).

**Variabili CI da impostare** (Settings → CI/CD → Variables, **Protected** — NON sono segreti, sono identificatori):
| Variabile | Valore |
|---|---|
| `ARM_CLIENT_ID` | client id della **user-assigned MI** DEV |
| `ARM_TENANT_ID` | tenant DEV |
| `ARM_SUBSCRIPTION_ID` | subscription DEV |
| `TF_VAR_databricks_host` | `https://adb-3179436993731139.19.azuredatabricks.net` (workspace DEV) |

(`ARM_USE_MSI=true` è già nel `.gitlab-ci.yml` generato.) I valori DEV sono stati forniti dal team e vanno
inseriti come variabili CI — **non** si committano nel repo.
**Permessi MI**: attesi sufficienti per il rilascio (state storage `stdevdataplatformweu00/statefile`,
subscription/RG DEV, workspace Databricks). Referente permessi: Francesco Giambona (Technology Reply,
fr.giambona@reply.it) se il `plan` segnala mancanze.

## Sviluppo (diario)
- 2026-07-03 · backend DEV compilato; codice pronto; MR pendente su creazione subgroup.
- 2026-08-03 · **subgroup GitLab disponibile** (`CNO/cno-data-platform/logistico`, Maintainer). Lo split del
  monorepo → repo `logistico-infrastructure` è ora tracciato in [[ACT_9011]]. Resta il blocco A7 (utenza Azure)
  per `init/plan/apply`.
- 2026-08-22 · **repo `logistico-infrastructure` pronto e pushato su GitHub** (via split, [[ACT_9011]]/[[ACT_9017]]);
  **group runner `azure-runner` disponibile** e verificato col pilot `logistico-lib`; **progetto GitLab creato**
  nel subgroup. Il `.gitlab-ci.yml` generato è **solo `validate` + `plan`** (nessun `apply`/`destroy` → **fase
  non distruttiva**; l'`apply`/PROD è separato, [[ACT_8.1.2]]). Unico blocco residuo: le **`ARM_*`** (service
  principal, utenza A7) come variabili CI masked, necessarie a `init`/`plan` (autenticazione al backend
  `stdevdataplatformweu00/statefile` e refresh dello stato — sola lettura).
- 2026-08-22 (bring-up CI su GitLab, non distruttivo) · superati 3 intoppi di pipeline, tutti fixati nel
  generatore `split_to_multirepo.py` (valgono per tutti i repo): (1) runner `stuck` → `tags:[azure-runner]`
  ([[LL-011]]); (2) `Terraform has no command named "sh"` → `image.entrypoint:[""]`; (3) `No configuration
  files` → `terraform -chdir=terraform/brownfield`. Ora **`validate` verde** e **`plan`** arriva all'auth del
  backend e si ferma su *"could not configure AzureCli Authorizer: 'az' not found"* = **mancano le `ARM_*`**
  (vedi sezione Credenziali). CI dimostrato corretto fino all'autenticazione; nessun'azione distruttiva.

## Verifica
`terraform init` aggancia lo state su `stdevdataplatformweu00/statefile`; `terraform plan` verde in DEV;
MR approvata da Ippazio (Reply).

## Esito
- Repo su GitHub (SoT) pronto; **promosso su GitLab** (`logistico-infrastructure`, snapshot `v0.1.3`); runner ok.
- Pipeline non distruttiva (`validate` ✅ / `plan` bloccato all'auth backend). CI provato corretto fino
  all'autenticazione.
- **2026-08-27 — credenziali ricevute (Managed Identity)**: adeguati codice e CI (`ARM_USE_MSI=true`,
  `azure_use_msi` sul provider databricks, `databricks_host` DEV via CI var).
- **2026-08-27 — `plan` DEV VERDE** ✅: impostate le 4 variabili CI. Nota: le variabili sono **Protected** e
  funzionano perché `main` è un **branch protetto** → esposte al job (con `main` non protetto sparivano e il
  `plan` chiedeva `databricks_host` — [[LL-016]]). `init` autentica al backend via MSI, `plan` legge lo stato
  in sola lettura. **Correzione al mio consiglio precedente**: le var vanno bene **Protected** (posture
  corretta) purché `main` sia protetto — non serve toglierle.

## Follow-up
- ✅ Promosso su GitLab; ✅ variabili CI (MSI) impostate; ✅ `plan` DEV verde; ✅ stage `apply` manuale in CI.
- ✅ **Plan rivisto (2026-08-27)**: `15 to add, 0 to change, 0 to destroy` — additivo, brownfield corretto (5
  catalog letti, non toccati). Crea 8 schemi + Volume `landing.files` + 6 grants `Engineering-dev`, tutti
  `force_destroy=false`/`managed_by=terraform`. **Safe da applicare.** `tfplan` salvato come artefatto.
- **2026-08-27 — `apply` DEV tentato → bloccato sui permessi MI** (auth MSI ok, ma **0 risorse create**, stato
  invariato): `cannot create schema: User does not have CREATE SCHEMA on Catalog '<cat>'` su **tutti** i 5
  catalog. La MI legge i catalog ma non ha `CREATE SCHEMA`. → **richiesta a Francesco Giambona (Reply)**:
  concedere alla MI (SP applicationId `54d17490-…`) **`USE CATALOG` + `CREATE SCHEMA`** su `bronze_dev`,
  `silver_dev`, `gold_dev`, `config_dev`, `landing_dev`. PROD → [[ACT_8.1.2]].
- **2026-09-01 — grant ASSEGNATI (team infrastructure)** ✅: `USE CATALOG` + `CREATE SCHEMA` concessi alla MI
  **`id-dev-dataplatform-workload-00`** (= SP applicationId `54d17490-…`) sui 5 catalog DEV. **OP-INF-1 chiuso**
  ([[LL-018]]: authN era già ok, mancava authZ → ora concessa). **Prossimo passo: ri-lanciare la pipeline
  `infrastructure`** (rigenera `plan`/`tfplan`) e **cliccare il job `apply`** (gate manuale). Atteso: 15 add
  (8 schemi + Volume `landing.files` + 6 grants), 0 destroy. A `apply` verde → ACT_0.1.6 close + sblocco
  0.1.1/0.1.2/0.1.3/0.1.7.
- **2026-09-01 — `apply` fallito su piano stale/lock** ([[LL-019]]): dopo il grant, l'`apply` ha dato
  *"Inconsistent dependency lock file"* + *"Saved plan is stale"*. Causa: il job `apply` rifà `init` senza il
  lock/provider del `plan` (lock gitignorato, veicolato solo `tfplan`) **e** applicava un piano non coerente con
  lo stato corrente. **Fix nel generatore** `split_to_multirepo.py`: il `plan` passa all'`apply` anche
  `.terraform.lock.hcl` + `.terraform/` (`needs:[plan]`), `apply` fa `init -lockfile=readonly`. **Procedura:**
  ri-lanciare l'**intera** pipeline (plan+apply stesso run) contro lo stato corrente, non ri-cliccare apply
  vecchi. NB: pinnare l'immagine Terraform (non `latest`).
- **2026-09-01 — `apply` v0.1.5 ESEGUITO (parziale)**: fix CI OK (nessun errore lock/stale). **Creati**: 8 schemi
  (`bronze/silver/silver_curated/gold/gold_dm/config.logistica_etl`, `condiviso`, `landing.logistica`) + **Volume
  `landing_dev.logistica.files`**. **Fallito** sui 6 `databricks_grants`: *"cannot create grants: Could not find
  principal with name Engineering-dev"* → **[[OP-INF-2]]**. Stato Terraform consistente (schemi/Volume tracciati).
- **2026-09-01 — OP-INF-2 chiuso: era il NOME del gruppo.** Verificato nel workspace (Settings → Profile / Catalog
  `bronze_dev` Permissions): il gruppo reale è **`Group-Engineering-dev`** (prefisso `Group-`), già assegnato al
  workspace con `ALL PRIVILEGES`/`MANAGE`. Il default storico `Engineering-dev` era sbagliato. **Fix**:
  `variables.tf` → `default = "Group-Engineering-dev"`. **Next**: release **v0.1.6** → promozione GitLab → ri-run
  pipeline → i 6 grant si applicano (idempotente, 0 destroy). Chiude l'`apply` DEV completo.
- **2026-09-01 — `apply` v0.1.6 VERDE ✅ (infra DEV completa)**: `Apply complete! Resources: 6 added, 0 changed,
  0 destroyed`. Applicati i 6 `databricks_grants` a `Group-Engineering-dev` su bronze/silver/silver_curated/gold/
  gold_dm/config.logistica_etl. Output: `schemi_creati` (6+condiviso) + `landing_volume_path=/Volumes/landing_dev/
  logistica/files`. **Fondamenta UC DEV provisionate** (8 schemi + Volume + grants). ACT_0.1.6 **chiuso** → sblocca
  gli ACT 0.1.1/0.1.2/0.1.3/0.1.7. Restano prereq di piattaforma per l'ingestion (container AzCopy §F.2) e PROD.
