"""
Runner per eseguire un notebook Bronze in locale (fuori da Databricks).

Cosa fa:
  1. Avvia una SparkSession locale con Delta Lake.
  2. Crea i database bronze_dev / silver_dev / gold_prod nel metastore Spark.
  3. Monkey-patch dell'import 'utils' (logistica_utils) e di 'logging_helper'
     per evitare la dipendenza dal path Databricks /Workspace/Repos/...
  4. Inietta nel namespace del notebook: spark, dbutils, sc.
  5. Esegue il notebook come modulo Python (i marker '# COMMAND ----------' e
     '# MAGIC %md' sono commenti Python validi, quindi vengono semplicemente ignorati).
  6. Cattura `dbutils.notebook.exit("...")` come terminazione regolare.

Uso:
    py tests/local_bronze/run_notebook.py \
        --notebook notebooks/bronze/carichi/bronze_carichi_testate.py \
        --run-date 2026-06-09

Per gli override widget si possono passare coppie --set widget=value:
    py tests/local_bronze/run_notebook.py --notebook ... --set siti=lgax,lgcx
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import sys
import traceback
from datetime import date
from pathlib import Path

# Setup path: aggiunge il root del repo e la libreria utils al sys.path,
# cosi' i notebook che fanno "from utils import get_catalog" funzionano.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from dbutils_stub import DBUtilsStub, NotebookExit  # noqa: E402
from spark_session import build_spark, ensure_databases  # noqa: E402


# ─── Default per test locale ────────────────────────────────────────────────

DEFAULT_DATA_ROOT = Path(r"C:/PROGETTI/LOGISTICO_DATA/data")
DEFAULT_LANDING = DEFAULT_DATA_ROOT / "landing"
DEFAULT_WAREHOUSE = DEFAULT_DATA_ROOT / "warehouse"

logger = logging.getLogger("run_notebook")


def _file_uri(p: Path) -> str:
    """Pathlib -> file:///C:/... (Windows-safe per Spark)."""
    return p.resolve().as_uri()


# NB: niente punto finale nelle chiavi, cosi' il rewrite copre sia i riferimenti
# a tabella (catalog.schema.table -> catalog_schema.table) sia i comandi DDL di
# namespace (CREATE SCHEMA catalog.schema -> CREATE SCHEMA catalog_schema).
# L'ordine conta: le forme piu' lunghe (logistica_dm) PRIMA di quelle piu' corte
# (logistica), altrimenti "logistica" verrebbe consumato come prefisso.
_FQN_MAP = [
    ("bronze_dev.logistica",   "bronze_dev_logistica"),
    ("bronze_prod.logistica",  "bronze_prod_logistica"),
    ("silver_dev.logistica_curated",  "silver_dev_logistica_curated"),   # piu' specifico, prima di .logistica
    ("silver_prod.logistica_curated", "silver_prod_logistica_curated"),
    ("silver_dev.logistica",   "silver_dev_logistica"),
    ("silver_prod.logistica",  "silver_prod_logistica"),
    ("gold_dev.logistica_dm",  "gold_dev_logistica_dm"),   # piu' specifico, prima di logistica
    ("gold_dev.logistica",     "gold_dev_logistica"),
    ("gold_prod.logistica_dm", "gold_prod_logistica_dm"),  # piu' specifico, prima di logistica
    ("gold_prod.logistica",    "gold_prod_logistica"),
    ("gold_prod.condiviso",    "gold_prod_condiviso"),
    ("bronze_dev.condiviso",  "bronze_dev_condiviso"),      # D2: anagrafiche LU_* nel nostro schema isolato
    ("bronze_prod.condiviso", "bronze_prod_condiviso"),
    # Control layer trasversale per ambiente (D1: config_dev nel DWH, non control_dev)
    ("config_dev.etl",        "config_dev_etl"),
    ("config_dev.parametri",  "config_dev_parametri"),
    ("config_prod.etl",       "config_prod_etl"),
    ("config_prod.parametri", "config_prod_parametri"),
]


def _rewrite_fqn(name_or_sql) -> str:
    """Collassa FQN a 3 livelli in 2 livelli per il metastore locale."""
    if not isinstance(name_or_sql, str):
        return name_or_sql
    out = name_or_sql
    for src, dst in _FQN_MAP:
        out = out.replace(src, dst)
    return out


