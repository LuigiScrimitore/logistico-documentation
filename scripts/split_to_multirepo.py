#!/usr/bin/env python3
"""
split_to_multirepo.py — Proietta il monorepo nei 4 repo del multi-repo (ADR-0016).

STRUMENTO DI TRANSIZIONE, MONO-DIREZIONALE: monorepo → multi-repo, MAI il contrario.

Durante la finestra di switch del team il **source of truth resta il monorepo**: si
rigenerano i 4 repo da qui con questo script. Al **cutover** (team pronto a lavorare
sui 4 repo) si **congela** il monorepo e si **smette** di rigenerare: da quel momento il
SoT diventano i 4 repo (GitHub, poi i 3 sul GitLab cliente). NON esiste sync inverso.

Come funziona
-------------
- Itera su ``git ls-files`` (solo file TRACCIATI): ``.env``, ``warehouse/``, ``data/``,
  ``__pycache__`` ecc. sono esclusi *gratis* dal ``.gitignore``.
- Ogni file è instradato al repo di destinazione secondo RULES (match per prefisso più
  lungo). Un file non mappato viene **segnalato** (mai perso in silenzio).
- Per il repo selezionato: si **svuota** l'albero di lavoro (tranne ``.git`` e i file
  generati) e si ricopiano i file mappati → la proiezione riflette esattamente lo stato
  corrente del monorepo (le rimozioni si propagano).
- Si (ri)generano i file per-repo: ``README.md`` (dove serve), ``.gitignore``,
  ``.gitlab-ci.yml``.
- Provenienza: viene stampato lo SHA sorgente e il messaggio di commit suggerito
  ``import da monorepo @<sha>`` (ADR-0016, init pulito).

Uso
---
    python scripts/split_to_multirepo.py --dry-run --all        # anteprima routing
    python scripts/split_to_multirepo.py --only logistico-lib   # genera solo lib
    python scripts/split_to_multirepo.py --all                  # genera tutti e 4
    python scripts/split_to_multirepo.py --only logistico-lib --out /c/PROGETTI/logistico-repos

Default ``--out``: ``../logistico-repos`` rispetto alla root del monorepo.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# La console Windows (cp1252) non codifica i glifi Unicode dei report: forziamo UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

# ---------------------------------------------------------------------------
# Repo di destinazione (ADR-0016). documentation resta SOLO su GitHub.
# ---------------------------------------------------------------------------
REPOS = [
    "logistico-lib",
    "logistico-workflows",
    "logistico-infrastructure",
    "logistico-documentation",
]

# ---------------------------------------------------------------------------
# RULES: (prefisso_sorgente, repo, strip_prefix)
#   - prefisso_sorgente: path relativo alla root del monorepo (dir con "/", o file)
#   - repo: destinazione
#   - strip_prefix: prefisso da rimuovere dal path per ottenere il dest nel repo
#                   (es. "lib/" → logistica_utils/ e setup.py finiscono alla root)
# Match per PREFISSO PIÙ LUNGO: le regole più specifiche vincono su quelle generiche.
# ---------------------------------------------------------------------------
RULES = [
    # ---- logistico-lib: setup.py + package alla root ----
    ("lib/", "logistico-lib", "lib/"),

    # ---- logistico-infrastructure: Terraform brownfield alla root (infra/ strippato) ----
    ("infra/", "logistico-infrastructure", "infra/"),

    # ---- logistico-workflows: notebook, DAB, sql, script runtime ----
    # (il DAB consolidato è databricks.yml + workflows/*.yml — ACT_9018/ADR-0021;
    #  infra/databricks_bundle/ rimosso, niente più regola dedicata.)
    ("notebooks/", "logistico-workflows", ""),
    ("workflows/", "logistico-workflows", ""),
    ("sql/", "logistico-workflows", ""),
    ("databricks.yml", "logistico-workflows", ""),
    ("scripts/cdtdw_lookup_extractor/", "logistico-workflows", ""),
    ("scripts/quadratura/", "logistico-workflows", ""),
    ("scripts/sftp/", "logistico-workflows", ""),

    # ---- logistico-documentation: doc + tooling dev/ops (solo GitHub) ----
    ("DOCS/", "logistico-documentation", ""),
    ("docs/", "logistico-documentation", ""),
    ("docker/", "logistico-documentation", ""),
    ("tests/", "logistico-documentation", ""),
    ("scripts/landing_simulator/", "logistico-documentation", ""),
    ("scripts/migration/", "logistico-documentation", ""),
    ("scripts/lessons/", "logistico-documentation", ""),
    ("scripts/", "logistico-documentation", ""),   # script sciolti (apply_*, rerun_*, ...)
    ("requirements-dev.txt", "logistico-documentation", ""),
    ("pytest.ini", "logistico-documentation", ""),
    ("README.md", "logistico-documentation", ""),
]

# File del monorepo intenzionalmente NON proiettati: ogni repo genera i propri.
SKIP = {
    ".gitlab-ci.yml",   # CI del monorepo; ogni repo ha la sua (generata sotto)
    ".gitignore",       # idem
}

# Repo per cui NON generare un README (usano quello proiettato dal monorepo).
NO_README_GEN = {"logistico-documentation"}


# ===========================================================================
# Git helpers
# ===========================================================================
def run_git(root: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )
    return out.stdout


def tracked_files(root: Path) -> list[str]:
    raw = run_git(root, "ls-files", "-z")
    return [p for p in raw.split("\0") if p]


def head_sha(root: Path) -> str:
    return run_git(root, "rev-parse", "--short", "HEAD").strip()


def working_tree_dirty(root: Path) -> bool:
    # Solo modifiche a file TRACCIATI: la proiezione parte da git ls-files, quindi i file
    # untracked (es. export/artefatti) non la influenzano e non devono bloccare la rigenerazione.
    return bool(run_git(root, "status", "--porcelain", "--untracked-files=no").strip())


# ===========================================================================
# Routing
# ===========================================================================
def route(path: str) -> tuple[str, str] | None:
    """Instrada un file tracciato → (repo, dest_rel) o None se non mappato."""
    if path in SKIP:
        return None
    best = None
    for prefix, repo, strip in RULES:
        is_dir_rule = prefix.endswith("/")
        match = path.startswith(prefix) if is_dir_rule else path == prefix
        if match and (best is None or len(prefix) > len(best[0])):
            dest = path[len(strip):] if strip and path.startswith(strip) else path
            best = (prefix, repo, dest)
    if best is None:
        return None
    _, repo, dest = best
    return repo, dest


# ===========================================================================
# File generati per-repo
# ===========================================================================
def gen_gitignore() -> str:
    return (
        "# Python\n__pycache__/\n*.py[cod]\n*.egg-info/\n.eggs/\nbuild/\ndist/\n"
        "*.whl\n\n# Virtual env\n.venv/\nvenv/\nenv/\n\n"
        "# Secrets / dati (MAI versionare)\n.env\n.env.*\n!.env.example\n"
        "*.pem\n*.key\n*.p12\nterraform.tfvars\n*.tfstate\n*.tfstate.*\n.terraform/\n"
        "credentials.json\n\n# Testing\n.pytest_cache/\n.coverage\ncoverage.xml\n\n"
        "# IDE / OS\n.idea/\n.vscode/\n.DS_Store\nThumbs.db\n"
    )


def gen_readme(repo: str, sha: str) -> str:
    purpose = {
        "logistico-lib": "Libreria condivisa `logistica_utils` → wheel (GitLab Package Registry).",
        "logistico-workflows": "Notebook, Databricks Asset Bundle, SQL e script runtime.",
        "logistico-infrastructure": "Terraform brownfield dell'infrastruttura Azure/Databricks.",
    }.get(repo, "")
    return (
        f"# {repo}\n\n{purpose}\n\n"
        "> **Repo generato** dallo split del monorepo (ADR-0016) via\n"
        "> `scripts/split_to_multirepo.py`.\n"
        f"> Proiezione da monorepo **@{sha}**.\n>\n"
        "> **Durante la transizione il source of truth è il monorepo**: non modificare\n"
        "> questi file a mano finché non avviene il cutover. Al cutover il monorepo viene\n"
        "> congelato e questo repo diventa autonomo (SoT).\n"
    )


CI_LIB = """\
# logistico-lib — build & publish del wheel logistica_utils nel GitLab Package Registry.
stages: [test, build, publish]

