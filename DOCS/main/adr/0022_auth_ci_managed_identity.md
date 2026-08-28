# ADR-0022 · Autenticazione CI/CD verso Azure/Databricks via Managed Identity (no secret)

**Status**: accepted (2026-08-27)

**Contesto**:
Con lo split multi-repo ([[ADR-0016]]), i 3 repo su GitLab (`logistico-infrastructure`, `-workflows`,
`-lib`) devono autenticarsi in CI verso **Azure** (Terraform sul provider/backend `azurerm`) e verso
**Databricks** (deploy del DAB, pubblicazione del wheel). Il piano/handoff iniziale
(`10_piano_migrazione_databricks.md`, `11_devops_handoff_databricks.md`, `12_checklist_infra_setup.md` §B3,
in coerenza con [[ADR-0005]]) prevedeva **secret di deploy** come variabili CI/CD masked:
`ARM_CLIENT_ID/SECRET/TENANT_ID/SUBSCRIPTION_ID` + `DATABRICKS_HOST/TOKEN`. Il meccanismo concreto
("certificate vs secret manager") era **in definizione con Technology** → blocco ricorrente (0-4 nel doc 11,
ping mensile). Il **group runner** del subgroup GitLab gira su infrastruttura Azure aziendale e può avere una
**Managed Identity** assegnata; Technology preferisce non distribuire client secret / PAT di lunga durata.

**Alternative considerate**:
1. **Secret di deploy come masked/protected CI variables** (client secret ARM + Databricks PAT):
   funziona ovunque, ma introduce **segreti di lunga durata** da custodire e ruotare, dipende dal meccanismo
   "certificate vs secret manager" ancora aperto lato Technology, e amplia la superficie di rischio (token
   nelle variabili CI).
2. **Managed Identity del group runner** (identità assegnata all'host del runner): **nessun segreto** da
   custodire/ruotare. Terraform con `ARM_USE_MSI=true`; provider/CLI Databricks via la stessa MSI
   (`azure_use_msi=true`). Le uniche variabili CI restano **identificativi non sensibili** (client_id/tenant/
   subscription, host).
3. **Service Principal dedicato con secret in Key Vault**: allineato a un eventuale SP unico data-platform
   ([[OP-18]]), ma dipende da Technology e **reintroduce un segreto** da gestire.

**Decisione**:
**Opzione 2 — auth via Managed Identity del group runner**, **nessun secret di deploy** sui repo.
- **Terraform**: `ARM_USE_MSI=true` (provider `azurerm` + backend `azurerm`).
- **Databricks**: provider/CLI via MSI (`azure_use_msi=true`).
- **Variabili CI** = solo identificativi non sensibili, impostati come **protected** (attivi solo su ref
  protetti — `main` + tag `v*`, [[LL-016]]): `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`,
  `DATABRICKS_HOST`.
- I job **runtime** restano coerenti con [[ADR-0005]] (nessun secret Oracle; ingestion in push).

**Conseguenze**:
+ Nessun secret di deploy da custodire/ruotare → **superficie di rischio ridotta**; sblocca il punto
  "meccanismo secret" (0-4 nel doc 11) **senza attendere Technology**.
+ Auth **uniforme** per i 3 repo; niente PAT Databricks di lunga durata.
+ **Validato in DEV (2026-08-27)**: infra `terraform plan` verde (15 add, 0 destroy); workflows `deploy_dev`
  verde (7 job); lib wheel `v1.0.4` pubblicato nel Package Registry.
− **authN ≠ authZ** ([[LL-018]]): la MI **autentica** ma serve comunque l'**autorizzazione** Unity Catalog.
  L'`apply` infra DEV è bloccato finché la MI non ha `USE CATALOG` + `CREATE SCHEMA` sui 5 catalog → [[OP-INF-1]].
− Le variabili CI sono **protette**: le pipeline su ref non protetti non le vedono ([[LL-016]]) → gestire di
  conseguenza i feature branch.
− **Dipendenza dalla MI del runner**: se il runner cambia host/identità, vanno riassegnate la MI e i relativi
  grant Azure/UC.
− **PROD**: stesso modello via gate manuale sui tag `v*` (`deploy_prod`), con MI + grant dell'ambiente PROD
  da predisporre al provisioning.

**Relazione con [[ADR-0005]]**: ADR-0005 riguarda l'assenza di segreti **Oracle** (ingestion in push). Questa
ADR **estende** il principio "no secret" all'**auth CI di deploy** (Azure/Databricks) via Managed Identity, e
supera nei doc la parte che citava i secret di deploy come masked var (aggiornati: `03_linee_guida.md` Gap #5,
`10_piano_migrazione_databricks.md` §7, `11_devops_handoff_databricks.md` §0-4/FASE C, `12_checklist_infra_setup.md`
§B3, `16_runbook_multirepo_github_gitlab.md` §Auth).

**Riferimenti**: [[ACT_0.1.6]] (infra multi-repo — plan verde/apply bloccato) · [[ACT_9018]] (workflows
`deploy_dev` in DEV) · [[LL-016]] (protected var su ref protetti) · [[LL-018]] (authN ≠ authZ) · [[OP-INF-1]]
(grant `CREATE SCHEMA` alla MI) · [[ADR-0016]] (multi-repo) · [[ADR-0005]] (no secret Oracle) ·
`16_runbook_multirepo_github_gitlab.md` (runbook operativo).
