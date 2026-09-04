# 16 · Runbook multi-repo — locale → GitHub → GitLab cliente

**Owner**: Team Logistico 2.0   **Ultimo aggiornamento**: 2026-09-04
**Collegati**: [[ACT_9011]] (split), [[ACT_9017]] (script), [[ACT_9018]] (DAB), [[ACT_0.1.6]] (infra multi-repo), ADR-0016 (multi-repo), ADR-0005 (auth CI)

## Governance dei due host (modello di lavoro)
| Host | Repo | Contenuto | Ruolo |
|------|------|-----------|-------|
| **GitHub** (nostro/aziendale) | **4** (lib, workflows, infrastructure, **documentation**) | tutte le modifiche ed **evolutive** (WIP, branch, fix) | **source of truth di sviluppo** |
| **GitLab cliente** (`CNO/cno-data-platform/logistico`) | **3** (lib, workflows, infrastructure — **documentation MAI**) | solo **release testate, complete, stabili** | ambiente di **rilascio/deploy** |

Direzione **sempre mono-direzionale**: monorepo → GitHub → GitLab. Mai il contrario.
**Auth CI / segreti** (aggiornato 2026-08-27): mai `.env`/`terraform.tfvars`/token nei repo (già in `.gitignore`).
L'autenticazione della CI verso Azure/Databricks usa la **Managed Identity del group runner** — **nessun secret di
deploy** sui repo (niente `ARM_CLIENT_SECRET`, niente `DATABRICKS_TOKEN`). Terraform gira con `ARM_USE_MSI=true`; la
Databricks CLI usa la stessa MSI. Le uniche variabili CI sono **identificativi non sensibili**, impostati come
**protected** (attivi solo su `main` e tag `v*` → [[LL-016]]): `ARM_CLIENT_ID`/`ARM_TENANT_ID`/`ARM_SUBSCRIPTION_ID`
e `DATABRICKS_HOST`. Decisione formalizzata in [[ADR-0022]]. Vedi [[ACT_0.1.6]] e [[LL-018]] (authN ≠ authZ).
**Credenziali**: `push` e login (`gh`/GitLab PAT/SSH) verso gli host remoti restano **azione dell'utente**;
questo runbook fornisce i comandi esatti.

## Stato pubblicazione (aggiornato 2026-09-04)
**Sintesi:** **release 2026-09-04** dopo il run E2E DEV **7/7 job verdi** (ACT_9026/9027, canonico sito numerico
[[ADR-0026]], rimozione CND [[ACT_CND-01]]). Pubblicati GitHub (4 repo) + GitLab (lib `v1.0.5`, workflows `v0.1.6`;
CI cliente verdi). **Infra invariata** in questo giro (`v0.1.6`, non ripubblicata). Ciclo eseguito con
`split_to_multirepo.py` (GitHub) + `promote_to_gitlab.py` (GitLab, push ff, history cliente preservata).

| Repo | GitHub (SoT) | GitLab cliente | Note |
|------|:---:|:---:|------|
| `logistico-lib` | ✅ | ✅ `v1.0.5` | wheel `logistica_utils` nel Package Registry (CI verde). v1.0.5: `julian_to_date` ANSI-safe + `get_sito_alias_map` completa ([[ACT_9027]]/[[LL-025]]/[[LL-027]]). NB pacchetto a runtime resta 1.0.0 via %pip Volume ([[LL-013]]) |
| `logistico-infrastructure` | ✅ | ✅ `v0.1.6` | **invariato** in questo giro (0 file diff) → non ripubblicato. `apply` v0.1.6 verde (8 schemi + Volume + 6 grants, ACT_0.1.6 chiuso) |
| `logistico-workflows` | ✅ | ✅ `v0.1.6` | v0.1.6: canonico sito numerico ([[ADR-0026]]), fix ANSI serverless ([[ACT_9027]]), rimozione 7 notebook CND ([[ACT_CND-01]]). CI `main` verde → `bundle validate`; `deploy_prod` gate manuale |
| `logistico-documentation` | ✅ | ❌ (mai) | solo GitHub, per scelta |

Lezioni operative emerse durante la migrazione (per il team): [[LL-009]] una direzione sola · [[LL-010]] split
da file tracciati · [[LL-011]] runner tag · [[LL-012]] CA aziendale nel container · [[LL-013]] versione wheel
dal tag · [[LL-014]] entrypoint immagine CI · [[LL-015]] formato `resources:` dei file DAB · [[LL-016]] protected
var solo su ref protetti · [[LL-017]] `job.parameters` DAB da dichiarare · [[LL-018]] auth OK ≠ autorizzato ·
[[LL-019]] apply di un tfplan in CI: lock+provider e stato coerenti col plan.

---

## Fase 0 — (transizione) rigenerare i repo dal monorepo
Finché il monorepo è il SoT, i 4 repo locali si (ri)generano con lo script deterministico ([[ACT_9017]]):
```bash
# anteprima routing (nessuna scrittura)
python scripts/split_to_multirepo.py --dry-run --all
# generazione in ../logistico-repos/
python scripts/split_to_multirepo.py --all
```
Prerequisito: **working tree del monorepo pulito** (la proiezione riflette HEAD). Al **cutover** si congela
il monorepo e si smette di rigenerare.

