# ACT_9011 · Split monorepo → 4 repo GitLab (+ Package Registry)

**Status**: in-progress (pilot lib completato; workflows/infra + cutover pendenti)
**Type**: infra
**Origin**: emerged (accesso subgroup GitLab concesso 2026-08-03)   **Sprint**: fuori-sprint (emergente)
**Fase / Wave**: FASE 0 — Fondamenta   **Gg (stima)**: 2
**Blocco**: 🏗️ creazione repo + push sul GitLab cliente (azione utente); parte locale eseguibile subito
**Created**: 2026-08-03   **Closed**: —
**Dipende da**: subgroup `CNO/cno-data-platform/logistico` (✅)   **Blocca**: [[ACT_0.1.6]] (consegna infra), pipeline CI/CD per repo, DBR-05 (wheel)
**ADR collegate**: ADR-0016 (multi-repo, 4 repo), ADR-0005 (secret CI/CD), ADR-0017 (rilascio a fasi)   **OP collegati**: I-07, I-08, I-09, DBR-05

## Contesto e motivazione
Il codice vive oggi in un **monorepo** (GitHub `LuigiScrimitore/Logistico2.0`). Con l'accesso al subgroup
`CNO/cno-data-platform/logistico` (Maintainer, 2026-08-03) si esegue lo split in **4 repo** (ADR-0016).
**Topologia**: **GitHub (nostro) = source of truth con tutti e 4 i repo**; il **GitLab cliente ospita 3**
(infrastructure/workflows/lib, **documentation escluso**); sync **una via GitHub → GitLab**. Il monorepo
GitHub attuale viene sostituito dai 4 repo → diventa **archivio**.

## Obiettivo
4 repo GitHub (SoT) popolati e funzionanti; 3 di essi (`-infrastructure`/`-workflows`/`-lib`) seedati sul
GitLab cliente con CI/CD e wheel via Package Registry; `logistico-documentation` **solo su GitHub**. Nessun
segreto/dato reale committato.

## Analisi tecnica — mappatura monorepo → repo
| Sorgente (monorepo) | Repo destinazione | GitHub (SoT) / GitLab cliente | Note |
|---------------------|-------------------|-------------------------------|------|
| `infra/` (Terraform brownfield) | **logistico-infrastructure** | GitHub ✅ · GitLab ✅ | escluso `infra/databricks_bundle/` → va in workflows |
| `notebooks/`, `workflows/*.yml`, `sql/`, `databricks.yml`, `infra/databricks_bundle/databricks.yml`, `scripts/{cdtdw_lookup_extractor,quadratura,sftp}` | **logistico-workflows** | GitHub ✅ · GitLab ✅ | consolidare i due `databricks.yml`; dipende dal wheel di lib |
| `lib/logistica_utils` + `lib/setup.py` | **logistico-lib** | GitHub ✅ · GitLab ✅ | build wheel → Package Registry |
| `DOCS/`, `docker/`, `scripts/{landing_simulator,migration}`, script one-off root (`add_*.py`, `build_*.py/js`, `update_*.py`, `write_readme.py`), `tests/` di dev | **logistico-documentation** | GitHub ✅ · GitLab ❌ (mai) | resta solo su GitHub |

**Decisioni (2026-08-03, ADR-0016)**: (a) **GitHub = source of truth** con i 4 repo (sostituiscono il
monorepo → archivio); **init pulito anche per i 4 repo GitHub** (`import @<sha>`, nessuna storia interna).
(b) i **3 repo cliente** su GitLab sono seedati **da GitHub**, anch'essi con **init pulito**, sync **una via
GitHub → GitLab** ⇒ **init pulito uniforme su tutti**. (c) `logistico-documentation` = **repo nuovo, solo
GitHub**. (d) wheel via **GitLab Package Registry**; la pipeline di deploy verso Databricks cliente gira sul
**GitLab cliente**.

**Dipendenza `workflows → lib`**: `logistico-lib` CI builda il wheel e lo pubblica nel Package Registry
(PyPI-style) del progetto; `logistico-workflows` lo installa nel DAB (`databricks.yml` →
`libraries: - whl:` da registry, versione **pinnata**). = attività DBR-05.

**Secret CI/CD** (ADR-0005): solo `ARM_CLIENT_ID/SECRET/TENANT_ID/SUBSCRIPTION_ID` (infrastructure) e
`DATABRICKS_HOST/TOKEN` (workflows), come variabili masked per-repo. **Mai** `.env`/`terraform.tfvars`/token
nei repo (già in `.gitignore`).

