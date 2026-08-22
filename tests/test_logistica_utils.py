"""
test_logistica_utils.py — Test suite per la libreria logistica_utils.

Copre: SecretHelper, Logger, DeltaHelper, DQHelper, utils (surrogate_key_fallback, cast_decimal).
"""

import json
import os
import tempfile
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from logistica_utils import (
    DeltaHelper,
    DQHelper,
    Logger,
    SecretHelper,
    cast_decimal,
    surrogate_key_fallback,
)


# ===========================================================================
# SecretHelper
# ===========================================================================

class TestSecretHelper:

    def test_get_secret_from_env(self, monkeypatch):
        """get_secret() deve leggere da os.environ se dbutils non disponibile."""
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_URL", "jdbc:oracle:thin:@//host:1521/SVC")
        helper = SecretHelper(scope="logistica-kv")
        helper._dbutils = None  # Forza fallback su env
        result = helper.get_secret("oracle-logistica-jdbc-url")
        assert result == "jdbc:oracle:thin:@//host:1521/SVC"

    def test_get_secret_missing_env_raises(self, monkeypatch):
        """get_secret() deve alzare KeyError se la variabile env non esiste."""
        monkeypatch.delenv("ORACLE_LOGISTICA_JDBC_URL", raising=False)
        helper = SecretHelper()
        helper._dbutils = None
        with pytest.raises(KeyError, match="oracle-logistica-jdbc-url"):
            helper.get_secret("oracle-logistica-jdbc-url")

    def test_get_jdbc_url_from_env(self, monkeypatch):
        """get_jdbc_url() deve costruire la chiave corretta."""
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_URL", "jdbc:oracle:thin:@//h:1521/X")
        helper = SecretHelper()
        helper._dbutils = None
        assert helper.get_jdbc_url("oracle-logistica") == "jdbc:oracle:thin:@//h:1521/X"

    def test_get_jdbc_options_returns_required_fields(self, monkeypatch):
        """get_jdbc_options() deve restituire url, user, password, driver, fetchsize."""
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_URL", "jdbc:oracle:thin:@//h:1521/X")
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_USER", "scott")
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_PASSWORD", "tiger")

        helper = SecretHelper()
        helper._dbutils = None
        opts = helper.get_jdbc_options("oracle-logistica")

        assert "url" in opts
        assert "user" in opts
        assert "password" in opts
        assert "driver" in opts
        assert "fetchsize" in opts
        assert opts["user"] == "scott"
        assert opts["password"] == "tiger"
        assert opts["driver"] == "oracle.jdbc.OracleDriver"

    def test_get_jdbc_options_merges_extra(self, monkeypatch):
        """get_jdbc_options() deve aggiungere extra_options al dict."""
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_URL", "u")
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_USER", "u")
        monkeypatch.setenv("ORACLE_LOGISTICA_JDBC_PASSWORD", "p")

        helper = SecretHelper()
        helper._dbutils = None
        opts = helper.get_jdbc_options(
            "oracle-logistica",
            extra_options={"numPartitions": "8", "dbtable": "MY_TABLE"},
        )
        assert opts["numPartitions"] == "8"
        assert opts["dbtable"] == "MY_TABLE"

    def test_get_secret_uses_dbutils_when_available(self, mock_dbutils):
        """get_secret() usa dbutils.secrets.get() quando disponibile."""
        helper = SecretHelper(scope="logistica-kv")
        helper._dbutils = mock_dbutils
        result = helper.get_secret("oracle-logistica-jdbc-url")
        mock_dbutils.secrets.get.assert_called_once_with(
            scope="logistica-kv", key="oracle-logistica-jdbc-url"
        )
        assert "jdbc:oracle" in result


# ===========================================================================
# Logger
# ===========================================================================

