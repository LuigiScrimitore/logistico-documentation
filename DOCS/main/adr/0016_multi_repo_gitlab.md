# ADR-0016 · Codice su GitLab in **multi-repo** (infrastructure / workflows / lib)

**Status**: accepted (2026-07)

**Contesto**:
Il codice del progetto (Terraform, notebook + Databricks Asset Bundle, libreria condivisa
`logistica_utils`) deve essere versionato sul **GitLab aziendale**, sotto il macro-gruppo Data Platform.
Serve decidere la topologia dei repository: un unico mono-repo o più repo dedicati. La scelta impatta
permessi, CI/CD, cicli di rilascio indipendenti e riuso della libreria.

**Alternative considerate**:
1. **Mono-repo** (tutto in un repo) — semplice da clonare, ma mescola cicli di vita molto diversi
   (infra vs workflow vs libreria), CI/CD unica e più difficile dare permessi granulari; la libreria non
   è riusabile pulita come dipendenza.
2. **Multi-repo** sotto un **subgroup `logistico`**, con repo dedicati per infrastruttura / workflow / libreria.
   Cicli e CI/CD indipendenti; la lib è una dipendenza versionata.

**Decisione**:
**Multi-repo**: subgroup `CNO/cno-data-platform/logistico`, visibilità Internal, ruolo **Maintainer** al team.
I secret di deploy (`ARM_*`, `DATABRICKS_TOKEN`) sono variabili CI/CD mascherate a livello progetto
(coerente con ADR-0005: nessun segreto Oracle).

**Aggiornamento 2026-08-03 — 4 repo (accesso concesso)**: subgroup creato e Maintainer confermato. La
topologia definitiva è a **4 repo**. **GitHub (nostro) = source of truth**, ospita **tutti e 4**; il
**GitLab cliente ospita 3** (codice, documentation escluso). Sync **una via GitHub → GitLab**.
| Repo | GitHub (nostro, SoT) | GitLab cliente | Contenuto |
|------|:---:|:---:|-----------|
| `logistico-infrastructure` | ✅ | ✅ | Terraform brownfield (`infra/`) |
| `logistico-workflows` | ✅ | ✅ | notebook, `workflows/*.yml` (DAB), `sql/`, `databricks.yml`, script runtime |
| `logistico-lib` | ✅ | ✅ | `logistica_utils` → **wheel** |
| `logistico-documentation` | ✅ | ❌ (mai) | `DOCS/` + tooling dev (docker, simulator, script one-off) |

Scelte di esecuzione (2026-08-03):
- **Source of truth = GitHub (nostro)**: i 4 repo nascono qui (sostituiscono il monorepo, che diventa
  **archivio**). **Init pulito anche per i 4 repo GitHub** (commit iniziale "import da monorepo @<sha>",
  nessuna storia interna riportata) — deciso 2026-08-03.
- **GitLab cliente = 3 repo** (infrastructure/workflows/lib), seedati **da GitHub** con **init pulito**
  (commit "import @<sha>"). Sync **una via GitHub → GitLab**. ⇒ **init pulito uniforme su tutti i repo**.
- `logistico-documentation` = **repo nuovo dedicato** solo-doc, **solo su GitHub** (mai sul GitLab cliente).
- Dipendenza `workflows → lib`: il wheel di `logistico-lib` è pubblicato nel **GitLab Package Registry** del
  progetto e installato dal DAB di `logistico-workflows` (DBR-05). La **pipeline di deploy** verso il
  Databricks cliente gira sul **GitLab cliente**; i 3 repo restano **autosufficienti dentro GitLab** (nessun
  riferimento al nostro GitHub in build/run). **La documentazione NON esce dal nostro perimetro** (requisito).

**Aggiornamento 2026-08-22 — governance due host + promozione release (modello A)**:
Confermato il modello operativo dei due host (raffina il "seed one-shot al cutover" citato sopra in un
**flusso continuativo**):
- **GitHub (`LuigiScrimitore/*`) = SoT di sviluppo**, 4 repo (`logistico-lib`, `-workflows`,
  `-infrastructure`, `-documentation`): tutte le modifiche ed **evolutive** (branch, fix, WIP). Il monorepo
  `LuigiScrimitore/Logistico2.0` resta **archivio**.
- **GitLab cliente = rilascio**, 3 repo (documentation **mai**): riceve **solo release testate/stabili**.
- **Promozione = modello A (snapshot di release)**: il repo GitLab riceve **snapshot puliti** taggati
  `vX.Y.Z` (nessuna storia di sviluppo), coerente con l'init pulito. Scartato il modello B (dual-remote con
  push della history). Direzione **sempre** monorepo → GitHub → GitLab; mai inversa.
- Procedura operativa: `16_runbook_multirepo_github_gitlab.md`; automazione promozione:
  `scripts/promote_to_gitlab.py` ([[ACT_9017]]).
- **Validato (2026-08-22)**: 4 repo su GitHub; **pilot `logistico-lib` completato sul GitLab cliente** —
  promote → CI verde → wheel `logistica_utils 1.0.4` nel Package Registry. Lezioni operative emerse:
  [[LL-011]] (tag runner), [[LL-012]] (CA aziendale nel container), [[LL-013]] (versione dal tag). Restano
  `workflows` (dopo consolidamento `databricks.yml`, [[ACT_9018]]) e `infrastructure`.

**Conseguenze**:
+ Cicli di rilascio indipendenti (infra ≠ workflow ≠ lib); permessi e CI/CD per repo; lib riusabile via registry.
+ Abilita il rilascio a fasi (ADR-0017): si deploya un pezzo alla volta.
+ La documentazione resta privata (fuori dal GitLab cliente) pur essendo versionata.
− Coordinamento versioni lib↔workflows (mitigato dal Package Registry + pinning versione).
− Init pulito = si perde la granularità di storia sui repo cliente (accettato: l'handoff parte pulito).

**Riferimenti**:
- Esecuzione split → [[ACT_9011]] (runbook monorepo → 4 repo); consegna infra → [[ACT_0.1.6]].
- Sezione repo/CI-CD: `11_devops_handoff_databricks.md` e `12_checklist_infra_setup.md` §B (GitLab & CI/CD).
- Backlog I-07 (subgroup+repo), I-08 (secret CI/CD), I-09 (runner), DBR-05 (wheel). DAB: `infra/databricks_bundle/`.
- Collegate: ADR-0005 (no segreti/auth CI-CD), ADR-0017 (rilascio a fasi).
