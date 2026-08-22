# ACT_0.1.6 · Consegna Terraform `brownfield/` in multi-repo GitLab

**Status**: in-progress
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 1   **Blocco**: 🏗️ utenza Azure A7 (per `init/plan/apply`) — subgroup GitLab ora **disponibile**
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

## Sviluppo (diario)
- 2026-07-03 · backend DEV compilato; codice pronto; MR pendente su creazione subgroup.
- 2026-08-03 · **subgroup GitLab disponibile** (`CNO/cno-data-platform/logistico`, Maintainer). Lo split del
  monorepo → repo `logistico-infrastructure` è ora tracciato in [[ACT_9011]]. Resta il blocco A7 (utenza Azure)
  per `init/plan/apply`.

## Verifica
`terraform init` aggancia lo state su `stdevdataplatformweu00/statefile`; `terraform plan` verde in DEV;
MR approvata da Ippazio (Reply).

## Esito
— (in attesa subgroup GitLab)

## Follow-up
Azione operativa: mail Extrared per subgroup → creare i 3 repo → `init/plan` → review Ippazio → apply.
