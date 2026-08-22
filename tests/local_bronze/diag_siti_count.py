import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))
from spark_session import build_spark

s = build_spark("/workspace/data/warehouse", app_name="diag-siti-count")
for t in ["bronze_dev_logistica.struttura_mag",
          "bronze_dev_logistica.carrellisti",
          "bronze_dev_logistica.preparatori",
          "bronze_dev_logistica.aree_merceologiche"]:
    try:
        df = s.table(t)
        n = df.select("MAG_SITO_COD").distinct().count()
        vals = [r["MAG_SITO_COD"] for r in
                df.select("MAG_SITO_COD").distinct().orderBy("MAG_SITO_COD").limit(30).collect()]
        print(f"{t}: {n} siti -> {vals}")
    except Exception as e:
        print(f"{t}: ERR {str(e)[:100]}")
s.stop()