default:
  # Il group runner del subgroup Logistico è taggato "azure-runner": i job senza tag
  # restano "stuck" (nessun match). Vedi Settings > CI/CD > Runners del progetto.
  tags: [azure-runner]
  image: python:3.11
  before_script:
    # Il GitLab aziendale usa una CA interna che il container python non conosce:
    # l'upload del wheel falliva con CERTIFICATE_VERIFY_FAILED. Aggiungiamo la CA del
    # server (se il runner la espone in CI_SERVER_TLS_CA_FILE, o via COMPANY_CA_BUNDLE)
    # al trust store di sistema -> valido sia per PyPI (pubblica) sia per il GitLab (interna).
    - |
      CA="${CI_SERVER_TLS_CA_FILE:-${COMPANY_CA_BUNDLE:-}}"
      if [ -n "$CA" ] && [ -f "$CA" ]; then
        echo "CA aziendale trovata: $CA -> aggiunta al trust store"
        cp "$CA" /usr/local/share/ca-certificates/gitlab-internal-ca.crt
        update-ca-certificates >/dev/null 2>&1 || true
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
      else
        echo "ATTENZIONE: nessuna CA interna (CI_SERVER_TLS_CA_FILE/COMPANY_CA_BUNDLE)."
        echo "Se publish fallisce con CERTIFICATE_VERIFY_FAILED, fornire la CA come"
        echo "variabile CI di tipo File (COMPANY_CA_BUNDLE) — chiedere al team piattaforma."
      fi

