# ACT_0.1.6 · Consegna Terraform `brownfield/` in multi-repo GitLab

**Status**: in-progress (credenziali DEV ricevute 2026-08-27 — Managed Identity; da impostare variabili CI + Retry `plan`)
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 1   **Blocco**: 🏗️ **`ARM_*` (service principal Azure, utenza A7)** per `init/plan` — subgroup, repo e runner ora **disponibili**
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
- Repo su GitHub (SoT) pronto; **promosso su GitLab** (`logistico-infrastructure`, snapshot `v0.1.2`); runner ok.
- Pipeline non distruttiva (`validate` ✅ / `plan` bloccato all'auth backend). CI provato corretto fino
  all'autenticazione.
- **2026-08-27 — credenziali ricevute (Managed Identity)**: adeguati codice e CI (`ARM_USE_MSI=true`,
  `azure_use_msi` sul provider databricks, `databricks_host` DEV via CI var). Restano **azioni utente**:
  impostare le 4 variabili CI (vedi sezione Autenticazione) e fare **Retry** del job `plan` — poi si legge il
  primo `plan` reale in DEV (sola lettura).

## Follow-up
- Promuovere `logistico-infrastructure` sul GitLab cliente (snapshot via `promote_to_gitlab.py`).
- Ottenere/impostare le **`ARM_*` DEV** (service principal) come variabili CI masked/protected → far girare `plan`.
- Review MR con Ippazio (Reply); poi `apply` DEV → [[ACT_8.1.2]] per PROD.