def _install_fqn_rewriters(spark) -> None:
    """
    Monkey-patch globale di tutti i punti API che ricevono un FQN, per riscrivere
    catalog.schema.table -> catalog_schema.table al volo. Trasparente al notebook.

    API patchate:
      - SparkSession.sql              (DDL/DML inline come CREATE SCHEMA, MERGE)
      - SparkSession.table            (read.table)
      - DataFrameReader.table
      - DataFrameWriter.saveAsTable
      - DataFrameWriterV2.using (v2 API)
      - Catalog.tableExists
      - DeltaTable.forName            (libreria delta)
    """
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.readwriter import DataFrameReader, DataFrameWriter
    from pyspark.sql.catalog import Catalog

    if getattr(spark, "_fqn_rewriter_installed", False):
        return  # idempotente

    # SparkSession.sql
    orig_sql = SparkSession.sql
    def new_sql(self, sqlQuery, *args, **kwargs):
        return orig_sql(self, _rewrite_fqn(sqlQuery), *args, **kwargs)
    SparkSession.sql = new_sql

    # SparkSession.table (alias spark.table(...))
    orig_session_table = SparkSession.table
    def new_session_table(self, tableName):
        return orig_session_table(self, _rewrite_fqn(tableName))
    SparkSession.table = new_session_table

    # DataFrameReader.table
    orig_reader_table = DataFrameReader.table
    def new_reader_table(self, tableName):
        return orig_reader_table(self, _rewrite_fqn(tableName))
    DataFrameReader.table = new_reader_table

    # DataFrameWriter.saveAsTable
    orig_save = DataFrameWriter.saveAsTable
    def new_save(self, name, *args, **kwargs):
        return orig_save(self, _rewrite_fqn(name), *args, **kwargs)
    DataFrameWriter.saveAsTable = new_save

    # DataFrameWriter.insertInto
    orig_insert = DataFrameWriter.insertInto
    def new_insert(self, tableName, *args, **kwargs):
        return orig_insert(self, _rewrite_fqn(tableName), *args, **kwargs)
    DataFrameWriter.insertInto = new_insert

    # Catalog.tableExists
    orig_te = Catalog.tableExists
    def new_te(self, tableName, dbName=None):
        return orig_te(self, _rewrite_fqn(tableName), dbName)
    Catalog.tableExists = new_te

    # DeltaTable.forName
    try:
        from delta.tables import DeltaTable
        orig_fn = DeltaTable.forName
        def new_fn(sparkSession, identifier):
            return orig_fn(sparkSession, _rewrite_fqn(identifier))
        DeltaTable.forName = staticmethod(new_fn)
    except ImportError:
        pass

    spark._fqn_rewriter_installed = True


def run_notebook(notebook_path: Path,
                 spark,
                 dbutils: DBUtilsStub) -> int:
    """Esegue il notebook come script Python con spark/dbutils iniettati."""
    if not notebook_path.exists():
        logger.error("Notebook non trovato: %s", notebook_path)
        return 2

    # Installa i rewriter FQN (idempotente)
    _install_fqn_rewriters(spark)

    code = notebook_path.read_text(encoding="utf-8-sig")  # -sig: tollera BOM UTF-8
    # Iniezione globale: rendiamo disponibili spark, dbutils, sc
    g: dict = {
        "__name__": "__main__",
        "__file__": str(notebook_path),
        "spark": spark,
        "dbutils": dbutils,
        "sc": spark.sparkContext,
    }
    try:
        exec(compile(code, str(notebook_path), "exec"), g)
    except NotebookExit as e:
        logger.info("Notebook terminato regolarmente: dbutils.notebook.exit(%r)", e.message)
        return 0
    except Exception:
        logger.error("ERRORE durante l'esecuzione del notebook:\n%s", traceback.format_exc())
        return 1
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a Bronze notebook locally (no Databricks)")
    p.add_argument("--notebook", required=True, help="Path al notebook Bronze da eseguire")
    p.add_argument("--run-date", default=str(date.today()), help="Override widget run_date")
    p.add_argument("--env", default="dev", help="Override widget env (dev|prod)")
    p.add_argument("--landing", default=str(DEFAULT_LANDING),
                   help=f"Cartella landing locale (default: {DEFAULT_LANDING})")
    p.add_argument("--warehouse", default=str(DEFAULT_WAREHOUSE),
                   help=f"Cartella warehouse Delta locale (default: {DEFAULT_WAREHOUSE})")
    # Default = tutti i 22 siti attivi (allineato a CDT_ESTR.S_LOGISTIX / config.yaml dblinks),
    # cosi' i run locali sono rappresentativi come in produzione. Override con --siti per subset.
    p.add_argument("--siti",
                   default="laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx",
                   help="Override widget siti (Logistix multi-sito; default = 22 siti attivi)")
    p.add_argument("--file-format", default="csv",
                   help="Override widget file_format (default csv per il test, auto rileva)")
    p.add_argument("--set", action="append", default=[],
                   help="Override widget arbitrario: --set NOME=VALORE (ripetibile)")
    p.add_argument("--memory-gb", type=int, default=4, help="Memoria driver Spark (default 4 GB)")
    p.add_argument("--keep-spark-alive", action="store_true",
                   help="Mantiene attiva la SparkSession (utile in script multi-notebook)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    nb_path = (REPO_ROOT / args.notebook) if not Path(args.notebook).is_absolute() else Path(args.notebook)
    logger.info("Notebook: %s", nb_path)
    logger.info("Run date: %s | env: %s", args.run_date, args.env)
    logger.info("Landing : %s", args.landing)
    logger.info("Warehouse: %s", args.warehouse)

    # Spark
    spark = build_spark(args.warehouse, memory_gb=args.memory_gb)
    # Database (usa DB_NAMES = catalog_schema collassati per il metastore locale)
    ensure_databases(spark)

    # Costruisci override widget
    overrides = {
        "env": args.env,
        "run_date": args.run_date,
        "landing_base_path": _file_uri(Path(args.landing)),
        "file_format": args.file_format,
        "siti": args.siti,
    }
    for kv in args.set:
        if "=" not in kv:
            logger.error("--set deve essere NOME=VALORE, ricevuto %r", kv)
            return 2
        k, v = kv.split("=", 1)
        overrides[k.strip()] = v

    dbutils = DBUtilsStub(widget_overrides=overrides)

    # Run
    try:
        return run_notebook(nb_path, spark, dbutils)
    finally:
        if not args.keep_spark_alive:
            spark.stop()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
