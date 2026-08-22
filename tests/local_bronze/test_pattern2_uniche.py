import sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parent.parent
sys.path.insert(0,str(REPO/"lib"/"logistica_utils")); sys.path.insert(0,str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
spark=build_spark("/workspace/data/warehouse",app_name="test-p2"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
NB=REPO/"notebooks/silver/prep_spedizioni/silver_storico_liste_uniche.py"
def run(full_refresh):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
    ov={"env":"dev","run_date":"2026-06-11","landing_base_path":land,"file_format":"csv","siti":"x","full_refresh":full_refresh}
    g={"__name__":"__main__","__file__":str(NB),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    t0=time.time()
    try: exec(compile(NB.read_text(encoding="utf-8"),str(NB),"exec"),g)
    except NotebookExit as e: pass
    return round(time.time()-t0,1)
def metrics(tag):
    df=spark.table("silver_dev_logistica.storico_liste_uniche")
    m=df.agg(F.count(F.lit(1)).alias("n"), F.sum("NUM_RIGHE").alias("sr"), F.sum(F.col("LSPRL_QTA_EVASA")).alias("sq")).collect()[0]
    print(f"{tag}: righe={m['n']} sum_NUM_RIGHE={m['sr']} sum_QTA_EVASA={m['sq']}",flush=True)
    return (m['n'], m['sr'], m['sq'])
print("== FULL refresh (baseline) ==",flush=True); s1=run("true"); a=metrics("FULL")
print(f"  full {s1}s",flush=True)
print("== INCREMENTALE (pattern #2) ==",flush=True); s2=run("false"); b=metrics("INCR")
print(f"  incr {s2}s",flush=True)
print("MATCH:" , "OK" if a==b else f"MISMATCH {a} vs {b}",flush=True)
spark.stop()