class TestLogger:

    def _capture_log(self, func, *args, **kwargs) -> dict:
        """Esegue func() catturando stdout e restituisce il JSON parsato."""
        import sys
        from io import StringIO
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            func(*args, **kwargs)
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue().strip()
        return json.loads(output)

    def test_info_emits_valid_json(self):
        log = Logger("test_notebook", area="logistica", layer="bronze")
        record = self._capture_log(log.info, "Test message", key1="value1")
        assert record["level"] == "INFO"
        assert record["message"] == "Test message"
        assert record["notebook"] == "test_notebook"
        assert record["area"] == "logistica"
        assert record["layer"] == "bronze"
        assert record["key1"] == "value1"
        assert "timestamp" in record

    def test_error_includes_exception_fields(self):
        log = Logger("test_notebook", area="logistica", layer="bronze")
        exc = ValueError("test error")
        record = self._capture_log(log.error, "Error occurred", exception=exc)
        assert record["level"] == "ERROR"
        assert record["exception_type"] == "ValueError"
        assert "test error" in record["exception_message"]

    def test_warning_level(self):
        log = Logger("nb", area="a", layer="b")
        record = self._capture_log(log.warning, "warn msg")
        assert record["level"] == "WARNING"

    def test_log_run_start_sets_run_id(self):
        log = Logger("nb", area="logistica", layer="bronze")
        record = self._capture_log(log.log_run_start, "SRC", "TGT", "2026-05-29")
        assert record["event"] == "run_start"
        assert record["run_date"] == "2026-05-29"
        assert log._run_id is not None

    def test_log_run_end(self):
        log = Logger("nb", area="logistica", layer="silver")
        record = self._capture_log(log.log_run_end, 1000, 950, 12.5)
        assert record["event"] == "run_end"
        assert record["rows_read"] == 1000
        assert record["rows_written"] == 950
        assert record["duration_seconds"] == 12.5

    def test_log_dq_result_passed(self):
        log = Logger("nb", area="a", layer="b")
        record = self._capture_log(
            log.log_dq_result, "check_no_nulls", True, {"null_count": 0}
        )
        assert record["passed"] is True
        assert record["level"] == "INFO"

    def test_log_dq_result_failed_is_warning(self):
        log = Logger("nb", area="a", layer="b")
        record = self._capture_log(
            log.log_dq_result, "check_no_nulls", False, {"null_count": 5}
        )
        assert record["passed"] is False
        assert record["level"] == "WARNING"

    def test_json_timestamp_format(self):
        log = Logger("nb", area="a", layer="b")
        record = self._capture_log(log.info, "ts test")
        ts = record["timestamp"]
        # Formato: 2026-05-29T14:30:00.000Z
        assert ts.endswith("Z")
        assert "T" in ts


# ===========================================================================
# DeltaHelper
# ===========================================================================

class TestDeltaHelper:

    @pytest.fixture()
    def tmp_schema(self, spark, tmp_path):
        """Crea un database temporaneo per i test Delta."""
        db_name = "test_delta_db"
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name} LOCATION '{tmp_path}'")
        yield db_name
        spark.sql(f"DROP DATABASE IF EXISTS {db_name} CASCADE")

    def test_table_not_exists(self, spark, tmp_schema):
        dh = DeltaHelper(spark, catalog="", schema=tmp_schema)
        # Deve restituire False per tabella inesistente
        assert dh.table_exists("nonexistent_table_xyz") is False

    def test_merge_into_creates_table_if_not_exists(self, spark, tmp_schema):
        """merge_into deve creare la tabella se non esiste."""
        dh = DeltaHelper(spark, catalog="", schema=tmp_schema)
        schema = StructType([
            StructField("ID", LongType(), nullable=False),
            StructField("VALORE", StringType(), nullable=True),
        ])
        df = spark.createDataFrame([(1, "alpha"), (2, "beta")], schema=schema)

        dh.merge_into(
            target_table="test_merge_create",
            source_df=df,
            merge_keys=["ID"],
        )

        result = spark.table(f"{tmp_schema}.test_merge_create").collect()
        assert len(result) == 2

    def test_merge_into_upsert(self, spark, tmp_schema):
        """merge_into deve aggiornare righe esistenti e inserire nuove."""
        dh = DeltaHelper(spark, catalog="", schema=tmp_schema)
        schema = StructType([
            StructField("ID", LongType(), nullable=False),
            StructField("VALORE", StringType(), nullable=True),
        ])

        # Caricamento iniziale
        initial_df = spark.createDataFrame([(1, "original"), (2, "original2")], schema=schema)
        dh.merge_into("test_upsert", initial_df, merge_keys=["ID"])

        # Upsert: modifica riga 1, aggiunge riga 3
        update_df = spark.createDataFrame([(1, "updated"), (3, "new")], schema=schema)
        dh.merge_into("test_upsert", update_df, merge_keys=["ID"])

        result = {row["ID"]: row["VALORE"]
                  for row in spark.table(f"{tmp_schema}.test_upsert").collect()}

        assert result[1] == "updated"   # aggiornato
        assert result[2] == "original2" # invariato
        assert result[3] == "new"       # inserito

    def test_get_max_watermark_empty_table(self, spark, tmp_schema):
        """get_max_watermark deve restituire None se la tabella non esiste."""
        dh = DeltaHelper(spark, catalog="", schema=tmp_schema)
        result = dh.get_max_watermark("nonexistent_wm_table", "TS_COL")
        assert result is None

    def test_get_max_watermark_correct_value(self, spark, tmp_schema):
        """get_max_watermark deve restituire il massimo corretto."""
        dh = DeltaHelper(spark, catalog="", schema=tmp_schema)
        schema = StructType([
            StructField("ID", LongType()),
            StructField("TS_COL", LongType()),
        ])
        df = spark.createDataFrame([(1, 100), (2, 500), (3, 250)], schema=schema)
        df.write.format("delta").mode("overwrite").saveAsTable(f"{tmp_schema}.test_watermark")

        result = dh.get_max_watermark("test_watermark", "TS_COL")
        assert result == 500


