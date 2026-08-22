import sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parent.parent
sys.path.insert(0,str(REPO/"lib"/"logistica_utils")); sys.path.insert(0,str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
spark=build_spark("/workspace/data/warehouse",app_name="test-prune"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
NB=REPO/"notebooks/bronze/prep_spedizioni/bronze_storico_liste.py"
def run(d):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
    ov={"env":"dev","run_date":d,"landing_base_path":land,"file_format":"csv","siti":"x"}
    g={"__name__":"__main__","__file__":str(NB),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    t0=time.time()
    try: exec(compile(NB.read_text(encoding="utf-8"),str(NB),"exec"),g)
    except NotebookExit as e: print("  exit",e.message,flush=True)
    print(f"  run {d}: {round(time.time()-t0,1)}s",flush=True)
spark.sql("DROP TABLE IF EXISTS bronze_dev_logistica.storico_liste"); print("dropped bronze storico_liste",flush=True)
print("== run 06-10 (CTAS) ==",flush=True); run("2026-06-10")
print("== run 06-11 (MERGE pruning) ==",flush=True); run("2026-06-11")
df=spark.table("bronze_dev_logistica.storico_liste"); print("TOTALE bronze =",df.count(),flush=True)
for r in df.groupBy("_bronze_load_date").count().orderBy("_bronze_load_date").collect():
    print("  _bronze_load_date=%s -> %d" % (r["_bronze_load_date"], r["count"]),flush=True)
keys=["LSPRL_SITO","LSPRL_NRO_GABBIA","LSPRL_NRO_ORDINE_NEG","LSPRL_COD_NEGOZIO","LSPRL_COD_MSI","LSPRL_DATA_ORDIN_NEG","LSPRL_SEQUE_PRELIEVO","LSPRL_FLAG_SCARTATO"]
print("distinct chiavi =", df.select(*keys).distinct().count(), flush=True)
spark.stop()
