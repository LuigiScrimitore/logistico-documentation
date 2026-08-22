"""
Batch runner Silver: identico a run_all_bronze ma punta a notebooks/silver.
Riusa tutta l'infrastruttura (Spark + FQN rewriter + dbutils stub).
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

# Reimporto e patcho main di run_all_bronze per cambiare default bronze-dir
import run_all_bronze  # noqa: E402

if __name__ == "__main__":
    # Forza il default a notebooks/silver se non specificato
    if not any(a.startswith("--bronze-dir") for a in sys.argv[1:]):
        sys.argv.extend(["--bronze-dir", str(REPO_ROOT / "notebooks" / "silver")])
    if not any(a.startswith("--report") for a in sys.argv[1:]):
        sys.argv.extend(["--report", "/workspace/data/warehouse/silver_test_report.json"])
    # VACUUM di manutenzione a fine run (default ON), SOLO sul layer silver.
    # Retention via env AUTO_VACUUM_RETAIN_HOURS (default 0).
    if "--vacuum" not in sys.argv[1:]:
        sys.argv.append("--vacuum")
    if not any(a.startswith("--vacuum-prefix") for a in sys.argv[1:]):
        sys.argv.extend(["--vacuum-prefix", "silver"])
    # Patch del prefix nei file silver: i Silver iniziano con "silver_*"
    orig_discover = run_all_bronze.discover_notebooks

    def discover_silver(root: Path):
        nbs = sorted(root.rglob("silver_*.py"))
        return [p for p in nbs if "__pycache__" not in p.parts]
    run_all_bronze.discover_notebooks = discover_silver

    sys.exit(run_all_bronze.main())
