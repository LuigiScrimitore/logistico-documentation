"""
Generatore Bronze notebook per le tabelle cdt_estr.

Output: notebooks/bronze/cdt_estr/bronze_<table>.py per ognuna delle 12 tabelle
del config.yaml sezione "cdt_estr".

Usa il template "stat single-source" (non multi-sito), schema-on-read (no SOURCE_COLS).
"""

from __future__ import annotations
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts" / "landing_simulator"))

import yaml

CFG = yaml.safe_load((REPO / "scripts" / "landing_simulator" / "config.yaml").read_text(encoding="utf-8"))
CDT_ESTR = CFG["systems"]["cdt_estr"]

OUT_DIR = REPO / "notebooks" / "bronze" / "cdt_estr"
OUT_DIR.mkdir(parents=True, exist_ok=True)


TEMPLATE_FULL = '''# Databricks notebook source
# Area: CDT_ESTR (migrazione TO-BE)
# Layer: Bronze
# Versione: 1.0.0
# Data: 2026-06-09
# Descrizione: Ingestion 1:1 della tabella CDT_ESTR.{TABLE_UPPER} verso Bronze Delta.
#              Sorgente: tabella materializzata dal flusso AS-IS CDT_ESTR (da dismettere).
#              MODE = {MODE}.
#              Schema-on-read (StringType) — replica fedele della struttura WL1_*/S_*.
#              Riferimento: DOCS/99. SCRIPT/CDT_ESTR_VISTE.sql + config landing simulator.

# COMMAND ----------

import sys
sys.path.insert(0, "/Workspace/Repos/logistico/logistica_utils")

from logging_helper import get_logger
from utils import get_catalog

from pyspark.sql import functions as F
from pyspark.sql.utils import AnalysisException
from datetime import date

# COMMAND ----------
# MAGIC %md #### 1. Widget standard

# COMMAND ----------

dbutils.widgets.dropdown("env", "dev", ["dev", "prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
dbutils.widgets.text("landing_base_path", "abfss://logistica@<storage>.dfs.core.windows.net", "Landing base path")
dbutils.widgets.text("file_format", "auto", "csv | parquet | auto")

env               = dbutils.widgets.get("env")
run_date          = dbutils.widgets.get("run_date")
landing_base_path = dbutils.widgets.get("landing_base_path").rstrip("/")
file_format       = dbutils.widgets.get("file_format").strip().lower()

# COMMAND ----------
# MAGIC %md #### 2. Parametri specifici del notebook

# COMMAND ----------

NOTEBOOK_NAME  = "bronze_{TABLE}"
SOURCE_SYSTEM  = "cdt_estr"
TABLE_NAME     = "{TABLE}"
MODE           = "{MODE}"

# Schema-on-read: tutte le colonne come StringType, struttura completa della WL1/S_.
SOURCE_COLS = []  # estrae tutto

TARGET_CATALOG = get_catalog("bronze", env)
TARGET_SCHEMA  = "logistica"
FULL_TARGET    = f"{{TARGET_CATALOG}}.{{TARGET_SCHEMA}}.{{TABLE_NAME}}"

logger = get_logger(NOTEBOOK_NAME)
year, month, day = run_date.split("-")

# COMMAND ----------
# MAGIC %md #### 3. Costruzione path landing (cdt-estr-landing/{TABLE})

# COMMAND ----------

def landing_path():
    return f"{{landing_base_path}}/cdt-estr-landing/{{TABLE_NAME}}/{{year}}/{{month}}/{{day}}/"

def detect_format(path):
    if file_format != "auto":
        return file_format
    try:
        for f in dbutils.fs.ls(path):
            if f.name.endswith(".parquet"):
                return "parquet"
            if f.name.endswith(".csv"):
                return "csv"
    except Exception:
        pass
    return "csv"

def read_one(path):
    fmt = detect_format(path)
    if fmt == "parquet":
        return spark.read.format("parquet").load(path)
    return (spark.read.option("header", "true").option("inferSchema", "false")
            .option("sep", ";").option("encoding", "UTF-8").csv(f"{{path}}*.csv"))

# COMMAND ----------
# MAGIC %md #### 4. Lettura (unitaria, dato grezzo)

# COMMAND ----------

logger.info(f"START {{NOTEBOOK_NAME}} | env={{env}} | run_date={{run_date}} | MODE={{MODE}}")

path = landing_path()
try:
    raw_df = read_one(path)
    logger.info(f"Letto: {{path}}")
except AnalysisException:
    logger.warning(f"File non trovato in landing per la run_date: {{path}} — terminato.")
    dbutils.notebook.exit("NO_DATA")

# COMMAND ----------
# MAGIC %md #### 5. Metadati Bronze

# COMMAND ----------

bronze_df = (
    raw_df
    .withColumn("_bronze_load_date", F.lit(run_date).cast("date"))
    .withColumn("_bronze_insert_ts", F.current_timestamp())
    .withColumn("_source_file", F.input_file_name())
)

rows_read = bronze_df.count()
logger.info(f"Righe lette: {{rows_read}}")
if rows_read == 0:
    logger.warning("Nessuna riga in landing per la run_date. Notebook terminato.")
    dbutils.notebook.exit("NO_DATA")

# COMMAND ----------
# MAGIC %md #### 6. Scrittura {WRITE_DESC}

# COMMAND ----------

{WRITE_BLOCK}

logger.info(f"END {{NOTEBOOK_NAME}} | righe_processate={{rows_read}}")
'''

