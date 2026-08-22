"""
Pilota watermark bronze->clean su silver_storico_liste_clean (OP-35).
Scenario: watermark a 06-11 -> un solo run processa il delta 06-12+06-13 (catch-up),
watermark avanza a 06-13; secondo run -> NO_DATA (idempotente), watermark invariato.
"""
import sys, logging
sys.path.insert(0, "/workspace/code/lib/logistica_utils")
sys.path.insert(0, "/workspace/code/tests/local_bronze")
logging.basicConfig(level=logging.ERROR)
from pathlib import Path
from datetime import date
from dbutils_stub import DBUtilsStub, NotebookExit
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters
import utils

spark = build_spark("/workspace/data/warehouse", app_name="pilot-watermark")
ensure_databases(spark); _install_fqn_rewriters(spark)
NB = Path("/workspace/code/notebooks/silver/prep_spedizioni/silver_storico_liste_clean.py")
fails = []
def check(n, c): print(("OK   " if c else "FAIL ")+n); (fails.append(n) if not c else None)

def run_clean():
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "static")
    ov = {"env":"dev","run_date":"2026-06-13","full_refresh":"false","process_from":""}
    g = {"__name__":"__main__","__file__":str(NB),"spark":spark,"dbutils":DBUtilsStub(widget_overrides=ov),"sc":spark.sparkContext}
    try:
        exec(compile(NB.read_text(encoding="utf-8"), str(NB), "exec"), g); return "OK"
    except NotebookExit as e: return f"EXIT:{e.message}"

# Setup: watermark a 06-11 (come se avessimo processato solo fino al giorno 11)
utils.update_watermark(spark,"dev","bronze_to_clean","stat","storico_liste","_ALL_","2026-06-11",0,"OK")
check("setup watermark = 06-11", utils.read_watermark(spark,"dev","bronze_to_clean","stat","storico_liste")==date(2026,6,11))

# Run A: catch-up del delta 06-12+06-13 in UN solo run
rA = run_clean()
wmA = utils.read_watermark(spark,"dev","bronze_to_clean","stat","storico_liste")
check(f"run A processa (status={rA})", rA=="OK")
check(f"run A avanza watermark a 06-13 (={wmA})", wmA==date(2026,6,13))

# Run B: nessun dato nuovo (> 06-13) -> NO_DATA, watermark invariato
rB = run_clean()
wmB = utils.read_watermark(spark,"dev","bronze_to_clean","stat","storico_liste")
check(f"run B NO_DATA (status={rB})", rB=="EXIT:NO_DATA")
check(f"run B watermark invariato 06-13 (={wmB})", wmB==date(2026,6,13))

print("RESULT " + ("ALL_OK" if not fails else f"{len(fails)} FAIL: {fails}"))
spark.stop()
