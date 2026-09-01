#!/usr/bin/env python3
"""Scaffold di una voce worklog dal diff git (ADR-0024).

Pre-compila una nuova voce `DOCS/main/worklog/YYYY-MM-DD-NN_slug.md` deducendo dal commit range:
- `push_monorepo` = HEAD corto;
- gli id `ACT_/ADR-/LL-/OP-` citati nei **file toccati** e nei **commit message** del range;
- data dal commit HEAD, `NN` = progressivo del giorno.
L'umano completa poi narrazione + stato (8-12 righe) e rigenera l'indice.

Uso:
    python scripts/worklog/new_entry.py --slug backend-azcopy --title "Backend AzCopy per il send"
    python scripts/worklog/new_entry.py --slug fix-x --range abc123..HEAD --title "..."

Default range: <push_monorepo dell'ultima voce>..HEAD (o HEAD~1..HEAD se non deducibile).
Nessuna scrittura remota: prepara solo il file locale, poi commit/push come al solito.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKLOG_DIR = ROOT / "DOCS" / "main" / "worklog"

RE_ACT = re.compile(r"ACT_[0-9A-Za-z.\-]+")
RE_ADR = re.compile(r"ADR-\d{4}")
RE_LL = re.compile(r"LL-\d{3}")
RE_OP = re.compile(r"OP-[A-Z0-9]+(?:-[A-Z0-9]+)*")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False).stdout


def last_entry_hash() -> str | None:
    files = sorted(WORKLOG_DIR.glob("20??-*.md"), reverse=True)
    if not files:
        return None
    for line in files[0].read_text(encoding="utf-8").splitlines():
        if line.startswith("push_monorepo:"):
            h = line.split(":", 1)[1].strip().strip('"').strip("'")
            return h or None
    return None


def detect_ids(text: str) -> dict[str, list[str]]:
    def norm_act(s: str) -> str:
        # ACT_<code>_<slug> -> ACT_<code>; togli punteggiatura di fine frase (es. "ACT_0.1.6.")
        return ("ACT_" + s[4:].split("_", 1)[0]).rstrip(".-")
    acts = sorted({norm_act(x) for x in RE_ACT.findall(text)})
    return {
        "act": acts,
        "adr": sorted(set(RE_ADR.findall(text))),
        "lesson": sorted(set(RE_LL.findall(text))),
        "op": sorted(set(RE_OP.findall(text))),
    }


def fmt_list(v: list[str]) -> str:
    return "[" + ", ".join(v) + "]"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slug", required=True, help="slug kebab-case della voce")
    p.add_argument("--title", default="", help="titolo leggibile della voce")
    p.add_argument("--range", dest="rng", default="", help="commit range (default: <ultima voce>..HEAD)")
    p.add_argument("--author", default="", help="autore (default: git config user.name)")
    args = p.parse_args(argv)

    head = git("rev-parse", "--short", "HEAD").strip()
    if not head:
        print("[ERROR] non sembra un repo git (o HEAD assente).", file=sys.stderr)
        return 2
    date = git("show", "-s", "--format=%cd", "--date=short", "HEAD").strip()

    rng = args.rng
    if not rng:
        base = last_entry_hash()
        rng = f"{base}..HEAD" if base else "HEAD~1..HEAD"

    files = git("diff", "--name-only", rng)
    msgs = git("log", rng, "--format=%B")
    ids = detect_ids(files + "\n" + msgs)

    author = args.author or git("config", "user.name").strip() or "sconosciuto"

    # progressivo del giorno
    nn = 1 + sum(1 for _ in WORKLOG_DIR.glob(f"{date}-*.md"))
    fname = f"{date}-{nn:02d}_{args.slug}.md"
    fpath = WORKLOG_DIR / fname
    if fpath.exists():
        print(f"[ERROR] esiste gia': {fpath}", file=sys.stderr)
        return 2

    changed = [f for f in files.splitlines() if f.strip()]
    changed_hint = ", ".join(sorted({Path(f).name for f in changed})[:12]) or "(nessuno)"

    content = (
        f"---\n"
        f"data: {date}\n"
        f"titolo: {args.title or args.slug}\n"
        f"autore: {author}\n"
        f'push_monorepo: {head}\n'
        f'push_documentation: "n/d"\n'
        f'push_gitlab: "—"\n'
        f"act: {fmt_list(ids['act'])}\n"
        f"adr: {fmt_list(ids['adr'])}\n"
        f"lesson: {fmt_list(ids['lesson'])}\n"
        f"op: {fmt_list(ids['op'])}\n"
        f"---\n\n"
        f"## Cosa e' stato fatto\n"
        f"- TODO (quali ACT toccate e in che stato). File toccati: {changed_hint}\n\n"
        f"## Novita'\n"
        f"- TODO (ADR nate/cambiate, lessons nuove, OP aperti/chiusi, info emerse)\n\n"
        f"## Doc aggiornati\n"
        f"- TODO\n\n"
        f"## Stato dopo il push / prossimi passi\n"
        f"- TODO (1-3 righe: dove siamo, blocchi, prossimo passo)\n"
    )
    fpath.write_text(content, encoding="utf-8", newline="\n")
    print(f"[OK] creata {fpath.relative_to(ROOT)} (range {rng})")
    print(f"     id rilevati -> act={ids['act']} adr={ids['adr']} lesson={ids['lesson']} op={ids['op']}")
    print("     completa narrazione+stato, poi: python scripts/worklog/worklog_index.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
