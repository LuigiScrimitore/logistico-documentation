#!/usr/bin/env python3
"""Rigenera DOCS/main/lessons/INDEX.md dal frontmatter dei file LL-*.md.

Perche' generato e non scritto a mano (ADR-0020): un indice mantenuto manualmente e' un
file che tutti toccano, quindi una macchina da conflitti git. Rigenerandolo, i contributi
paralleli restano su file distinti e l'indice si ricostruisce senza merge.

Uso:
    python scripts/lessons/lessons_index.py            # rigenera
    python scripts/lessons/lessons_index.py --check    # verifica allineamento (exit 1 se stale)

Il --check e' pensato per CI / pre-commit: fallisce se l'indice non riflette i file.
Nessuna dipendenza esterna: il frontmatter e' letto con un parser minimo (YAML solo per i
sottoinsiemi usati dal template), cosi' lo script gira anche senza pyyaml installato.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSONS_DIR = ROOT / "DOCS" / "main" / "lessons"
INDEX = LESSONS_DIR / "INDEX.md"

STADI = {
    "lezione": "🟡 lezione",
    "regola-documentata": "🔵 regola",
    "guardrail-automatico": "🟢 guardrail",
}


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parser minimo per il frontmatter del template: scalari e liste (inline o a trattini)."""
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

        # elemento di lista a trattini
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

        if not val:                      # lista a trattini nelle righe successive
            current_list_key = key
            data[key] = []
            continue

        current_list_key = None
        if val.startswith("[") and val.endswith("]"):   # lista inline
            items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            data[key] = [v for v in items if v]
        else:
            data[key] = val.strip('"').strip("'")
    return data


def collect() -> list[dict[str, object]]:
    out = []
    for f in sorted(LESSONS_DIR.glob("LL-*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not fm:
            print(f"[WARN] {f.name}: frontmatter assente o malformato, saltato", file=sys.stderr)
            continue
        fm["_file"] = f.name
        out.append(fm)
    return out


def as_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)] if v else []


def render(lessons: list[dict[str, object]]) -> str:
    L: list[str] = []
    L.append("# Lezioni operative — indice")
    L.append("")
    L.append("> ⚠️ **File generato.** Non modificare a mano: rigenerare con")
    L.append("> `python scripts/lessons/lessons_index.py`. Convenzioni in [README](README.md),")
    L.append("> decisione in [ADR-0020](../adr/0020_lezioni_operative.md).")
    L.append("")
    L.append(f"**{len(lessons)} lezioni.** Stadio: 🟡 lezione · 🔵 regola documentata · 🟢 guardrail automatico")
    L.append("")

    # ── ricerca per sintomo: la via d'accesso principale ──────────────────────
    L.append("## Cerca per sintomo")
    L.append("")
    L.append("Parti da qui: il sintomo e' come il problema si presenta, non il nome dell'attivita'.")
    L.append("")
    L.append("| Sintomo | Lezione |")
    L.append("|---|---|")
    righe = []
    for le in lessons:
        for s in as_list(le.get("sintomi")):
            righe.append((s.lower(), f"| `{s}` | [{le['id']}]({le['_file']}) |"))
    for _, riga in sorted(righe):
        L.append(riga)
    L.append("")

    # ── elenco completo ──────────────────────────────────────────────────────
    L.append("## Tutte le lezioni")
    L.append("")
    L.append("| ID | Titolo | Stadio | Tag | Origine | Data |")
    L.append("|---|---|---|---|---|---|")
    for le in lessons:
        stadio_raw = str(le.get("stadio", "lezione"))
        stadio = STADI.get(stadio_raw, stadio_raw)
        if str(le.get("automatizzabile", "")).lower() == "true" and stadio_raw != "guardrail-automatico":
            stadio += " ⚠️ da automatizzare"
        tag = ", ".join(f"`{t}`" for t in as_list(le.get("tag")))
        orig = ", ".join(as_list(le.get("origine")))
        L.append(f"| [{le['id']}]({le['_file']}) | {le.get('titolo','')} | {stadio} | {tag} | {orig} | "
                 f"{le.get('data','')} |")
    L.append("")

    # ── debito: lezioni automatizzabili non ancora guardrail ─────────────────
    debito = [le for le in lessons
              if str(le.get("automatizzabile", "")).lower() == "true"
              and str(le.get("stadio")) != "guardrail-automatico"]
    L.append("## Debito di automazione")
    L.append("")
    if debito:
        L.append("Lezioni nate da difetti sui dati che **devono** diventare un check DQ o un test "
                 "(ADR-0020, scala vincolante):")
        L.append("")
        for le in debito:
            L.append(f"- [{le['id']}]({le['_file']}) — {le.get('titolo','')}")
    else:
        L.append("Nessuno: tutte le lezioni automatizzabili sono gia' guardrail.")
    L.append("")

    # ── raggruppamento per tag ───────────────────────────────────────────────
    per_tag: dict[str, list[dict[str, object]]] = {}
    for le in lessons:
        for t in as_list(le.get("tag")):
            per_tag.setdefault(t, []).append(le)
    L.append("## Per tag")
    L.append("")
    for t in sorted(per_tag):
        ids = " · ".join(f"[{le['id']}]({le['_file']})" for le in per_tag[t])
        L.append(f"- **`{t}`**: {ids}")
    L.append("")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true",
                   help="non scrive: exit 1 se l'indice non e' allineato ai file")
    args = p.parse_args(argv)

    if not LESSONS_DIR.is_dir():
        print(f"[ERROR] directory non trovata: {LESSONS_DIR}", file=sys.stderr)
        return 2

    lessons = collect()
    nuovo = render(lessons)

    if args.check:
        attuale = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if attuale != nuovo:
            print("[STALE] INDEX.md non allineato: esegui python scripts/lessons/lessons_index.py",
                  file=sys.stderr)
            return 1
        print(f"[OK] INDEX.md allineato ({len(lessons)} lezioni)")
        return 0

    INDEX.write_text(nuovo, encoding="utf-8", newline="\n")
    debito = sum(1 for le in lessons
                 if str(le.get("automatizzabile", "")).lower() == "true"
                 and str(le.get("stadio")) != "guardrail-automatico")
    print(f"[OK] INDEX.md rigenerato: {len(lessons)} lezioni, {debito} da automatizzare")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
