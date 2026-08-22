"""
Utility per ispezionare lo stato delle tabelle Delta nel warehouse locale.

Mostra: database, tabelle, conteggio righe, colonne (schema), ultime righe.
Utile per validare a vista l'output di un Bronze run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))

from spark_session import build_spark  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect Delta tables in local warehouse")
    p.add_argument("--warehouse", default=r"C:/PROGETTI/LOGISTICO_DATA/data/warehouse",
                   help="Path warehouse Delta locale")
    p.add_argument("--database", default=None, help="Filtra per database (es. bronze_dev)")
    p.add_argument("--table", default=None, help="Filtra per tabella (es. sto_tes_carichi)")
    p.add_argument("--show", type=int, default=5, help="Numero righe da stampare per tabella (default 5)")
    p.add_argument("--schema", action="store_true", help="Stampa schema completo")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    spark = build_spark(args.warehouse, app_name="logistico-inspect-delta", memory_gb=2)

    try:
        databases = [r.namespace for r in spark.sql("SHOW DATABASES").collect()]
        if args.database:
            databases = [d for d in databases if d == args.database]

        for db in databases:
            tables = [r.tableName for r in spark.sql(f"SHOW TABLES IN `{db}`").collect()]
            if args.table:
                tables = [t for t in tables if t == args.table]
            if not tables:
                continue
            print(f"\n===== DATABASE: {db} =====")
            for tname in tables:
                fqn = f"`{db}`.`{tname}`"
                try:
                    df = spark.read.table(fqn)
                    cnt = df.count()
                    print(f"\n  --- {fqn} ({cnt:,} righe, {len(df.columns)} colonne) ---")
                    if args.schema:
                        df.printSchema()
                    if args.show > 0 and cnt > 0:
                        df.show(args.show, truncate=80, vertical=False)
                except Exception as e:
                    print(f"  [ERRORE] {fqn}: {e}")
    finally:
        spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