# ===========================================================================
# DQHelper
# ===========================================================================

class TestDQHelper:

    def _make_logger(self):
        """Logger con output soppresso per i test."""
        import sys
        from io import StringIO
        log = Logger("test", area="test", layer="test")
        return log

    def test_check_no_duplicates_passes(self, spark, sample_carichi_df):
        """check_no_duplicates deve passare su CARICO_ID univoco (1-100)."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        result = dq.check_no_duplicates(["CARICO_ID"])
        assert result is True

    def test_check_no_duplicates_fails(self, spark):
        """check_no_duplicates deve fallire quando ci sono duplicati sulla chiave."""
        schema = StructType([
            StructField("ID", LongType()),
            StructField("VAL", StringType()),
        ])
        # Riga con ID=1 appare due volte
        df = spark.createDataFrame([(1, "a"), (1, "b"), (2, "c")], schema=schema)
        log = self._make_logger()
        dq = DQHelper(spark, df, "test_table", log)
        result = dq.check_no_duplicates(["ID"])
        assert result is False

    def test_check_no_nulls_passes(self, spark, sample_carichi_df):
        """check_no_nulls deve passare su colonne senza NULL."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        result = dq.check_no_nulls(["CARICO_ID", "DATA_CARICO"])
        assert result is True

    def test_check_no_nulls_fails_when_null_present(self, spark):
        """check_no_nulls deve fallire se ci sono NULL."""
        schema = StructType([
            StructField("ID", LongType()),
            StructField("NAME", StringType()),
        ])
        df = spark.createDataFrame([(1, "Alice"), (2, None), (3, "Bob")], schema=schema)
        log = self._make_logger()
        dq = DQHelper(spark, df, "test_table", log)
        result = dq.check_no_nulls(["NAME"])
        assert result is False

    def test_check_row_count_passes(self, spark, sample_carichi_df):
        """check_row_count deve passare quando il count supera il minimo."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        assert dq.check_row_count(expected_min=50) is True
        assert dq.check_row_count(expected_min=100) is True

    def test_check_row_count_fails(self, spark, sample_carichi_df):
        """check_row_count deve fallire quando il count è sotto il minimo."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        assert dq.check_row_count(expected_min=101) is False

    def test_check_numeric_range_passes(self, spark, sample_carichi_df):
        """check_numeric_range deve passare per PESO_NETTO > 0."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        result = dq.check_numeric_range("PESO_NETTO", min_val=0)
        assert result is True

    def test_check_numeric_range_fails_negative(self, spark):
        """check_numeric_range deve fallire per valori negativi quando min=0."""
        from decimal import Decimal
        schema = StructType([StructField("PESO", DecimalType(18, 4))])
        df = spark.createDataFrame([(Decimal("10.0"),), (Decimal("-5.0"),)], schema=schema)
        log = self._make_logger()
        dq = DQHelper(spark, df, "test_table", log)
        result = dq.check_numeric_range("PESO", min_val=0)
        assert result is False

    def test_run_all_returns_report(self, spark, sample_carichi_df):
        """run_all deve restituire un dict con all_passed, passed_count, failed_count."""
        log = self._make_logger()
        dq = DQHelper(spark, sample_carichi_df, "test_table", log)
        report = dq.run_all([
            ("check_no_duplicates", {"key_cols": ["CARICO_ID"]}),
            ("check_no_nulls", {"cols": ["CARICO_ID"]}),
            ("check_row_count", {"expected_min": 10}),
        ])
        assert "all_passed" in report
        assert "passed_count" in report
        assert "failed_count" in report
        assert report["all_passed"] is True
        assert report["passed_count"] == 3
        assert report["failed_count"] == 0


# ===========================================================================
# surrogate_key_fallback
# ===========================================================================

class TestSurrogateKeyFallback:

    def test_all_fk_resolved(self, spark, sample_carichi_df, sample_dim_fornitore):
        """FK esistenti nella dimensione devono restare invariate."""
        result = surrogate_key_fallback(
            df=sample_carichi_df,
            fk_col="FORNITORE_ID",
            dim_df=sample_dim_fornitore,
            dim_pk="FORNITORE_ID",
            default_val=-1,
        )
        # FORNITORE_ID va da 1 a 10, tutti esistono in dim_fornitore → nessun -1
        negative_count = result.filter(F.col("FORNITORE_ID") == -1).count()
        assert negative_count == 0

    def test_missing_fk_becomes_default(self, spark):
        """FK non trovate nella dimensione devono diventare -1."""
        fact_schema = StructType([
            StructField("ID", LongType()),
            StructField("DIM_ID", IntegerType()),
        ])
        fact_df = spark.createDataFrame(
            [(1, 10), (2, 99), (3, 10)],  # 99 non esiste nella dim
            schema=fact_schema,
        )

        dim_schema = StructType([
            StructField("DIM_ID", IntegerType()),
            StructField("DESC", StringType()),
        ])
        dim_df = spark.createDataFrame([(10, "exists")], schema=dim_schema)

        result = surrogate_key_fallback(fact_df, "DIM_ID", dim_df, "DIM_ID", default_val=-1)
        rows = {row["ID"]: row["DIM_ID"] for row in result.collect()}

        assert rows[1] == 10   # trovato
        assert rows[2] == -1   # non trovato → -1
        assert rows[3] == 10   # trovato

    def test_custom_default_val(self, spark):
        """default_val deve essere rispettato quando specificato."""
        fact_schema = StructType([StructField("FK", IntegerType())])
        fact_df = spark.createDataFrame([(999,)], schema=fact_schema)
        dim_schema = StructType([StructField("PK", IntegerType())])
        dim_df = spark.createDataFrame([(1,)], schema=dim_schema)

        result = surrogate_key_fallback(fact_df, "FK", dim_df, "PK", default_val=0)
        assert result.collect()[0]["FK"] == 0


# ===========================================================================
# cast_decimal
# ===========================================================================

class TestCastDecimal:

    def test_cast_changes_type_to_decimal(self, spark):
        """cast_decimal deve cambiare il tipo delle colonne in DecimalType."""
        schema = StructType([
            StructField("PESO", StringType()),  # stringa
            StructField("QTA", StringType()),
        ])
        df = spark.createDataFrame([("10.5", "3.0")], schema=schema)
        result = cast_decimal(df, ["PESO", "QTA"], precision=18, scale=4)

        for field in result.schema.fields:
            if field.name in ("PESO", "QTA"):
                assert isinstance(field.dataType, DecimalType)
                assert field.dataType.precision == 18
                assert field.dataType.scale == 4

    def test_cast_preserves_value_precision(self, spark):
        """cast_decimal deve preservare il valore numerico."""
        from decimal import Decimal
        schema = StructType([StructField("VAL", StringType())])
        df = spark.createDataFrame([("123.4567",)], schema=schema)
        result = cast_decimal(df, ["VAL"])
        row = result.collect()[0]
        assert row["VAL"] == Decimal("123.4567")

    def test_cast_raises_for_missing_column(self, spark):
        """cast_decimal deve alzare ValueError per colonne inesistenti."""
        schema = StructType([StructField("A", StringType())])
        df = spark.createDataFrame([("x",)], schema=schema)
        with pytest.raises(ValueError, match="non trovate"):
            cast_decimal(df, ["NONEXISTENT"])

    def test_cast_partial_columns(self, spark):
        """cast_decimal deve agire solo sulle colonne indicate."""
        schema = StructType([
            StructField("A", StringType()),
            StructField("B", StringType()),
        ])
        df = spark.createDataFrame([("1.0", "2.0")], schema=schema)
        result = cast_decimal(df, ["A"])  # solo A

        a_type = result.schema["A"].dataType
        b_type = result.schema["B"].dataType
        assert isinstance(a_type, DecimalType)
        assert isinstance(b_type, StringType)
