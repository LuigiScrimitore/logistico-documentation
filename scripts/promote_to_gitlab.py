#!/usr/bin/env python3
"""
promote_to_gitlab.py — Promuove una release stabile a un repo del GitLab cliente (modello A).

MODELLO A (ADR-0016, snapshot di release): il repo GitLab riceve **snapshot puliti** di release,
NON la storia di sviluppo di GitHub. Direzione **mono-direzionale**: (monorepo →) GitHub → GitLab,
mai il contrario.

Da eseguire quando un repo GitHub è **testato/stabile**:
1. checkout dello stato stabile nel `--source` (es. `git checkout vX.Y.Z`);
2. questo script snapshotta i file TRACCIATI del source nel working copy GitLab, committa
   ``release vX.Y.Z (github @<sha>)`` e crea il tag ``vX.Y.Z``;
3. l'utente fa il push (`git push gitlab main --tags`) → la CI GitLab parte sul tag.

`logistico-documentation` NON è promuovibile: resta solo su GitHub.

Uso
---
    python scripts/promote_to_gitlab.py --repo logistico-lib --version v1.0.0 \
        --source C:/PROGETTI/logistico-repos/logistico-lib \
        --out    C:/PROGETTI/logistico-repos-gitlab
    # anteprima:
    python scripts/promote_to_gitlab.py --repo logistico-lib --version v1.0.0 --source ... --dry-run
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

# Repo promuovibili sul GitLab cliente (documentation escluso by-design, ADR-0016).
GITLAB_REPOS = {"logistico-lib", "logistico-workflows", "logistico-infrastructure"}
DOC_REPO = "logistico-documentation"
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+([-.].+)?$")   # v1.0.0, v1.2.3-rc1, ...


def run_git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def tracked_files(root: Path) -> list[str]:
    return [p for p in run_git(root, "ls-files", "-z").split("\0") if p]


def head_sha(root: Path) -> str:
    return run_git(root, "rev-parse", "--short", "HEAD").strip()


def is_clean(root: Path) -> bool:
    return not run_git(root, "status", "--porcelain").strip()


def wipe_worktree(repo_dir: Path) -> None:
    for child in repo_dir.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description="Promuove una release a un repo del GitLab cliente (modello A).")
    ap.add_argument("--repo", required=True, help="repo da promuovere (NON documentation)")
    ap.add_argument("--version", required=True, help="tag di release, es. v1.0.0")
    ap.add_argument("--source", required=True, help="working copy GitHub del repo (stato stabile checkoutato)")
    ap.add_argument("--out", default=None, help="dir dei working copy GitLab (default: ../logistico-repos-gitlab)")
    ap.add_argument("--dry-run", action="store_true", help="anteprima, nessuna scrittura")
    args = ap.parse_args()

    # Guardrail: documentation e nomi non validi.
    if args.repo == DOC_REPO:
        print(f"✗ {DOC_REPO} NON va sul GitLab cliente (ADR-0016): promozione rifiutata.", file=sys.stderr)
        return 2
    if args.repo not in GITLAB_REPOS:
        print(f"✗ repo sconosciuto: {args.repo}. Ammessi: {sorted(GITLAB_REPOS)}", file=sys.stderr)
        return 2
    if not VERSION_RE.match(args.version):
        print(f"✗ versione non valida: {args.version} (atteso vX.Y.Z).", file=sys.stderr)
        return 2

    source = Path(args.source).resolve()
    if not (source / ".git").exists():
        print(f"✗ --source non è un repo git: {source}", file=sys.stderr)
        return 2
    if not is_clean(source):
        print(f"✗ --source ha modifiche non committate: {source}\n"
              f"    Checkout di uno stato stabile (es. git checkout {args.version}) e riprova.",
              file=sys.stderr)
        return 2

    sha = head_sha(source)
    files = tracked_files(source)
    out = Path(args.out).resolve() if args.out else (source.parent.parent / "logistico-repos-gitlab")
    dest = out / args.repo

    print(f"== Promozione {args.repo} {args.version} — snapshot da GitHub @{sha} ==")
    print(f"   source: {source}\n   dest:   {dest}\n   file:   {len(files)}  (dry-run={args.dry_run})")

    if args.dry_run:
        print("\n(dry-run: nessuna scrittura)")
        return 0

    # Snapshot pulito nel working copy GitLab.
    dest.mkdir(parents=True, exist_ok=True)
    if not (dest / ".git").exists():
        run_git(dest, "init", "-b", "main")
    else:
        wipe_worktree(dest)
    for rel in files:
        src_f = source / rel
        dst_f = dest / rel
        dst_f.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_f, dst_f)

    run_git(dest, "add", "-A")
    # Se non ci sono differenze rispetto all'ultimo commit, git commit fallirebbe: gestiamo.
    if not run_git(dest, "status", "--porcelain").strip() and run_git(dest, "log", "--oneline", "-1").strip():
        print("\n⚠️  nessuna differenza rispetto all'ultima release: niente da promuovere.")
        return 0
    run_git(dest, "commit", "-m", f"release {args.version} (github @{sha})")
    run_git(dest, "tag", args.version)

    print(f"\n✓ snapshot committato e taggato {args.version} in {dest}")
    print("\nPush sul GitLab cliente (azione utente — richiede autenticazione):")
    print(f"    cd {dest}")
    print("    git remote add gitlab https://<gitlab-host>/cno/cno-data-platform/logistico/"
          f"{args.repo}.git   # solo la prima volta")
    print("    git push gitlab main --tags")
    print("\nLa CI GitLab parte sul tag (lib: publish wheel · workflows: bundle deploy + gate PROD · infra: plan).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
