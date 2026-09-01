#!/usr/bin/env python3
"""Rigenera DOCS/main/worklog/INDEX.md dal frontmatter delle voci del worklog.

Perche' generato e non scritto a mano (ADR-0024, come lessons/ADR-0020): un indice mantenuto
a mano e' un file che tutti toccano, quindi una macchina da conflitti git. Rigenerandolo, i
contributi paralleli restano su file distinti e l'indice si ricostruisce senza merge.

Uso:
    python scripts/worklog/worklog_index.py            # rigenera
    python scripts/worklog/worklog_index.py --check    # exit 1 se l'indice e' stale (CI/pre-commit)

Voci: DOCS/main/worklog/YYYY-MM-DD-NN_slug.md. Ordinamento per nome file decrescente = newest-first.
Nessuna dipendenza esterna: frontmatter letto con un parser minimo (niente pyyaml).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKLOG_DIR = ROOT / "DOCS" / "main" / "worklog"
INDEX = WORKLOG_DIR / "INDEX.md"


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parser minimo: scalari e liste (inline [a, b] o a trattini)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    body = text[3:end]
    data: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_list_key:
            val = stripped[2:].strip().strip('"').strip("'")
            data.setdefault(current_list_key, [])
            if isinstance(data[current_list_key], list):
                data[current_list_key].append(val)  # type: ignore[union-attr]
            continue
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            current_list_key = key
            data[key] = []
            continue
        current_list_key = None
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            data[key] = [v for v in items if v]
        else:
            data[key] = val.strip('"').strip("'")
    return data


def as_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)] if v else []


def collect() -> list[dict[str, object]]:
    out = []
    for f in sorted(WORKLOG_DIR.glob("20??-*.md"), reverse=True):  # newest-first per nome
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not fm:
            print(f"[WARN] {f.name}: frontmatter assente o malformato, saltato", file=sys.stderr)
            continue
        fm["_file"] = f.name
        out.append(fm)
    return out


def _refs(fm: dict[str, object], key: str) -> str:
    return " ".join(as_list(fm.get(key))) or "—"


def render(entries: list[dict[str, object]]) -> str:
    L: list[str] = []
    L.append("# Worklog — indice (per push su `main`)")
    L.append("")
    L.append("> ⚠️ **File generato.** Non modificare a mano: rigenerare con")
    L.append("> `python scripts/worklog/worklog_index.py`. Convenzioni in [README](README.md),")
    L.append("> decisione in [ADR-0024](../adr/0024_worklog_diario_push.md).")
    L.append("")
    if entries:
        top = entries[0]
        L.append(f"**Ultimo push:** [{top.get('titolo','')}]({top['_file']}) "
                 f"· {top.get('data','')} · monorepo `{top.get('push_monorepo','')}`")
        L.append("")
    L.append(f"**{len(entries)} voci.** La prima riga (in alto) è il push più recente = **stato corrente**.")
    L.append("")
    L.append("| Data | Push | Cosa | ACT | ADR | LL | OP |")
    L.append("|---|---|---|---|---|---|---|")
    for e in entries:
        L.append(
            f"| {e.get('data','')} "
            f"| `{e.get('push_monorepo','')}` "
            f"| [{e.get('titolo','')}]({e['_file']}) "
            f"| {_refs(e,'act')} | {_refs(e,'adr')} | {_refs(e,'lesson')} | {_refs(e,'op')} |"
        )
    L.append("")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="non scrive: exit 1 se l'indice non e' allineato")
    args = p.parse_args(argv)

    if not WORKLOG_DIR.is_dir():
        print(f"[ERROR] directory non trovata: {WORKLOG_DIR}", file=sys.stderr)
        return 2

    entries = collect()
    nuovo = render(entries)

    if args.check:
        attuale = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if attuale != nuovo:
            print("[STALE] INDEX.md non allineato: esegui python scripts/worklog/worklog_index.py",
                  file=sys.stderr)
            return 1
        print(f"[OK] INDEX.md allineato ({len(entries)} voci)")
        return 0

    INDEX.write_text(nuovo, encoding="utf-8", newline="\n")
    print(f"[OK] INDEX.md rigenerato: {len(entries)} voci")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