WRITE_BLOCK_FULL = """(bronze_df.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true").saveAsTable(FULL_TARGET))
logger.info(f"FULL OVERWRITE {FULL_TARGET} ({rows_read} righe)")"""

WRITE_BLOCK_SNAPSHOT = """# SNAPSHOT: scrittura partizionata per _bronze_load_date (storico giornaliero).
(bronze_df.write.format("delta").mode("append")
 .partitionBy("_bronze_load_date").option("mergeSchema", "true")
 .saveAsTable(FULL_TARGET))
logger.info(f"SNAPSHOT append {FULL_TARGET} ({rows_read} righe per run_date={run_date})")"""

WRITE_BLOCK_DELTA_MERGE = """from delta.tables import DeltaTable

MERGE_KEYS = {MERGE_KEYS_LIST}  # da config landing

if not spark.catalog.tableExists(FULL_TARGET):
    (bronze_df.write.format("delta").mode("overwrite")
     .option("overwriteSchema", "true").saveAsTable(FULL_TARGET))
    logger.info(f"Creazione iniziale {FULL_TARGET} ({rows_read} righe)")
else:
    tgt = DeltaTable.forName(spark, FULL_TARGET)
    cond = " AND ".join([f"tgt.{k} = src.{k}" for k in MERGE_KEYS])
    (tgt.alias("tgt").merge(bronze_df.alias("src"), cond)
        .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
    logger.info(f"MERGE INTO {FULL_TARGET} completato")"""


def render_notebook(tname: str, tspec: dict) -> str:
    mode_raw = (tspec.get("mode") or "full").lower()
    mode_map = {"full": "FULL_OVERWRITE", "snapshot": "SNAPSHOT", "delta": "DELTA_MERGE"}
    mode = mode_map[mode_raw]

    if mode == "FULL_OVERWRITE":
        wblock = WRITE_BLOCK_FULL
        wdesc = "FULL_OVERWRITE (stato corrente)"
    elif mode == "SNAPSHOT":
        wblock = WRITE_BLOCK_SNAPSHOT
        wdesc = "SNAPSHOT (append partizionato per data)"
    else:
        merge_keys = tspec.get("merge_keys") or []
        wblock = WRITE_BLOCK_DELTA_MERGE.replace("{MERGE_KEYS_LIST}", repr(merge_keys))
        wdesc = "DELTA_MERGE (incrementale via MERGE INTO)"

    return TEMPLATE_FULL.format(
        TABLE=tname,
        TABLE_UPPER=tname.upper(),
        MODE=mode,
        WRITE_BLOCK=wblock,
        WRITE_DESC=wdesc,
    )


def main() -> int:
    created = []
    for tname, tspec in CDT_ESTR["tables"].items():
        if tspec.get("disabled"):
            print(f"  SKIP {tname} (disabled)")
            continue
        out_file = OUT_DIR / f"bronze_{tname}.py"
        content = render_notebook(tname, tspec)
        out_file.write_text(content, encoding="utf-8")
        created.append(out_file)
        print(f"  WROTE {out_file.relative_to(REPO)}")
    print(f"\nTotale: {len(created)} notebook generati in {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
