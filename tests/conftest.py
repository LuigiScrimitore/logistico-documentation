"""
conftest.py — Fixture condivise per la test suite di Logistico 2.0.

Fornisce:
- spark: SparkSession locale con Delta Lake extension
- mock_dbutils: mock di dbutils.secrets / dbutils.widgets
- sample_carichi_df: 100 righe di carichi realistici
- sample_dim_fornitore: dimensione fornitore di test
- sample_dim_articolo: dimensione articolo di test
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import Generator
from unittest.mock import MagicMock

import pytest
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# ---------------------------------------------------------------------------
# Aggiungi il path della libreria al sys.path
# ---------------------------------------------------------------------------
_LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lib")
if _LIB_PATH not in sys.path:
    sys.path.insert(0, _LIB_PATH)


# ---------------------------------------------------------------------------
# SparkSession con Delta Lake
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def spark() -> Generator[SparkSession, None, None]:
    """
    SparkSession locale con Delta Lake extension abilitata.

    Scope "session" per riusare la stessa sessione in tutti i test
    (avvio JVM costoso).
    """
    warehouse_dir = os.path.join(os.path.dirname(__file__), "_spark_warehouse")
    builder = (
        SparkSession.builder
        .master("local[2]")
        .appName("logistica_utils_tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.warehouse.dir", warehouse_dir)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "4")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "2g")
        # Evita log verbosi in output test
        .config("spark.sql.adaptive.enabled", "false")
    )
    # I config sopra dichiarano estensione e catalog Delta, ma NON mettono i jar
    # sul classpath: senza questo passo si ha ClassNotFoundException su DeltaCatalog.
    # configure_spark_with_delta_pip imposta spark.jars.packages e risolve dalla
    # cache ivy pre-popolata nel Dockerfile (offline).
    spark_local = configure_spark_with_delta_pip(builder).getOrCreate()
    spark_local.sparkContext.setLogLevel("ERROR")
    yield spark_local
    spark_local.stop()


# ---------------------------------------------------------------------------
# Mock dbutils
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_dbutils() -> MagicMock:
    """
    Mock completo di dbutils per test locali senza ambiente Databricks.

    Preimposta i segreti usati nei test con valori fittizi.
    """
    dbutils = MagicMock()

    # Mappa segreti: scope → key → value
    _secrets: dict = {
        "logistica-kv": {
            "oracle-logistica-jdbc-url": "jdbc:oracle:thin:@//test-host:1521/LOGISTICA",
            "oracle-logistica-jdbc-user": "test_user",
            "oracle-logistica-jdbc-password": "test_password_123",
        }
    }

    def _get_secret(scope: str, key: str) -> str:
        try:
            return _secrets[scope][key]
        except KeyError:
            raise Exception(f"Secret not found: scope={scope}, key={key}")

    dbutils.secrets.get.side_effect = _get_secret
    dbutils.widgets.get.return_value = ""
    return dbutils


# ---------------------------------------------------------------------------
# DataFrame campione: Carichi Testate
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_carichi_df(spark: SparkSession):
    """
    DataFrame campione con 100 righe di carichi logistici.

    Schema:
        CARICO_ID       LONG        (chiave, 1-100)
        DATA_CARICO     DATE
        FORNITORE_ID    INT
        ART_ID          INT
        PESO_NETTO      DECIMAL(18,4)
        PESO_LORDO      DECIMAL(18,4)
        QTA_RICEVUTA    DECIMAL(18,4)
    """
    schema = StructType([
        StructField("CARICO_ID", LongType(), nullable=False),
        StructField("DATA_CARICO", DateType(), nullable=False),
        StructField("FORNITORE_ID", IntegerType(), nullable=True),
        StructField("ART_ID", IntegerType(), nullable=True),
        StructField("PESO_NETTO", DecimalType(18, 4), nullable=True),
        StructField("PESO_LORDO", DecimalType(18, 4), nullable=True),
        StructField("QTA_RICEVUTA", DecimalType(18, 4), nullable=True),
    ])

    base_date = date(2026, 1, 1)
    rows = []
    for i in range(1, 101):
        rows.append((
            i,                                              # CARICO_ID
            base_date + timedelta(days=(i - 1) % 365),    # DATA_CARICO
            (i % 10) + 1,                                  # FORNITORE_ID (1-10)
            (i % 20) + 1,                                  # ART_ID (1-20)
            # OP-TST-1: valori Decimal, non float. pyspark 3.5.9 (tirato da
            # delta-spark 3.2.0) ha il type-check stretto e rifiuta la coercizione
            # float -> DecimalType(18,4) che le versioni vecchie accettavano.
            Decimal(100 + i * 2),                          # PESO_NETTO
            Decimal(110 + i * 2),                          # PESO_LORDO
            Decimal(i * 5),                                # QTA_RICEVUTA
        ))

    return spark.createDataFrame(rows, schema=schema)


# ---------------------------------------------------------------------------
# DataFrame campione: DIM_FORNITORE
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_dim_fornitore(spark: SparkSession):
    """
    Dimensione Fornitore con 10 fornitori (FORNITORE_ID 1-10).

    Schema:
        FORNITORE_ID    INT
        RAGIONE_SOCIALE STRING
        PAESE           STRING
        ATTIVO          STRING
    """
    schema = StructType([
        StructField("FORNITORE_ID", IntegerType(), nullable=False),
        StructField("RAGIONE_SOCIALE", StringType(), nullable=True),
        StructField("PAESE", StringType(), nullable=True),
        StructField("ATTIVO", StringType(), nullable=True),
    ])

    fornitori = [
        (1, "Fornitore Alpha Srl", "IT", "S"),
        (2, "Beta Supply SpA", "IT", "S"),
        (3, "Gamma Logistics GmbH", "DE", "S"),
        (4, "Delta Trading SA", "FR", "S"),
        (5, "Epsilon Parts Ltd", "GB", "S"),
        (6, "Zeta Components Srl", "IT", "N"),
        (7, "Eta Materials BV", "NL", "S"),
        (8, "Theta Industries SA", "ES", "S"),
        (9, "Iota Systems Srl", "IT", "S"),
        (10, "Kappa Group SpA", "IT", "S"),
        (-1, "SCONOSCIUTO", "XX", "N"),   # Default per Late-Arriving
    ]
    return spark.createDataFrame(fornitori, schema=schema)


# ---------------------------------------------------------------------------
# DataFrame campione: DIM_ARTICOLO
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_dim_articolo(spark: SparkSession):
    """
    Dimensione Articolo con 20 articoli (ART_ID 1-20) + riga -1 sconosciuto.

    Schema:
        ART_ID          INT
        COD_ARTICOLO    STRING
        DESCRIZIONE     STRING
        CATEGORIA       STRING
        UM              STRING
    """
    schema = StructType([
        StructField("ART_ID", IntegerType(), nullable=False),
        StructField("COD_ARTICOLO", StringType(), nullable=True),
        StructField("DESCRIZIONE", StringType(), nullable=True),
        StructField("CATEGORIA", StringType(), nullable=True),
        StructField("UM", StringType(), nullable=True),
    ])

    articoli = [(i, f"ART{i:04d}", f"Articolo {i}", f"CAT{(i % 5) + 1}", "KG")
                for i in range(1, 21)]
    articoli.append((-1, "SCONOSCIUTO", "Articolo sconosciuto", "N/A", "N/A"))

    return spark.createDataFrame(articoli, schema=schema)