> ⚠️ `logistico-workflows`: i due `databricks.yml` (root + `databricks_bundle/`) vengono **affiancati**;
> il consolidamento in un unico bundle è **manuale** (lo script lo segnala).

---

## Fase 1 — Setup iniziale: locale → GitHub (una tantum per repo)
Da eseguire per **tutti e 4** i repo (`logistico-lib`, `-workflows`, `-infrastructure`, `-documentation`).
Esempio con `logistico-lib`; ripetere sostituendo il nome.

**1a. Init pulito del repo locale** (ADR-0016: nessuna storia interna riportata):
```bash
cd C:/PROGETTI/logistico-repos/logistico-lib
git init -b main
git add -A
git commit -m "import da monorepo @<sha>"   # <sha> = quello stampato dallo script
```

**1b. Creare il repo vuoto su GitHub** (via web o `gh`):
```bash
# opzione gh CLI (richiede login gh):
gh repo create <github-org>/logistico-lib --private --source . --remote origin --push
```
oppure manuale:
```bash
git remote add origin https://github.com/<github-org>/logistico-lib.git
git push -u origin main
```
Ripetere per gli altri 3. **documentation va anch'esso su GitHub.**

---

## Fase 2 — Sviluppo su GitHub (ongoing)
- Tutte le modifiche/evolutive avvengono sui repo **GitHub** (branch + PR, merge su `main`).
- Durante la transizione, se una modifica nasce ancora nel **monorepo**, si rigenera con lo script (Fase 0)
  e si ricommitta sul repo → resta valido il flusso mono→multi. Al cutover questo passo sparisce.
- `logistico-workflows` dipende dal wheel di `logistico-lib`: vedi Fase 3/registry (DBR-05).

---

## Fase 3 — Promozione a GitLab cliente (solo release stabili, 3 repo)
Obiettivo: sul GitLab cliente arrivano **solo** stati testati/stabili, **senza** la storia di sviluppo, e
**mai** `documentation`. Due modelli possibili — **scegliere uno** (vedi nota decisione in fondo):

> ✅ **Modello scelto: A (snapshot di release)** — adottato e implementato in `scripts/promote_to_gitlab.py`
> ([[ACT_9017]]). Il modello B resta documentato solo come alternativa non adottata.

### Modello A — snapshot di release (SCELTO, allineato ad ADR-0016)
Il repo GitLab riceve **snapshot puliti** di release, non la history di GitHub. Coerente con l'"init pulito"
e con "solo release stabili".
1. Su GitHub, quando un repo è testato/stabile, si tagga la release: `git tag vX.Y.Z && git push origin vX.Y.Z`.
2. Si materializza lo snapshot testato nel working copy GitLab (stesso spirito dello split: copia dei file,
   nessuna history) e si committa come release:
   ```bash
   cd C:/PROGETTI/logistico-repos-gitlab/logistico-lib   # working copy dedicata al cliente
   git init -b main                                        # solo la prima volta
   # (rimpiazzare i file con lo snapshot testato di GitHub @<sha>)
   git add -A
   git commit -m "release vX.Y.Z (github @<sha>)"
   git tag vX.Y.Z
   git remote add gitlab https://<gitlab-host>/cno/cno-data-platform/logistico/logistico-lib.git  # 1a volta
   git push gitlab main --tags
   ```
3. La CI GitLab parte sul tag: **lib** pubblica il wheel nel Package Registry; **workflows** fa
   `bundle deploy` con **gate PROD manuale** (ACT_0.2.4); **infrastructure** fa `terraform plan`.

> ✅ **Implementato**: `scripts/promote_to_gitlab.py` (analogo a `split_to_multirepo.py`) materializza lo
> snapshot GitHub-stabile → working copy GitLab, senza history. Usato per la pubblicazione dei 3 repo (2026-08-27).

### Modello B — dual-remote con push dei tag (git standard)
Un solo repo con due remote (`origin`=GitHub, `gitlab`=cliente); si pushano a GitLab **solo i tag di release**:
```bash
git remote add gitlab https://<gitlab-host>/.../logistico-lib.git
git push gitlab vX.Y.Z
```
Semplice, ma **porta la history di sviluppo** su GitLab (contro l'"init pulito" di ADR-0016). Da usare solo se
si accetta storia condivisa tra i due host.

---

## Chi fa cosa
- **Io (assistant)**: rigenero i repo (script), preparo i comandi esatti, verifico routing/segreti, posso
  implementare `promote_to_gitlab.py` una volta scelto il modello.
- **Utente**: login `gh`/GitLab, creazione repo remoti, `push`, impostazione variabili CI/CD masked.

## Verifica (per ogni repo pushato)
- Clone pulito builda/valida (lib: wheel; workflows: `bundle validate`; infra: `plan`).
- `git log`/scan: nessun `.env`/tfvars/token nella storia.
- `documentation` **assente** sul GitLab cliente.

## Nota decisione (chiusa 2026-08-27)
Modello di promozione **deciso: A (snapshot di release)**, per coerenza con ADR-0016; implementato in
`scripts/promote_to_gitlab.py`. Il modello continuativo "GitHub=evolutive / GitLab=release stabili" **raffina**
l'ADR-0016 (che citava un seed one-shot al cutover) — recepito in ADR-0016.