test:
  stage: test
  script:
    - pip install -e ".[dev]"
    - python -c "import logistica_utils; print('import OK:', logistica_utils.__name__)"
    # NB: gli unit test della lib oggi vivono in logistico-documentation (ADR-0016).
    #     Valutare se portarne un sottoinsieme qui per un gate autosufficiente.

build:
  stage: build
  script:
    - pip install build
    # La versione del wheel deve seguire il TAG di release, non restare quella hardcoded
    # in setup.py: senza questo ogni release ripubblica la stessa versione (collisione nel
    # Package Registry) e il numero non traccia il rilascio. Su tag: allinea setup.py al tag.
    - if [ -n "$CI_COMMIT_TAG" ]; then V="${CI_COMMIT_TAG#v}"; sed -i 's/version="[^"]*"/version="'"$V"'"/' setup.py; fi
    - python -m build --wheel
  artifacts:
    paths: [dist/*.whl]
    expire_in: 1 week

publish:
  stage: publish
  script:
    - pip install twine
    - >
      TWINE_USERNAME=gitlab-ci-token
      TWINE_PASSWORD="${CI_JOB_TOKEN}"
      python -m twine upload
      --repository-url "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi"
      dist/*.whl
  rules:
    - if: '$CI_COMMIT_TAG'   # pubblica solo su tag di versione (es. v1.0.0)
"""

CI_WORKFLOWS = """\
# logistico-workflows — validate/deploy del Databricks Asset Bundle.
# Secret CI/CD (ADR-0005, masked per-repo): DATABRICKS_HOST, DATABRICKS_TOKEN.
stages: [validate, deploy]

default:
  tags: [azure-runner]   # group runner del subgroup Logistico (vedi Runners del progetto)
  image: python:3.11

validate:
  stage: validate
  script:
    - pip install databricks-cli   # TODO: pinnare la versione della Databricks CLI
    - databricks bundle validate
  # TODO: installare il wheel di logistico-lib dal Package Registry (DBR-05) e
  #       pinnare la versione in databricks.yml (libraries: - whl: ...).

deploy_dev:
  stage: deploy
  script:
    - databricks bundle deploy -t dev
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy_prod:
  stage: deploy
  script:
    - databricks bundle deploy -t prod
  rules:
    - if: '$CI_COMMIT_TAG'
      when: manual   # gate PROD manuale (ADR-0017 / ACT_0.2.4)
"""

CI_INFRA = """\
# logistico-infrastructure — Terraform validate/plan (apply manuale).
# Secret CI/CD (ADR-0005, masked per-repo): ARM_CLIENT_ID/SECRET/TENANT_ID/SUBSCRIPTION_ID.
stages: [validate, plan]

default:
  tags: [azure-runner]   # group runner del subgroup Logistico (vedi Runners del progetto)
  image:
    name: hashicorp/terraform:latest   # TODO: pinnare la versione di Terraform
    # L'immagine terraform ha ENTRYPOINT=terraform: senza reset GitLab esegue
    # "terraform sh -c ..." -> 'no command named sh'. entrypoint: [""] ripristina la shell.
    entrypoint: [""]

variables:
  # Config brownfield sotto terraform/brownfield/ (la root ha solo il modulo greenfield
  # deprecato: "Non eseguire terraform apply"). Tutti i comandi usano -chdir su questa dir.
  TF_DIR: terraform/brownfield
  # Auth via Managed Identity (team 2026-08-27): niente client_secret né token Databricks.
  # ARM_USE_MSI=true fa autenticare azurerm (provider + backend use_azuread_auth) con la MI
  # del runner Azure. Il provider databricks usa azure_use_msi=true (in main.tf) + ARM_CLIENT_ID.
  # Da impostare come variabili CI (Settings > CI/CD > Variables, Protected — NON sono segreti):
  #   ARM_CLIENT_ID (client id user-assigned MI), ARM_TENANT_ID, ARM_SUBSCRIPTION_ID (DEV),
  #   TF_VAR_databricks_host (URL workspace DEV).
  ARM_USE_MSI: "true"

validate:
  stage: validate
  script:
    - terraform -chdir=$TF_DIR init -backend=false
    - terraform -chdir=$TF_DIR validate

plan:
  stage: plan
  script:
    - terraform -chdir=$TF_DIR init
    - terraform -chdir=$TF_DIR plan
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
"""

CI_BY_REPO = {
    "logistico-lib": CI_LIB,
    "logistico-workflows": CI_WORKFLOWS,
    "logistico-infrastructure": CI_INFRA,
    # documentation: nessuna pipeline (repo solo-doc, mai sul GitLab cliente).
}


# ===========================================================================
# Generazione
# ===========================================================================
def wipe_repo_worktree(repo_dir: Path) -> None:
    """Svuota l'albero di lavoro del repo tranne .git/ (le rimozioni si propagano)."""
    if not repo_dir.exists():
        return
    for child in repo_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def generate(root: Path, out: Path, targets: list[str], dry_run: bool) -> int:
    sha = head_sha(root)
    files = tracked_files(root)

    # Routing di tutti i file tracciati.
    routing: dict[str, list[tuple[str, str]]] = {r: [] for r in REPOS}
    unmapped: list[str] = []
    for f in files:
        r = route(f)
        if r is None:
            if f not in SKIP:
                unmapped.append(f)
            continue
        repo, dest = r
        routing[repo].append((f, dest))

    print(f"== Split monorepo @{sha} → {out}  (dry-run={dry_run}) ==\n")
    for repo in REPOS:
        n = len(routing[repo])
        flag = "→ genero" if repo in targets else "  (skip)"
        gl = "GitLab❌" if repo == "logistico-documentation" else "GitLab✅"
        print(f"  {repo:<26} {n:>4} file  {gl}  {flag}")

    # File non mappati: MAI persi in silenzio.
    print()
    if unmapped:
        print(f"  ⚠️  {len(unmapped)} file NON MAPPATI (aggiungere una regola o a SKIP):")
        for f in unmapped[:40]:
            print(f"        {f}")
        if len(unmapped) > 40:
            print(f"        ... e altri {len(unmapped) - 40}")
    else:
        print("  ✓ nessun file non mappato: ogni file tracciato ha una destinazione.")

    # Avviso consolidamento databricks.yml (ADR-0016 / ACT_9011).
    dbx = [f for f, _ in routing["logistico-workflows"] if f.endswith("databricks.yml")]
    if len(dbx) > 1 and "logistico-workflows" in targets:
        print("\n  ⚠️  logistico-workflows: consolidare manualmente i databricks.yml:")
        for f in dbx:
            print(f"        {f}")

    if dry_run:
        print("\n(dry-run: nessuna scrittura)")
        return 1 if unmapped else 0

    # Scrittura effettiva dei repo selezionati.
    for repo in targets:
        repo_dir = out / repo
        repo_dir.mkdir(parents=True, exist_ok=True)
        wipe_repo_worktree(repo_dir)
        for src_rel, dest_rel in routing[repo]:
            src = root / src_rel
            dst = repo_dir / dest_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        # File generati (hanno precedenza sui proiettati).
        (repo_dir / ".gitignore").write_text(gen_gitignore(), encoding="utf-8")
        if repo not in NO_README_GEN:
            (repo_dir / "README.md").write_text(gen_readme(repo, sha), encoding="utf-8")
        if repo in CI_BY_REPO:
            (repo_dir / ".gitlab-ci.yml").write_text(CI_BY_REPO[repo], encoding="utf-8")
        print(f"\n  ✓ {repo}: {len(routing[repo])} file proiettati in {repo_dir}")

    print(f"\nProvenienza — commit iniziale suggerito per ogni repo:")
    print(f'    git add -A && git commit -m "import da monorepo @{sha}"')
    return 1 if unmapped else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Split monorepo → multi-repo (ADR-0016, mono→multi).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--only", choices=REPOS, help="genera un solo repo")
    g.add_argument("--all", action="store_true", help="genera tutti e 4 i repo")
    ap.add_argument("--out", default=None, help="dir di output (default: ../logistico-repos)")
    ap.add_argument("--dry-run", action="store_true", help="anteprima routing, nessuna scrittura")
    args = ap.parse_args()

    root = Path(run_git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
    out = Path(args.out).resolve() if args.out else (root.parent / "logistico-repos")
    targets = REPOS if args.all else [args.only]

    if working_tree_dirty(root) and not args.dry_run:
        print("⚠️  Il working tree del monorepo non è pulito. La proiezione riflette i file\n"
              "    TRACCIATI (HEAD): modifiche non committate NON vengono proiettate.\n"
              "    Committa o fai --dry-run prima di generare.", file=sys.stderr)
        return 2

    return generate(root, out, targets, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
