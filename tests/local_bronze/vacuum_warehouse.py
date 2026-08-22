"""
VACUUM manutentivo del warehouse Delta locale.

Rimuove i file parquet non piu' referenziati dalla versione corrente delle tabelle
(tombstone accumulati da MERGE ripetuti). NON tocca i dati correnti.

Uso (dentro il container):
    docker compose exec spark python /workspace/code/tests/local_bronze/vacuum_warehouse.py
    # opzionale: --warehouse /workspace/data/warehouse --retain-hours 0 --dry-run

RETAIN 0 HOURS e' sicuro in locale (sessione singola, nessun lettore concorrente).
Disabilita retentionDurationCheck per consentire retention < 168h.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spark_session import build_spark  # noqa: E402


def find_delta_tables(warehouse: Path) -> list[Path]:
    """Tutte le directory tabella Delta = quelle che contengono _delta_log."""
    return sorted({p.parent for p in warehouse.rglob("_delta_log") if p.is_dir()})


def dir_size_gb(path: Path) -> float:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / 1024**3, 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--warehouse", default="/workspace/data/warehouse")
    ap.add_argument("--retain-hours", type=float, default=0.0)
    ap.add_argument("--memory-gb", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true",
                    help="VACUUM DRY RUN: elenca i file che verrebbero rimossi, senza cancellare.")
    args = ap.parse_args()

    warehouse = Path(args.warehouse).resolve()
    tables = find_delta_tables(warehouse)
    if not tables:
        print(f"Nessuna tabella Delta trovata sotto {warehouse}")
        return 0

    before_total = dir_size_gb(warehouse)
    print(f"Warehouse: {warehouse}")
    print(f"Tabelle Delta trovate: {len(tables)}")
    print(f"Dimensione totale PRIMA: {before_total} GB")
    print(f"Modalita': {'DRY RUN' if args.dry_run else f'VACUUM RETAIN {args.retain_hours}h'}")
    print("-" * 70)

    spark = build_spark(warehouse, app_name="vacuum-warehouse", memory_gb=args.memory_gb)
    if args.retain_hours < 168:
        spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

    rh = args.retain_hours
    ok, fail = 0, 0
    for tdir in tables:
        rel = str(tdir).replace(str(warehouse), "").lstrip("/\\")
        sz_before = dir_size_gb(tdir)
        path_sql = str(tdir).replace("'", "''")
        try:
            if args.dry_run:
                n = spark.sql(f"VACUUM delta.`{path_sql}` RETAIN {rh} HOURS DRY RUN").count()
                print(f"DRY  {rel:55} {sz_before:7.3f} GB  ({n} file rimovibili)")
            else:
                spark.sql(f"VACUUM delta.`{path_sql}` RETAIN {rh} HOURS")
                sz_after = dir_size_gb(tdir)
                freed = round(sz_before - sz_after, 3)
                print(f"OK   {rel:55} {sz_before:7.3f} -> {sz_after:7.3f} GB  (liberati {freed})")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {rel:55} {str(e)[:80]}")
            fail += 1

    after_total = dir_size_gb(warehouse)
    print("-" * 70)
    print(f"Dimensione totale DOPO: {after_total} GB  (liberati {round(before_total-after_total,3)} GB)")
    print(f"Tabelle OK={ok} FAIL={fail}")
    spark.stop()
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
