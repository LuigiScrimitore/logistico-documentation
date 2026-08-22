"""
Diagnostica orphan SITO_COD sui fatti logistica_curated vs LU_SITO.

Verifica l'ipotesi: i fatti portano il codice sito GREZZO (LSPRL_SITO/MAG_SITO_COD),
mentre LU_SITO ha il codice CANONICO (normalize_sito -> numerico 2 cifre).
Confronta match esatto (così com'è il join attuale) vs match con normalize_sito.

  docker exec logistico-spark bash -c "cd /workspace/code && python tests/local_bronze/diag_sito.py"
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from spark_session import build_spark  # noqa: E402
from utils import normalize_sito, get_sito_alias_map  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

WAREHOUSE = "/workspace/data/warehouse"
LU_SITO   = "gold_dev_logistica.LU_SITO"
BRONZE_SCHEMA = "bronze_dev_logistica"

# (tabella_silver, colonna_sito, etichetta)
FACTS = [
    ("silver_dev_logistica_curated.carico",          "SITO_COD",     "f_carico"),
    ("silver_dev_logistica_curated.ordini",          "SITO_COD",     "f_ordini"),
    ("silver_dev_logistica_curated.prep_sped",       "MAG_SITO_COD", "f_prep_sped"),
    ("silver_dev_logistica_curated.turno_prep_sito", "SITO_COD",     "f_turno_prep_sito"),
    ("silver_dev_logistica_curated.trasporto",       "MAG_SITO_COD", "f_trasporto"),
]


def sep(t):
    print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


def main() -> int:
    spark = build_spark(WAREHOUSE, app_name="diag-sito")

    if not spark.catalog.tableExists(LU_SITO):
        print(f"[MANCANTE] {LU_SITO}")
        return 1

    amap = get_sito_alias_map(spark, BRONZE_SCHEMA)
    print(f"alias_map TABGEN: {amap}")

    lu = spark.table(LU_SITO).select(F.col("SITO_COD").cast("string").alias("c")).distinct()
    lu_codes = [r["c"] for r in lu.collect()]
    print(f"LU_SITO codici canonici ({len(lu_codes)}): {sorted(lu_codes)}")

    for table, col, label in FACTS:
        sep(f"### {label} ({table}) — colonna {col}")
        if not spark.catalog.tableExists(table):
            print(f"[MANCANTE] {table} — salto")
            continue
        src = spark.table(table)
        if col not in src.columns:
            print(f"[ATTENZIONE] {col} assente. Colonne sito candidate: "
                  f"{[c for c in src.columns if 'SITO' in c.upper()]}")
            continue

        total = src.count()
        raw = src.select(F.col(col).cast("string").alias("raw"))

        # valori grezzi distinti
        print("-- valori sito GREZZI distinti (campione) --")
        raw.select("raw").distinct().orderBy("raw").show(20, False)

        # match esatto (join attuale)
        m_raw = raw.filter(F.col("raw").isin(lu_codes)).count()
        # match con normalize_sito
        norm = src.select(normalize_sito(F.col(col), amap).alias("n"))
        m_norm = norm.filter(F.col("n").isin(lu_codes)).count()

        print(f"righe totali           : {total}")
        print(f"match GREZZO (attuale) : {m_raw}/{total} ({round(100*m_raw/total,1)}%) "
              f"-> orphan {round(100*(total-m_raw)/total,1)}%")
        print(f"match NORMALIZZATO     : {m_norm}/{total} ({round(100*m_norm/total,1)}%) "
              f"-> orphan {round(100*(total-m_norm)/total,1)}%")
        print("-- valori NORMALIZZATI distinti (campione) --")
        norm.select("n").distinct().orderBy("n").show(20, False)

    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
