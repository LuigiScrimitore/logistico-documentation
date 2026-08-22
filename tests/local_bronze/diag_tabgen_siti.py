"""Ispeziona TABGEN per capire se esiste un master completo dei siti/CEDI."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))
from spark_session import build_spark
from pyspark.sql import functions as F

spark = build_spark("/workspace/data/warehouse", app_name="diag-tabgen")
tg = spark.table("bronze_dev_logistica.tabgen")
print("Colonne tabgen:", tg.columns)
print("\n-- TGEN_NRO_TAB distinti (campione) --")
tg.groupBy("TGEN_NRO_TAB").count().orderBy("TGEN_NRO_TAB").show(60, False)

print("\n-- Tab 7 (siti?) — campione righe --")
t7 = tg.filter("TGEN_NRO_TAB = 7")
print(f"righe tab 7: {t7.count()}")
cols = [c for c in tg.columns if c.startswith("TGEN") or c == "MAG_SITO_COD"]
t7.select(*cols[:12]).show(60, False)

print("\n-- struttura_mag: siti distinti --")
sm = spark.table("bronze_dev_logistica.struttura_mag")
sm.select("MAG_SITO_COD").distinct().orderBy("MAG_SITO_COD").show(60, False)

spark.stop()
