import sys, time, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parent.parent
sys.path.insert(0, str(REPO/"lib"/"logistica_utils")); sys.path.insert(0, str(HERE))
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters, _file_uri
import pyspark.sql.functions as F
DATES=["2026-06-10","2026-06-11"]; SITI="laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx"
spark=build_spark("/workspace/data/warehouse",app_name="rebuild-clean"); ensure_databases(spark); _install_fqn_rewriters(spark)
land=_file_uri(Path("/workspace/data/landing"))
for t in ["silver_dev_logistica.storico_liste_clean","silver_dev_logistica.storico_bolle_clean"]:
    spark.sql(f"DROP TABLE IF EXISTS {t}"); print("dropped",t,flush=True)
NBS=["notebooks/silver/prep_spedizioni/silver_storico_liste_clean","notebooks/silver/prep_spedizioni/silver_storico_bolle_clean"]
for d in DATES:
    print(f"== {d} ==",flush=True)
    for rel in NBS:
        spark.conf.set("spark.sql.sources.partitionOverwriteMode","static")
        nb=REPO/f"{rel}.py"; ov={"env":"dev","run_date":d,"landing_base_path":land,"file_format":"csv","siti":SITI}
        g={"__name__":"__main__","__file__":str(nb),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
        t0=time.time()
        try: exec(compile(nb.read_text(encoding="utf-8"),str(nb),"exec"),g); print(f"  OK {nb.name} {round(time.time()-t0,1)}s",flush=True)
        except NotebookExit as e: print(f"  OK {nb.name} exit({e.message})",flush=True)
        except Exception as e: print(f"  FAIL {nb.name} {str(e)[:200]}",flush=True); traceback.print_exc()
for t,keys in [("storico_liste_clean",['LSPRL_SITO','LSPRL_NRO_GABBIA','LSPRL_NRO_ORDINE_NEG','LSPRL_COD_NEGOZIO','LSPRL_COD_MSI','LSPRL_DATA_ORDIN_NEG','LSPRL_SEQUE_PRELIEVO','LSPRL_FLAG_SCARTATO']),("storico_bolle_clean",['BOL_SITO','BOL_NRO_BOLLA','BOL_DATA_BOLLA','BOL_NRO_RIGA'])]:
    df=spark.table("silver_dev_logistica."+t); n=df.count(); dd=df.select(*keys).distinct().count()
    print(f"VERIFY {t}: righe={n} distinte={dd} DUP={'NO' if n==dd else 'SI('+str(n-dd)+')'}",flush=True)
spark.stop()