## Runbook (parte LOCALE eseguibile ora / parte CLIENTE = utente)

> **Automazione (2026-08-22)**: la parte locale (step 1–3) è realizzata da uno **script di
> proiezione deterministico**, `scripts/split_to_multirepo.py` — vedi [[ACT_9017]]. È
> **mono-direzionale** (monorepo → multi-repo, mai il contrario) ed è la forma eseguibile
> della tabella di mappatura qui sopra. Itera su `git ls-files` (solo tracciati: `.env`,
> `warehouse/`, dati e `__pycache__` esclusi dal `.gitignore`), instrada ogni file al repo
> giusto e **segnala** i non mappati. Genera anche `.gitlab-ci.yml`/`README`/`.gitignore`
> per-repo. Dry-run 2026-08-22 @96b115e: **584 file, 0 non mappati** (lib 11, workflows 129,
> infrastructure 15, documentation 429). Destinazione: `C:\PROGETTI\logistico-repos\`.

**Locale (preparazione — nessun accesso cliente):**
1. `python scripts/split_to_multirepo.py --dry-run --all` per validare il routing, poi
   `--only <repo>` / `--all` per generare le cartelle di staging. Consolidamento dei due
   `databricks.yml` (workflows) **ancora manuale**: lo script li affianca e lo segnala.
2. `.gitlab-ci.yml` per-repo: generati dallo script — infrastructure (`terraform validate/plan`),
   workflows (`bundle validate/deploy`, gate PROD manuale), lib (`build`+`publish` wheel al
   Package Registry). Gli skeleton hanno TODO dove serve pinnare versioni/CLI.
3. `README.md` + `.gitignore` per-repo: generati dallo script (secret/dati esclusi).
4. `logistica_utils`: confermare `setup.py`/versione per il wheel (v1.0.0).

**GitHub (nostro — SoT, source di tutti e 4):**
5. Creare i 4 repo su GitHub e seedarli dal monorepo (storia preservabile con subtree split, o clean-init).
   `logistico-documentation` **resta solo qui**.

**GitLab cliente (esecuzione — utente, richiede push sul GitLab cliente):**
6. Creare i 3 progetti nel subgroup; seed **da GitHub** con **init pulito** (commit `import @<sha>`);
   `git remote add` + push (solo i 3, mai documentation).
7. Impostare le variabili CI/CD masked per-repo (ARM_* / DATABRICKS_*).
8. Pubblicare il wheel di lib nel Package Registry; agganciare workflows al registry (deploy da GitLab).
9. Definire il sync **una via GitHub → GitLab** per i 3 repo (seed one-shot al cutover; niente mirror
   continuo verso il cliente durante il freeze).

## Verifica
- I 3 repo cliente clonano e le pipeline partono (plan infra verde; `bundle validate` workflows; wheel
  pubblicato). Nessun file sensibile nei repo (`git log`/scan). Documentation non presente sul GitLab cliente.

## Esito
- **Parte locale automatizzata** via `scripts/split_to_multirepo.py` ([[ACT_9017]]): 4 repo generati in
  `C:\PROGETTI\logistico-repos\`, 584 file, 0 non mappati.
- **GitHub**: i 4 repo (`LuigiScrimitore/logistico-{lib,workflows,infrastructure,documentation}`) creati e
  pushati (init pulito `import @<sha>`). Il monorepo `Logistico2.0` resta archivio.
- **GitLab cliente — pilot `logistico-lib` completato** (2026-08-22): project creato nel subgroup
  `Logistico`, snapshot `v1.0.4` promosso (modello A), **CI verde**, wheel nel **Package Registry**
  (`logistica_utils 1.0.4`). Superati due ostacoli d'ambiente → [[LL-011]] (runner tag) e [[LL-012]] (CA).
- **Restano**: promuovere `workflows` e `infrastructure` (dopo il consolidamento `databricks.yml`,
  [[ACT_9018]]); variabili CI/CD masked (ARM_*/DATABRICKS_*); sync/cutover.

## Follow-up
Sblocca [[ACT_0.1.6]] (repo infrastructure pronto) e i gate cloud. Allineare compute serverless nei YML
([[ACT_9007]]) prima del deploy.
