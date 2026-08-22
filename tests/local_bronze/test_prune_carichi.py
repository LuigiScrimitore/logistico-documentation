import sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parent.parent
sys.path.insert(0,str(REPO/"lib"/"logistica_utils")); sys.path.insert(0,str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
SITI="laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx"
spark=build_spark("/workspace/data/warehouse",app_name="prune-carichi"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
NB=REPO/"notebooks/bronze/carichi/bronze_carichi_testate.py"
def run(d):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
    ov={"env":"dev","run_date":d,"landing_base_path":land,"file_format":"csv","siti":SITI}
    g={"__name__":"__main__","__file__":str(NB),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    try: exec(compile(NB.read_text(encoding="utf-8"),str(NB),"exec"),g)
    except NotebookExit as e: print("  exit",e.message,flush=True)
spark.sql("DROP TABLE IF EXISTS bronze_dev_logistica.sto_tes_carichi"); print("dropped",flush=True)
print("== 06-10 CTAS ==",flush=True); run("2026-06-10")
print("== 06-11 MERGE prune ==",flush=True); run("2026-06-11")
# nome tabella target: leggo da catalogo (potrebbe essere sto_tes_carichi o carichi_testate)
for t in ["sto_tes_carichi","carichi_testate","testate_carico"]:
    if spark.catalog.tableExists("bronze_dev_logistica."+t):
        df=spark.table("bronze_dev_logistica."+t); print("TARGET=",t,"TOT=",df.count(),flush=True)
        for r in df.groupBy("_bronze_load_date").count().orderBy("_bronze_load_date").collect():
            print("  %s -> %d" % (r["_bronze_load_date"], r["count"]),flush=True)
        k=["MAG_SITO_COD","STCAR_NRO_CARICO","STCAR_COD_MAGAZZINO"]
        print("  distinct_keys=",df.select(*k).distinct().count(),flush=True)
        break
spark.stop()
