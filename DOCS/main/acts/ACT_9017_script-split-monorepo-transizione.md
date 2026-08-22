# ACT_9017 · Script di split monorepo → multi-repo (tooling di transizione)

**Status**: in-progress (script pronto e validato; usato per seedare i repo fino al cutover)
**Type**: infra / tooling   **Origin**: emerged (domanda utente durante ACT_9011)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 0 — Fondamenta   **Gg (stima)**: 0,5
**Blocco**: 🟢 (solo-locale)
**Created**: 2026-08-22   **Closed**: —
**Dipende da**: [[ACT_9011]] (mappatura 4 repo), ADR-0016   **Blocca**: —
**ADR collegate**: ADR-0016 (multi-repo, init pulito), ADR-0005 (secret CI/CD)   **OP collegati**: —

## Contesto e motivazione
[[ACT_9011]] definisce lo split del monorepo in 4 repo (ADR-0016) con una **tabella di mappatura in
prosa**. Durante la preparazione è emersa la domanda: serve una procedura ripetibile per portare le
modifiche dal monorepo ai 4 repo **durante la finestra di switch del team**, o si lavora subito sui 4?

**Decisione**: costruire uno script di **proiezione deterministico e mono-direzionale**
(`scripts/split_to_multirepo.py`). Non è un sync permanente: è tooling di transizione.

## Decisioni di design
- **Mono-direzionale, sempre**: monorepo → multi-repo, **mai** il contrario. Evita il doppio
  source-of-truth (trappola classica delle migrazioni multi-repo). Durante la transizione il SoT
  resta il **monorepo**; si rigenerano i 4 repo da qui.
- **Proiezione, non `git subtree split`**: ADR-0016 ha scelto **init pulito senza storia interna** —
  il pregio di subtree (portarsi la history) qui *non* si vuole. Inoltre la mappatura non è
  "una cartella per repo" (`lib/setup.py`+`lib/logistica_utils/` → **root** di lib; due
  `databricks.yml` da consolidare): serve un copy-mapping con trasformazioni di layout, che subtree
  non fa. Ogni rigenerazione è seguita da un commit `import da monorepo @<sha>` (provenienza).
- **Sorgente = `git ls-files`**: si iterano solo i file **tracciati**, così `.env`, `warehouse/`,
  dati reali e `__pycache__` sono esclusi *gratis* dal `.gitignore`. Nessun file mappato in silenzio:
  i non mappati vengono **segnalati** (regola mancante o da aggiungere a SKIP).
- **Time-boxed, con ritiro al cutover**: quando il team è pronto (`git remote` + push sui 4 repo),
  si **congela** il monorepo e si **smette** di rigenerare; da lì il SoT sono i 4 repo. Lo script va
  poi ritirato (finirà comunque in `logistico-documentation`, mai sul GitLab cliente).

## Cosa fa lo script
- `--dry-run --all`: anteprima del routing (conteggi per repo + elenco non mappati). Nessuna scrittura.
- `--only <repo>` / `--all`: genera lo staging in `../logistico-repos/<repo>` (default `--out`),
  **svuotando** prima l'albero di lavoro (tranne `.git`) così le rimozioni si propagano.
- Genera i file per-repo: `.gitignore`, `README.md` (tranne documentation, che usa quello del
  monorepo), `.gitlab-ci.yml` (lib: build+publish wheel; workflows: bundle validate/deploy + gate PROD
  manuale; infrastructure: terraform validate/plan — con TODO dove pinnare versioni/CLI).
- Guard: se il working tree del monorepo non è pulito, in modalità scrittura si ferma (la proiezione
  riflette **HEAD**: le modifiche non committate non verrebbero proiettate).

## Verifica
Dry-run 2026-08-22 @96b115e: **584 file, 0 non mappati** — lib 11, workflows 129, infrastructure 15,
documentation 429 (= 586 tracciati − 2 SKIP: `.gitlab-ci.yml`/`.gitignore` del monorepo). Avviso
corretto sul consolidamento manuale dei due `databricks.yml` in workflows.

## Esito
- Script pronto e validato (dry-run 584 file, 0 non mappati).
- `logistico-lib` generato in `C:\PROGETTI\logistico-repos\logistico-lib` (11 file + `.gitignore`/
  `README`/`.gitlab-ci.yml`). **Wheel buildato e validato** con `python -m build --wheel` (host
  Python 3.13, build isolation): `logistica_utils-1.0.0-py3-none-any.whl` (38 KB), metadati corretti
  (`Requires-Dist: pyspark>=3.5, delta-spark>=3.0`), 10 moduli inclusi. È lo stesso comando del
  `.gitlab-ci.yml` generato → catena CI verso il Package Registry confermata (verso [[ACT_9011]] step 4
  e DBR-05). Il `git init`/commit `import @<sha>` e il push su GitHub/GitLab restano azione utente.

## Tooling collegato — `promote_to_gitlab.py` (modello A)
Secondo script di transizione, **mono-direzionale** GitHub → GitLab cliente: snapshotta lo stato
**testato/stabile** di un repo (source git, tag checkoutato) nel working copy GitLab, committa
`release vX.Y.Z (github @<sha>)` e crea il tag. Guardrail: **rifiuta `logistico-documentation`**, valida
il formato versione, esige source pulito, ed è **idempotente** (nessuna diff → "niente da promuovere").
Validato in locale 2026-08-22 (lib v1.0.0: commit+tag OK; documentation rifiutato). Procedura d'uso:
`16_runbook_multirepo_github_gitlab.md` (Fase 3, modello A confermato con ADR-0016 §aggiornamento 2026-08-22).

## Pilot completato — `logistico-lib` sul GitLab cliente (2026-08-22)
Giro end-to-end **dimostrato sul GitLab cliente reale** (`cp1lgitlab...Logistico/logistico-lib`):
`promote_to_gitlab.py` → push → **CI verde** → wheel nel **Package Registry** (`logistica_utils 1.0.4`).
Due ostacoli d'ambiente superati (entrambi promossi a lezione):
- **pipeline `stuck`** con group runner attivo → mancava il tag: aggiunto `tags: [azure-runner]` nel
  `default:` dei `.gitlab-ci.yml` generati → [[LL-011]].
- **`publish` in `CERTIFICATE_VERIFY_FAILED`** verso il GitLab (CA aziendale sconosciuta al container) →
  `before_script` che aggiunge la CA (`CI_SERVER_TLS_CA_FILE`) al trust store → [[LL-012]].
- **versione wheel disallineata** (tag `v1.0.2` ma pacchetto `1.0.0` da `setup.py`) → il `build` allinea la
  versione al tag (`CI_COMMIT_TAG`) → [[LL-013]]. Versione finale pubblicata: **`1.0.4`**.
Il fix dei tre è nel **generatore** (`split_to_multirepo.py`), quindi vale per tutti e 4 i repo.

## Follow-up
- Consolidamento dei due `databricks.yml` in `logistico-workflows` (oggi affiancati + warning).
- Al cutover: freeze monorepo, stop rigenerazione, ritiro degli script di transizione.
