import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))
from spark_session import build_spark
from utils import get_sito_alias_map

s = build_spark("/workspace/data/warehouse", app_name="diag-lusito")
print("alias_map (da tabgen):", get_sito_alias_map(s, "bronze_dev_logistica"))
lu = [r["SITO_COD"] for r in s.table("gold_dev_logistica.LU_SITO")
      .select("SITO_COD").distinct().orderBy("SITO_COD").collect()]
print(f"LU_SITO ({len(lu)}):", lu)
# siti usati dall'attivita'
act = [r["MAG_SITO_COD"] for r in s.table("silver_dev_logistica_curated.prep_sped")
       .select("MAG_SITO_COD").distinct().orderBy("MAG_SITO_COD").collect()]
print(f"attivita prep_sped ({len(act)}):", act)
print("attivita NON in LU_SITO:", sorted(set(act) - set(lu)))
s.stop()
