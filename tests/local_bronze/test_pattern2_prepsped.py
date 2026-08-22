import sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parent.parent
sys.path.insert(0,str(REPO/"lib"/"logistica_utils")); sys.path.insert(0,str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
spark=build_spark("/workspace/data/warehouse",app_name="t-prepsped"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
NB=REPO/"notebooks/silver/prep_spedizioni/silver_prep_prep_sped.py"
def run(fr):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
    ov={"env":"dev","run_date":"2026-06-11","landing_base_path":land,"file_format":"csv","siti":"x","full_refresh":fr}
    g={"__name__":"__main__","__file__":str(NB),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    t0=time.time()
    try: exec(compile(NB.read_text(encoding="utf-8"),str(NB),"exec"),g)
    except NotebookExit as e: print("  exit",e.message,flush=True)
    return round(time.time()-t0,1)
def m(tag):
    df=spark.table("silver_dev_logistica_curated.prep_sped")
    r=df.agg(F.count(F.lit(1)).alias("n"),F.sum("NUM_RIGHE_PREP").alias("sr"),F.sum(F.col("VAL_PREP_VEN").cast("decimal(20,2)")).alias("sv")).collect()[0]
    print(f"{tag}: righe={r['n']} sum_NUM_RIGHE={r['sr']} sum_VAL_VEN={r['sv']}",flush=True); return (r['n'],r['sr'],r['sv'])
print("== FULL ==",flush=True); s1=run("true"); a=m("FULL"); print("  full",s1,"s",flush=True)
print("== INCR ==",flush=True); s2=run("false"); b=m("INCR"); print("  incr",s2,"s",flush=True)
print("MATCH:", "OK" if a==b else f"MISMATCH {a} vs {b}",flush=True)
spark.stop()
