"""
Batch runner Gold: esegue i notebook Gold in ORDINE DI FASE.

A differenza di Bronze/Silver (indipendenti), il Gold ha dipendenze interne:
  - aggregati A_* leggono dai fact Gold F_* (Gold-to-Gold)
  - quindi: dimensioni (LU_*) -> fact (F_*) -> aggregati (A_*/dm)

Riusa l'infrastruttura di run_all_bronze (Spark + FQN rewriter + dbutils stub).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import run_all_bronze  # noqa: E402


# Ordine di fase per prefisso nome file. Indice = priorita' (piu' basso = prima).
PHASE_ORDER = {
    "gold_lu_":  0,   # lookup condivise (workaround CDT_DW) - prima dei fact che le agganciano
    "gold_dim_": 0,   # dimensioni / lookup LU_*
    "gold_f_":   1,   # fact F_*
    "gold_late": 1,   # late arriving handler (dopo i fact base, stessa fase)
    "gold_dm_":  2,   # datamart aggregati (es. A_GIACENZE_MONTHLY)
    "gold_a_":   3,   # aggregati A_* (alcuni leggono dai dm, es. a_stock <- A_GIACENZE_MONTHLY)
}


def phase_of(path: Path) -> int:
    name = path.name
    for prefix, order in PHASE_ORDER.items():
        if name.startswith(prefix):
            return order
    return 1  # default: trattalo come fact


def discover_gold(root: Path):
    nbs = [p for p in root.rglob("gold_*.py") if "__pycache__" not in p.parts]
    # Ordina per (fase, path) cosi' dimensioni < fact < aggregati, e dentro la fase per path
    return sorted(nbs, key=lambda p: (phase_of(p), str(p)))


if __name__ == "__main__":
    if not any(a.startswith("--bronze-dir") for a in sys.argv[1:]):
        sys.argv.extend(["--bronze-dir", str(REPO_ROOT / "notebooks" / "gold")])
    if not any(a.startswith("--report") for a in sys.argv[1:]):
        sys.argv.extend(["--report", "/workspace/data/warehouse/gold_test_report.json"])
    # VACUUM di manutenzione a fine run (default ON), SOLO sul layer gold.
    if "--vacuum" not in sys.argv[1:]:
        sys.argv.append("--vacuum")
    if not any(a.startswith("--vacuum-prefix") for a in sys.argv[1:]):
        sys.argv.extend(["--vacuum-prefix", "gold"])

    run_all_bronze.discover_notebooks = discover_gold
    sys.exit(run_all_bronze.main())
