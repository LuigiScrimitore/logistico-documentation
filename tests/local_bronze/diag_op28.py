"""
Diagnostica OP-28 — orphan rate OPERATORE_COD/PREPARATORE_COD.

Confronta i codici operatore usati nei fatti (prep_sped, turno_prep_sito) con
l'anagrafica dim_operatore / LU_OPERATORE per capire se gli orfani sono:
  (A) mismatch di FORMATO (zeri iniziali, larghezza, trailing space, case)
  (B) codici realmente ASSENTI dall'anagrafica.

Esecuzione:
  docker exec logistico-spark bash -c "cd /workspace/code && python tests/local_bronze/diag_op28.py"
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from spark_session import build_spark  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

WAREHOUSE = "/workspace/data/warehouse"

# Nomi collassati a 2 livelli (vedi spark_session.DB_NAMES)
DIM_OP    = "silver_dev_logistica.dim_operatore"
LU_OP     = "gold_dev_logistica.LU_OPERATORE"

# (tabella_fatto, colonna_codice_operatore, etichetta)
FACTS = [
    ("silver_dev_logistica_curated.prep_sped",       "OPER_PREP_COD",   "prep_sped"),
    ("silver_dev_logistica_curated.turno_prep_sito", "PREPARATORE_COD", "turno_prep_sito"),
]


def sep(t):
    print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


def norm(col):
    return F.upper(F.trim(col))


def diagnose_fact(spark, table, op_col, label, dim_codes):
    sep(f"### FATTO: {label} ({table}) — colonna {op_col}")
    if not spark.catalog.tableExists(table):
        print(f"[MANCANTE] {table} — salto")
        return
    src = spark.table(table)
    if op_col not in src.columns:
        cand = [c for c in src.columns if "OPER" in c.upper() or "PREP" in c.upper()]
        print(f"[ATTENZIONE] {op_col} assente. Candidate: {cand}")
        if not cand:
            return
        op_col = cand[0]
        print(f"Uso colonna: {op_col}")

    fact_codes = (src.select(F.col(op_col).cast("string").alias("c"))
                  .filter(F.col("c").isNotNull()).distinct())
    n_fact = fact_codes.count()
    if n_fact == 0:
        print("Nessun codice operatore (fatto vuoto)")
        return
    print(f"Codici operatore distinti nel fatto: {n_fact}")

    print("-- distribuzione lunghezze codice --")
    (fact_codes.withColumn("len", F.length("c"))
        .groupBy("len").count().orderBy("len").show(50, False))

    matched = fact_codes.join(dim_codes, "c", "inner").count()
    orphan = n_fact - matched
    print(f"MATCH ESATTO    : {matched}/{n_fact} ({round(100*matched/n_fact,1)}%) | orfani {orphan} ({round(100*orphan/n_fact,1)}%)")

    fact_n = fact_codes.select(norm(F.col("c")).alias("c")).distinct()
    dim_n  = dim_codes.select(norm(F.col("c")).alias("c")).distinct()
    m2 = fact_n.join(dim_n, "c", "inner").count()
    print(f"MATCH TRIM+UPPER: {m2}/{n_fact} ({round(100*m2/n_fact,1)}%)")

    fact_z = fact_codes.select(F.regexp_replace(norm(F.col("c")), r"^0+", "").alias("c")).distinct()
    dim_z  = dim_codes.select(F.regexp_replace(norm(F.col("c")), r"^0+", "").alias("c")).distinct()
    m3 = fact_z.join(dim_z, "c", "inner").count()
    print(f"MATCH no-zeri   : {m3}/{n_fact} ({round(100*m3/n_fact,1)}%)")

    print(f"-- campione 30 codici ORFANI ({label}) --")
    fact_codes.join(dim_codes, "c", "left_anti").orderBy("c").show(30, False)


def main() -> int:
    spark = build_spark(WAREHOUSE, app_name="diag-op28")

    if not spark.catalog.tableExists(DIM_OP):
        print(f"[MANCANTE] {DIM_OP}")
        return 1

    # ── Anagrafica ──────────────────────────────────────────────────────────
    dim = spark.table(DIM_OP)
    sep("dim_operatore — conteggio per TIPO_OPERATORE")
    dim.groupBy("TIPO_OPERATORE").count().orderBy("TIPO_OPERATORE").show(50, False)
    dim_codes = dim.select(F.col("OPERATORE_COD").cast("string").alias("c")).distinct()
    print(f"Codici operatore distinti in anagrafica: {dim_codes.count()}")
    sep("dim_operatore — distribuzione lunghezze codice")
    (dim.withColumn("len", F.length(F.col("OPERATORE_COD").cast("string")))
        .groupBy("len").count().orderBy("len").show(50, False))

    # ── Fatti ────────────────────────────────────────────────────────────────
    for table, op_col, label in FACTS:
        diagnose_fact(spark, table, op_col, label, dim_codes)

    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
