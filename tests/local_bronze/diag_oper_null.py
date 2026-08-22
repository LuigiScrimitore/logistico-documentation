import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))
from spark_session import build_spark
from pyspark.sql import functions as F

s = build_spark("/workspace/data/warehouse", app_name="diag-oper-null")

def report(tbl, col):
    df = s.table(tbl)
    tot = df.count()
    nulls = df.filter(F.col(col).isNull() | (F.trim(F.col(col).cast("string")) == "") | (F.col(col).cast("string") == "0")).count()
    print(f"{tbl}.{col}: tot={tot} | null/empty/0={nulls} ({round(100*nulls/tot,1)}%)")
    print("  campione valori:")
    df.groupBy(F.col(col).cast('string').alias('v')).count().orderBy(F.desc('count')).show(8, False)

report("silver_dev_logistica_curated.carico", "OPERATORE_COD")
report("silver_dev_logistica_curated.turno_prep_sito", "PREPARATORE_COD")
s.stop()
