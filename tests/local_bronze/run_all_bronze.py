"""
Batch runner: esegue TUTTI i notebook Bronze nel container e produce un report
pass/fail con righe processate.

Riusa la stessa SparkSession per tutti i notebook (--keep-spark-alive non basta:
ogni invocazione di run_notebook.py crea un processo diverso). Qui carichiamo
un solo Spark e iteriamo in-process: molto piu' veloce (~15s/notebook -> ~5s).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from dbutils_stub import DBUtilsStub, NotebookExit  # noqa: E402
from spark_session import build_spark, ensure_databases, vacuum_all_tables  # noqa: E402
from run_notebook import _install_fqn_rewriters, _file_uri  # noqa: E402


def discover_notebooks(root: Path) -> list[Path]:
    nbs = sorted(root.rglob("bronze_*.py"))
    return [p for p in nbs if "__pycache__" not in p.parts]


# Lista canonica dei 22 siti attivi (db-link logistix, vedi scripts/landing_simulator/config.yaml
# e run_big_rerun.SITI_22). Default del runner giornaliero: ingerire TUTTI i siti, altrimenti
# le anagrafiche FULL (struttura_mag/operatori/aree) regrediscono a 2 siti e i fatti company-wide
# vanno in orphan 85-95% su SITO/AREA (vedi OP-SITO).
SITI_22 = ("laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,"
           "lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx")


def run_one(nb_path: Path, spark, landing_uri: str, run_date: str, siti: str = SITI_22,
            file_format: str = "auto") -> dict:
    """Esegue un singolo notebook in-process. Ritorna dict con esito."""
    result: dict = {
        "notebook": str(nb_path.relative_to(REPO_ROOT)),
        "status": "UNKNOWN",
        "rows": None,
        "duration_s": 0.0,
        "error": None,
    }
    overrides = {
        "env": "dev",
        "run_date": run_date,
        "landing_base_path": landing_uri,
        "file_format": file_format,
        "siti": siti,
    }
    dbutils = DBUtilsStub(widget_overrides=overrides)
    g: dict = {
        "__name__": "__main__",
        "__file__": str(nb_path),
        "spark": spark,
        "dbutils": dbutils,
        "sc": spark.sparkContext,
    }
    code = nb_path.read_text(encoding="utf-8-sig")  # -sig: tollera BOM UTF-8
    start = time.time()
    try:
        exec(compile(code, str(nb_path), "exec"), g)
        result["status"] = "OK"
    except NotebookExit as e:
        result["status"] = "OK"
        result["error"] = f"notebook.exit({e.message!r})"
    except SystemExit as e:
        result["status"] = "OK"
        result["error"] = f"sys.exit({e.code!r})"
    except Exception as e:
        result["status"] = "FAIL"
        msg = str(e)
        # tronchiamo per leggibilita'
        result["error"] = (msg[:300] + "...") if len(msg) > 300 else msg
        result["traceback"] = traceback.format_exc()
    finally:
        result["duration_s"] = round(time.time() - start, 2)
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bronze-dir", default=str(REPO_ROOT / "notebooks" / "bronze"))
    p.add_argument("--landing", default="/workspace/data/landing")
    p.add_argument("--warehouse", default="/workspace/data/warehouse")
    p.add_argument("--run-date", default="2026-06-09")
    p.add_argument("--report", default="/workspace/data/warehouse/bronze_test_report.json")
    p.add_argument("--filter", default=None, help="Sostringa per filtrare i notebook")
    p.add_argument("--file-format", default="auto",
                   help="Formato file landing: csv | parquet | auto (default: auto — rileva dal filesystem).")
    p.add_argument("--siti", default=SITI_22,
                   help="Lista siti (db-link) separati da virgola. Default: tutti i 22 siti attivi.")
    p.add_argument("--vacuum", action="store_true",
                   help="A fine run, VACUUM di manutenzione di tutte le tabelle Delta del warehouse.")
    p.add_argument("--vacuum-retain-hours", type=float,
                   default=float(os.environ.get("AUTO_VACUUM_RETAIN_HOURS", "0")),
                   help="Retention VACUUM in ore (default 0 = locale, no time-travel; cloud: 168).")
    p.add_argument("--vacuum-prefix", default=None,
                   help="Prefisso/i database da vacuumare (csv, es. 'silver'). "
                        "Default: tutto il warehouse. Ogni layer pulisce il proprio.")
    args = p.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

    spark = build_spark(args.warehouse, app_name="bronze-batch-test")
    ensure_databases(spark)
    _install_fqn_rewriters(spark)
    landing_uri = _file_uri(Path(args.landing))

    nbs = discover_notebooks(Path(args.bronze_dir))
    if args.filter:
        nbs = [n for n in nbs if args.filter in n.name]

    print(f"\n{'='*100}")
    _nsiti = len([s for s in args.siti.split(",") if s.strip()])
    print(f"BATCH BRONZE TEST | {len(nbs)} notebook | {_nsiti} siti | landing={args.landing} | warehouse={args.warehouse}")
    print(f"{'='*100}\n")

    results = []
    for i, nb in enumerate(nbs, 1):
        rel = nb.relative_to(REPO_ROOT)
        print(f"[{i:2d}/{len(nbs)}] {rel} ...", end=" ", flush=True)
        r = run_one(nb, spark, landing_uri, args.run_date, args.siti,
                    file_format=getattr(args, "file_format", "auto"))
        results.append(r)
        if r["status"] == "OK":
            print(f"OK ({r['duration_s']}s)")
        else:
            print(f"FAIL ({r['duration_s']}s) - {r['error'][:120]}")

    # Riepilogo
    ok = sum(1 for r in results if r["status"] == "OK")
    fail = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{'='*100}")
    print(f"RIEPILOGO: {ok} OK | {fail} FAIL | {len(results)} totali")
    print(f"{'='*100}")
    if fail:
        print("\nFAILURES:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  - {r['notebook']}")
                print(f"      {r['error'][:200]}")

    # Persisti il report
    rep = Path(args.report)
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nReport: {rep}")

    # Manutenzione: VACUUM di fine run (rimuove i tombstone Delta accumulati dai MERGE).
    if args.vacuum:
        print(f"\n{'='*100}")
        try:
            _prefixes = [s.strip() for s in args.vacuum_prefix.split(",")] if args.vacuum_prefix else None
            vacuum_all_tables(spark, args.warehouse, retain_hours=args.vacuum_retain_hours,
                              prefixes=_prefixes)
        except Exception as e:  # noqa: BLE001
            print(f"VACUUM di manutenzione fallito (non bloccante): {str(e)[:200]}")
        print(f"{'='*100}")

    spark.stop()
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    # Run bronze diretto: VACUUM di fine run sul solo layer bronze (default ON).
    if "--vacuum" not in sys.argv[1:]:
        sys.argv.append("--vacuum")
    if not any(a.startswith("--vacuum-prefix") for a in sys.argv[1:]):
        sys.argv.extend(["--vacuum-prefix", "bronze"])
    sys.exit(main())
