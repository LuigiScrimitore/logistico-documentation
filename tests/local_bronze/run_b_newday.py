import sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent; REPO=HERE.parent.parent
sys.path.insert(0,str(REPO/"lib"/"logistica_utils")); sys.path.insert(0,str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
SITI="laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx"
spark=build_spark("/workspace/data/warehouse",app_name="run-b"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
DROPS=["bronze_dev_logistica.storico_liste","bronze_dev_logistica.storico_bolle",
       "bronze_dev_logistica.testate_bolle","bronze_dev_logistica.storico_riepiloghi",
       "silver_dev_logistica.storico_liste_clean","silver_dev_logistica.storico_bolle_clean",
       "silver_dev_logistica.storico_liste_uniche","silver_dev_logistica.storico_bolle_uniche",
       "silver_dev_logistica.prep_riepilogo","silver_dev_logistica_curated.prep_sped"]
NBS=[("bronze","notebooks/bronze/prep_spedizioni/bronze_storico_liste"),
     ("bronze","notebooks/bronze/prep_spedizioni/bronze_prep_bolle_righe"),
     ("bronze","notebooks/bronze/prep_spedizioni/bronze_prep_bolle_testate"),
     ("bronze","notebooks/bronze/prep_spedizioni/bronze_prep_riepiloghi"),
     ("clean","notebooks/silver/prep_spedizioni/silver_storico_liste_clean"),
     ("clean","notebooks/silver/prep_spedizioni/silver_storico_bolle_clean"),
     ("clean","notebooks/silver/prep_spedizioni/silver_prep_riepiloghi"),
     ("uniche","notebooks/silver/prep_spedizioni/silver_storico_liste_uniche"),
     ("uniche","notebooks/silver/prep_spedizioni/silver_storico_bolle_uniche"),
     ("prep","notebooks/silver/prep_spedizioni/silver_prep_prep_sped")]
def run(rel,d):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
    nb=REPO/f"{rel}.py"; ov={"env":"dev","run_date":d,"landing_base_path":land,"file_format":"csv","siti":SITI}
    g={"__name__":"__main__","__file__":str(nb),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    t0=time.time()
    try: exec(compile(nb.read_text(encoding="utf-8"),str(nb),"exec"),g); st="OK"
    except NotebookExit as e: st=f"exit({e.message})"
    except Exception as e: st="FAIL:"+str(e)[:120]
    return round(time.time()-t0,1),st
print("=== DROP ===",flush=True)
for t in DROPS: spark.sql(f"DROP TABLE IF EXISTS {t}")
print("dropped",len(DROPS),flush=True)
timings={}
for d in ["2026-06-10","2026-06-11"]:
    print(f"=== GIORNO {d} ===",flush=True)
    for ph,rel in NBS:
        s,st=run(rel,d); timings[(d,rel.split('/')[-1])]=s
        print(f"  [{d}] {rel.split('/')[-1]:32} {s:8.1f}s  {st}",flush=True)
print("=== PRUNING bronze (storico_liste / storico_bolle) ===",flush=True)
for t in ["storico_liste","storico_bolle"]:
    df=spark.table("bronze_dev_logistica."+t); tot=df.count()
    by={r['_bronze_load_date']:r['count'] for r in df.groupBy("_bronze_load_date").count().collect()}
    d11=by.get(__import__('datetime').date(2026,6,11),0)
    print(f"  {t}: TOT={tot}  06-11_ridatate={d11}  ({round(100*d11/max(tot,1),1)}%)",flush=True)
print("=== SPEEDUP day2/day1 per notebook ===",flush=True)
for ph,rel in NBS:
    n=rel.split('/')[-1]; t1=timings.get(("2026-06-10",n),0); t2=timings.get(("2026-06-11",n),0)
    print(f"  {n:32} day1={t1:7.1f}s  day2={t2:7.1f}s  ratio={round(t2/max(t1,0.1),2)}",flush=True)
print("=== B DONE ===",flush=True)
spark.stop()
