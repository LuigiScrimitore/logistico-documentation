# ACT_9018 · Consolidamento dei due `databricks.yml` in logistico-workflows

**Status**: in-progress (decisioni prese → [[ADR-0021]]; piano definito; esecuzione in attesa di validazione)
**Type**: infra / DAB   **Origin**: emerged (split multi-repo, [[ACT_9011]] / [[ACT_9017]])
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 0 — Fondamenta   **Gg (stima)**: 0,5–1
**Blocco**: 🟢 decisioni prese; resta un refactoring dei workflow (+ update test) da validare insieme
**Created**: 2026-08-22   **Closed**: —
**Dipende da**: [[ACT_9011]] (split), DBR-05 (wheel su Package Registry)   **Blocca**: CI di `logistico-workflows`
**ADR collegate**: [[ADR-0021]] (modello deploy per-area), ADR-0016 (multi-repo), ADR-0009 (serverless), ADR-0017 (rilascio a fasi)   **OP collegati**: DBR-05

## Contesto e motivazione
Nel monorepo esistono **due `databricks.yml`** che lo split porta entrambi in `logistico-workflows`. Non sono
due frammenti dello stesso bundle: sono **due bundle paralleli** con nomi diversi.

| | `databricks.yml` (root) | `infra/databricks_bundle/databricks.yml` |
|---|---|---|
| `bundle.name` | `logistica_20` | `logistico2-0` |
| Job inclusi | `include: workflows/*.yml` — **7 job reali per area** (DAG allineato ai notebook, [[ACT_9014]]) | `include: resources/*.job.yml` — **wave KIT-06** (solo `logistica_wave_a`, "TEMPLATE di riferimento") |
| Variabili | complete (env, landing_base_path, retail_master_schema, email_alert; default D2/D3) | minime (env, notifications_email) |
| Cost tag | — | `presets.tags` (business_unit/project/env/managed_by — KIT-05) |
| Wheel | `artifacts` → **build da `lib/`** | — |
| Path | relativi al repo | `sync: ../../notebooks`, `../../lib` (rotti nel layout multi-repo) |
| Host | `${DATABRICKS_HOST}` (CI-friendly) | `https://<WORKSPACE_*_URL>` (placeholder) |

## Le decisioni — PRESE (2026-08-22)
1. **Modello di deploy = pipeline per-area** (`workflows/*.yml`), wave KIT-06 archiviata → **[[ADR-0021]]**.
2. **Wheel dal Package Registry, pinnato** `logistica_utils==1.0.4` (DBR-05); rimosso il blocco `artifacts`
   build-da-`lib/`.
3. **Path** sistemati per il layout `logistico-workflows` (via `-chdir`/path relativi coerenti; niente `../../`).
4. **Merge**: base = root `databricks.yml` (variabili complete + host `${DATABRICKS_HOST}` + targets dev/prod)
   **+** `presets.tags` (cost tag) dallo scheletro; **un solo** `bundle.name` = **`logistico`**.

## Piano di consolidamento (nel monorepo → poi rigenerazione)
1. **`databricks.yml` unico** (sostituisce il root): `bundle.name: logistico`; `variables` invariate;
   `workspace.host: ${DATABRICKS_HOST}`; `targets.dev/prod` con l'aggiunta di `presets.tags`
   (business_unit/project/env/managed_by); **rimosso** `artifacts`; `include: resources/*.yml`.
2. **Convertire i 7 `workflows/*.yml` → formato DAB**: wrappare ciascuno in `resources: jobs: <name>: {…}`
   (contenuto job invariato) e spostarli sotto `resources/`. Sistemare `notebook_path` (`../notebooks/…` →
   coerente col bundle root) e la **dipendenza wheel**: `environments…dependencies` da
   `../lib/dist/logistica_utils-*.whl` → `logistica_utils==1.0.4` (dal Package Registry).
3. **Aggiornare `tests/test_workflows_alignment.py`**: `_load`/`_tasks` devono leggere `resources.jobs.<key>.tasks`
   invece del top-level `tasks` (i 30 guardrail devono restare verdi sul nuovo formato).
4. **Rimuovere/archiviare**: `infra/databricks_bundle/databricks.yml` (duplicato) e
   `resources/logistica_wave_a.job.yml` (scheletro wave — [[ADR-0021]]).
5. **Aggiornare la mappatura split** ([[ACT_9017]]): sparisce il secondo `databricks.yml` → niente più warning
   sul consolidamento; i job wrappati vanno in `logistico-workflows/resources/`.
6. **Validazione locale**: `test_workflows_alignment` verde sul nuovo formato + YAML valido. La `databricks
   bundle validate` completa richiede la CLI + `DATABRICKS_*` → si verifica in CI su GitLab (al gate).

**Punto che richiede validazione cloud (DBR-05)**: come il compute **serverless** installa il wheel dal
**Package Registry privato** (index-url/pip.conf nell'`environment`). Localmente pinniamo `==1.0.4`; il
meccanismo d'indice va confermato sul workspace Databricks. È l'unico pezzo non verificabile in locale.

## Dove si esegue
Il consolidamento va fatto nel **monorepo** (SoT in transizione), poi rigenerato in `logistico-workflows` con
`split_to_multirepo.py` (con `--only logistico-workflows`).

## Esito
- Decisioni prese ([[ADR-0021]]); piano definito ed **eseguito** (2026-08-22):
  - `databricks.yml` unico consolidato (`bundle.name: logistico`, `presets.tags`, niente `artifacts`,
    `include: workflows/*.yml`).
  - 7 `workflows/*.yml` wrappati in `resources: jobs: <key>:`; wheel → `logistica_utils==1.0.4` (registry).
  - `tests/test_workflows_alignment.py` legge `resources.jobs.<key>`; **suite 111/111 verde** (30 guardrail
    workflow inclusi).
  - Rimossi `infra/databricks_bundle/databricks.yml` (duplicato) e lo scheletro wave; regola split ripulita.
- **2026-08-27 — workflows DEPLOYATO in DEV via GitLab CI** 🎯: `logistico-workflows` promosso su GitLab;
  pipeline `main` **verde** (`validate` + `deploy_dev`) → i **7 job creati** nel workspace DEV (auth MSI). Con
  `mode: development` sono un sandbox sotto la MI, **schedule in pausa**. Bring-up chiuso lato deploy.
  Iterazioni superate (tutte fixate nel generatore + guardrail dove utile): yaml `variables` sotto `default`
  ([[LL-016]]/tag), `workspace.host` interpolato, notebook_path `.py` ([[LL-015]]), `root_path` per-utente in
  `mode:development`, `job.parameters` non dichiarati ([[LL-017]], + nuovo guardrail, suite 37).
- **Cloud-gated residuo**: il **wheel dal Package Registry** (DBR-05) serve al **run** di un job (non al
  deploy) — meccanismo d'indice pip sul serverless da confermare eseguendo una pipeline in DEV.

## Follow-up
- Eseguito il consolidamento: rigenerare `logistico-workflows`, poi promuovere su GitLab (`bundle validate`).
- Confermare a DBR-05 il meccanismo d'indice del Package Registry per il wheel sul serverless.
