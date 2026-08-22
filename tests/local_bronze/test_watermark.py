"""
Test fondamenta watermark (OP-35): control_<env>.etl.watermark + helper utils.
Valida: ensure/read/update (OK avanza, FAIL non avanza), idempotenza upsert,
pending_landing_dates (catch-up range), isolamento per-sito.
Esecuzione: docker exec logistico-spark python3 /workspace/code/tests/local_bronze/test_watermark.py
"""
import sys, logging
sys.path.insert(0, "/workspace/code/lib/logistica_utils")
sys.path.insert(0, "/workspace/code/tests/local_bronze")
logging.basicConfig(level=logging.ERROR)
from datetime import date
from spark_session import build_spark, ensure_databases
from run_notebook import _install_fqn_rewriters
import utils

ENV = "dev"
spark = build_spark("/workspace/data/warehouse", app_name="test-watermark")
ensure_databases(spark)
_install_fqn_rewriters(spark)

fails = []
def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

WM = "control_dev.etl.watermark"
spark.sql(f"DROP TABLE IF EXISTS {WM}")

# 1) ensure crea schema + tabella
utils.ensure_watermark_table(spark, ENV)
check("ensure crea tabella", spark.catalog.tableExists(WM))

# 2) read iniziale = None
check("read iniziale None",
      utils.read_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste") is None)

# 3) update OK -> avanza a 06-12
utils.update_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste", "_ALL_", "2026-06-12", 100, "OK")
check("read dopo OK = 06-12",
      utils.read_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste") == date(2026, 6, 12))

# 4) update FAIL -> NON avanza (resta 06-12), registra esito
utils.update_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste", "_ALL_", "2026-06-13", 0, "FAIL", "boom")
check("FAIL non avanza (resta 06-12)",
      utils.read_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste") == date(2026, 6, 12))

# 5) update OK -> avanza a 06-13
utils.update_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste", "_ALL_", "2026-06-13", 200, "OK")
check("read dopo OK2 = 06-13",
      utils.read_watermark(spark, ENV, "bronze_to_clean", "stat", "storico_liste") == date(2026, 6, 13))

# 6) idempotenza: una sola riga per chiave (upsert, non append)
n = spark.table(WM).where("stage='bronze_to_clean' AND sistema='stat' AND tabella='storico_liste'").count()
check("una sola riga per chiave", n == 1)

# 7) pending_landing_dates senza watermark -> tutte
avail = ["2026-06-11", "2026-06-12", "2026-06-13", "2026-06-14"]
p = utils.pending_landing_dates(spark, ENV, "stat", "storico_liste", "_ALL_", avail)
check("pending senza wm = 4", len(p) == 4)

# 8) set watermark landing 06-12 -> pending = [06-13, 06-14]
utils.update_watermark(spark, ENV, "landing_to_bronze", "stat", "storico_liste", "_ALL_", "2026-06-12", 100, "OK")
p2 = utils.pending_landing_dates(spark, ENV, "stat", "storico_liste", "_ALL_", avail)
check("pending dopo wm 06-12 = [13,14]", p2 == [date(2026, 6, 13), date(2026, 6, 14)])

# 9) isolamento per-sito (logistix multi-sito)
utils.update_watermark(spark, ENV, "landing_to_bronze", "logistix", "sto_righe_carico", "lgvx", "2026-06-13", 50, "OK")
check("sito lgvx = 06-13",
      utils.read_watermark(spark, ENV, "landing_to_bronze", "logistix", "sto_righe_carico", "lgvx") == date(2026, 6, 13))
check("sito lonx = None (isolato)",
      utils.read_watermark(spark, ENV, "landing_to_bronze", "logistix", "sto_righe_carico", "lonx") is None)

print("RESULT " + ("ALL_OK" if not fails else f"{len(fails)} FAIL: {fails}"))
spark.stop()
