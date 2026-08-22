"""Diagnostica #3 — orphan f_carico OPERATORE_COD (STCAR_COD_OPERATORE) vs LU_OPERATORE."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))
from spark_session import build_spark
from pyspark.sql import functions as F

s = build_spark("/workspace/data/warehouse", app_name="diag-carico-oper")

dimc = s.table("silver_dev_logistica.dim_operatore")
dim = dimc.select(F.col("OPERATORE_COD").cast("string").alias("c")).distinct()
print("dim_operatore per tipo:")
dimc.groupBy("TIPO_OPERATORE").count().orderBy("TIPO_OPERATORE").show(20, False)

car = s.table("silver_dev_logistica_curated.carico")
fc = car.select(F.col("OPERATORE_COD").cast("string").alias("c")).filter(F.col("c").isNotNull()).distinct()
n = fc.count()
print(f"\ncarico OPERATORE_COD distinti: {n}")
print("-- distribuzione lunghezze --")
fc.withColumn("len", F.length("c")).groupBy("len").count().orderBy("len").show(20, False)

def norm(c): return F.upper(F.trim(c))
m_raw = fc.join(dim, "c", "inner").count()
m_n = fc.select(norm(F.col("c")).alias("c")).distinct().join(dim.select(norm(F.col("c")).alias("c")).distinct(), "c", "inner").count()
fz = fc.select(F.regexp_replace(norm(F.col("c")), r"^0+", "").alias("c")).distinct()
dz = dim.select(F.regexp_replace(norm(F.col("c")), r"^0+", "").alias("c")).distinct()
m_z = fz.join(dz, "c", "inner").count()
print(f"MATCH ESATTO    : {m_raw}/{n} ({round(100*m_raw/n,1)}%)")
print(f"MATCH TRIM+UPPER: {m_n}/{n} ({round(100*m_n/n,1)}%)")
print(f"MATCH no-zeri   : {m_z}/{n} ({round(100*m_z/n,1)}%)")

print("\n-- 30 codici ORFANI --")
fc.join(dim, "c", "left_anti").orderBy("c").show(30, False)

# gli orfani esistono in qualche anagrafica bronze specifica?
for t, col in [("carrellisti","CRLLS_COD_CARRELLIST"), ("preparatori","PREP_COD_PREPARATOR"),
               ("ricevitori","RICV_COD_RICEVITOR"), ("spedizionieri","SPE_CODICE")]:
    codes = s.table(f"bronze_dev_logistica.{t}").select(F.col(col).cast("string").alias("c")).distinct()
    inter = fc.join(dim, "c", "left_anti").join(codes, "c", "inner").count()
    print(f"orfani presenti in bronze {t}: {inter}")

s.stop()
