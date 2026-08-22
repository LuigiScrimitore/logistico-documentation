"""
SparkSession locale con Delta Lake — per esecuzione notebook Bronze fuori da Databricks.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


# Mapping catalog Databricks -> nome database Spark locale.
# I notebook usano FQN a 3 livelli (catalog.schema.table); in locale collassiamo
# a 2 livelli (database.table) concatenando catalog_schema. Il rewrite avviene nel runner.
DB_NAMES = [
    "bronze_dev_logistica", "bronze_prod_logistica",
    "silver_dev_logistica", "silver_prod_logistica",
    "silver_dev_logistica_curated", "silver_prod_logistica_curated",  # strato preprocessing (Fase 1+2)
    # Gold: dev e prod separati e speculari (no più collassamento su gold_prod)
    "gold_dev_logistica", "gold_dev_logistica_dm",
    "gold_prod_logistica", "gold_prod_logistica_dm",
    # Control layer trasversale per ambiente: etl (watermark/log) + parametri (manuali)
    "control_dev_etl", "control_dev_parametri",
    "control_prod_etl", "control_prod_parametri",
    "cdtdw_condiviso",  # workaround LU legacy CDT_DW (in attesa OP-02 Retail Master)
]


def build_spark(warehouse_dir: str | Path, app_name: str = "logistico-bronze-local",
                memory_gb: int = 12):
    """
    SparkSession locale con DeltaCatalog su spark_catalog (default) — 2 livelli (db.table).

    Il runner pre-processa i notebook per collassare l'FQN a 3 livelli di Databricks
    (catalog.schema.table) in 2 livelli (database.table). Vedi run_notebook.py.
    """
    try:
        from pyspark.sql import SparkSession
        from delta import configure_spark_with_delta_pip
    except ImportError as e:
        raise RuntimeError(
            "PySpark/Delta non installati. Esegui:\n"
            "  py -m pip install -r tests/local_bronze/requirements.txt"
        ) from e

    warehouse = Path(warehouse_dir).resolve()
    warehouse.mkdir(parents=True, exist_ok=True)
    warehouse_uri = warehouse.as_uri()

    # Metastore Derby persistente (altrimenti Spark usa in-memory: i database spariscono)
    metastore_dir = warehouse / "_metastore_db"

    # Heap driver: env SPARK_DRIVER_MEMORY (es. "12g") ha precedenza sul param memory_gb.
    # In local[*] il driver E' anche l'executor, quindi questo e' l'unico heap che conta.
    driver_mem = os.environ.get("SPARK_DRIVER_MEMORY", f"{memory_gb}g")

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.sql.warehouse.dir", warehouse_uri)
        .config("spark.driver.memory", driver_mem)
        # Catalog implementation Hive + metastore Derby persistente
        .config("spark.sql.catalogImplementation", "hive")
        .config("javax.jdo.option.ConnectionURL",
                f"jdbc:derby:;databaseName={metastore_dir};create=true")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.merge.enableLowShuffle", "true")
        .config("spark.ui.showConsoleProgress", "false")
        # Date pre-1582 (es. watermark default 1900-01-01) -> rebase calendar mode
        # In Databricks 15.4 LTS il default va bene; in Spark 3.5 standalone serve LEGACY.
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "LEGACY")
        .config("spark.sql.parquet.int96RebaseModeInWrite", "LEGACY")
        .config("spark.sql.parquet.int96RebaseModeInRead", "LEGACY")
        .config("spark.sql.avro.datetimeRebaseModeInWrite", "LEGACY")
        .config("spark.sql.legacy.createHiveTableByDefault", "false")
        # Riduce verbosita' del logging Hive/Derby
        .config("spark.hadoop.hive.metastore.schema.verification", "false")
        .config("spark.hadoop.datanucleus.schema.autoCreateAll", "true")
    )

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Silenzia rumore Derby/Hive specifico del metastore locale.
    # In cloud (Unity Catalog) questi logger non vengono mai invocati.
    log4j = spark.sparkContext._jvm.org.apache.log4j
    log4j.Logger.getLogger("org.apache.hadoop.hive.metastore.HiveAlterHandler").setLevel(log4j.Level.FATAL)
    log4j.Logger.getLogger("org.apache.spark.sql.hive.HiveExternalCatalog").setLevel(log4j.Level.ERROR)
    log4j.Logger.getLogger("org.apache.hadoop.hive.metastore.ObjectStore").setLevel(log4j.Level.ERROR)

    return spark


def ensure_databases(spark, names: list[str] | None = None) -> None:
    """Crea i database (= catalog_schema collassati) necessari per i notebook."""
    targets = names or DB_NAMES
    for name in targets:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS `{name}`")


def reset_database(spark, name: str) -> None:
    spark.sql(f"DROP DATABASE IF EXISTS `{name}` CASCADE")
    spark.sql(f"CREATE DATABASE `{name}`")


def vacuum_all_tables(spark, warehouse_dir: str | Path, retain_hours: float = 0.0,
                      logger=None, prefixes: list[str] | None = None) -> dict:
    """Manutenzione: VACUUM delle tabelle Delta del warehouse.

    Rimuove i parquet tombstone (non piu' referenziati dalla versione corrente)
    accumulati dai MERGE/overwrite ripetuti. NON tocca i dati correnti.

    prefixes: se valorizzato (es. ["silver"]), vacuuma SOLO le tabelle nei database
    il cui nome inizia con uno dei prefissi → ogni layer pulisce il proprio
    (bronze→bronze_*, silver→silver_*, gold→gold_*). None = tutto il warehouse.

    retain_hours=0 (default LOCALE): rimuove TUTTI i tombstone, niente time-travel.
    In cloud usare la retention concordata (es. 168h = 7 giorni) impostando
    l'env AUTO_VACUUM_RETAIN_HOURS o passando il parametro.

    Sicuro in locale: sessione singola, nessun lettore concorrente.
    """
    warehouse = Path(warehouse_dir).resolve()
    tables = sorted({p.parent for p in warehouse.rglob("_delta_log") if p.is_dir()})
    if prefixes:
        tables = [t for t in tables
                  if any(t.relative_to(warehouse).parts[0].startswith(pf) for pf in prefixes)]

    def _log(msg):
        if logger:
            logger.info(msg)
        else:
            print(msg, flush=True)

    scope = ("+".join(prefixes) if prefixes else "TUTTO")
    if not tables:
        _log(f"VACUUM ({scope}): nessuna tabella Delta trovata.")
        return {"tables": 0, "ok": 0, "fail": 0}

    if retain_hours < 168:
        spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

    _log(f"VACUUM manutenzione [{scope}]: {len(tables)} tabelle | RETAIN {retain_hours}h")
    ok = fail = 0
    for tdir in tables:
        path_sql = str(tdir).replace("'", "''")
        try:
            spark.sql(f"VACUUM delta.`{path_sql}` RETAIN {retain_hours} HOURS")
            ok += 1
        except Exception as e:  # noqa: BLE001
            _log(f"VACUUM FAIL {tdir}: {str(e)[:120]}")
            fail += 1
    _log(f"VACUUM completato: OK={ok} FAIL={fail}")
    return {"tables": len(tables), "ok": ok, "fail": fail}
