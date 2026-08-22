"""
Rebuild mirato prep_spedizioni dopo il fix lettura-per-header + null-safe MERGE.
Drop delle tabelle bronze/clean coinvolte -> re-ingest bronze + clean per 06-10 e 06-11
(CTAS giorno 1 -> MERGE upsert giorno 2 = una copia) -> uniche/prep -> verifica no-dup.
Throwaway: eseguibile piu' volte (idempotente).
"""
from __future__ import annotations
import sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from dbutils_stub import DBUtilsStub, NotebookExit  # noqa: E402
from spark_session import build_spark, ensure_databases  # noqa: E402
from run_notebook import _install_fqn_rewriters, _file_uri  # noqa: E402
import pyspark.sql.functions as F  # noqa: E402

DATES = ["2026-06-10", "2026-06-11"]
SITI_22 = ("laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,"
           "lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx")
LANDING = "/workspace/data/landing"
WAREHOUSE = "/workspace/data/warehouse"

# Drop critici: bronze (forza CTAS schema corretto by-header) + clean (forza CTAS pulito).
DROPS = [
    "bronze_dev_logistica.storico_bolle", "bronze_dev_logistica.testate_bolle",
    "bronze_dev_logistica.storico_riepiloghi",
    "silver_dev_logistica.storico_bolle_clean", "silver_dev_logistica.storico_liste_clean",
]
# Ordine per giorno: bronze (3) -> clean (2) -> prep_riepilogo -> uniche (2)
NBS = [
    "notebooks/bronze/prep_spedizioni/bronze_prep_bolle_righe",
    "notebooks/bronze/prep_spedizioni/bronze_prep_bolle_testate",
    "notebooks/bronze/prep_spedizioni/bronze_prep_riepiloghi",
    "notebooks/silver/prep_spedizioni/silver_storico_liste_clean",
    "notebooks/silver/prep_spedizioni/silver_storico_bolle_clean",
    "notebooks/silver/prep_spedizioni/silver_prep_riepiloghi",
    "notebooks/silver/prep_spedizioni/silver_storico_liste_uniche",
    "notebooks/silver/prep_spedizioni/silver_storico_bolle_uniche",
]


def run_one(nb_rel, spark, landing_uri, run_date):
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "static")
    nb = REPO_ROOT / f"{nb_rel}.py"
    overrides = {"env": "dev", "run_date": run_date, "landing_base_path": landing_uri,
                 "file_format": "csv", "siti": SITI_22}
    g = {"__name__": "__main__", "__file__": str(nb), "spark": spark,
         "dbutils": DBUtilsStub(widget_overrides=overrides), "sc": spark.sparkContext}
    start = time.time()
    try:
        exec(compile(nb.read_text(encoding="utf-8"), str(nb), "exec"), g)
        st = "OK"; err = ""
    except NotebookExit as e:
        st = "OK"; err = f" exit({e.message!r})"
    except Exception as e:
        st = "FAIL"; err = " " + str(e)[:200]; traceback.print_exc()
    print(f"  [{st}] {nb.name} ({round(time.time()-start,1)}s){err}", flush=True)


def main():
    spark = build_spark(WAREHOUSE, app_name="rebuild-prep-sped")
    ensure_databases(spark)
    _install_fqn_rewriters(spark)
    landing_uri = _file_uri(Path(LANDING))

    print("===== DROP tabelle coinvolte =====", flush=True)
    for t in DROPS:
        spark.sql(f"DROP TABLE IF EXISTS {t}")
        print(f"  dropped {t}", flush=True)

    for d in DATES:
        print(f"\n===== REBUILD run_date={d} =====", flush=True)
        for nb in NBS:
            run_one(nb, spark, landing_uri, d)

    print("\n===== VERIFICA NO-DUP =====", flush=True)
    checks = [
        ("storico_liste_clean", ["LSPRL_SITO", "LSPRL_NRO_GABBIA", "LSPRL_NRO_ORDINE_NEG",
                                 "LSPRL_COD_NEGOZIO", "LSPRL_COD_MSI", "LSPRL_DATA_ORDIN_NEG",
                                 "LSPRL_SEQUE_PRELIEVO", "LSPRL_FLAG_SCARTATO"]),
        ("storico_bolle_clean", ["BOL_SITO", "BOL_NRO_BOLLA", "BOL_DATA_BOLLA", "BOL_NRO_RIGA"]),
    ]
    for t, keys in checks:
        df = spark.table("silver_dev_logistica." + t)
        n = df.count(); dd = df.select(*keys).distinct().count()
        nulls = df.filter(F.col(keys[-1]).isNull()).count() if t == "storico_bolle_clean" else -1
        dup = "NO" if n == dd else f"SI({n-dd})"
        extra = f" BOL_NRO_RIGA_nulls={nulls}" if nulls >= 0 else ""
        print(f"  {t}: righe={n} distinte={dd} DUP={dup}{extra}", flush=True)
    spark.stop()


if __name__ == "__main__":
    main()
