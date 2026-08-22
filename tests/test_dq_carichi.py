"""
test_dq_carichi.py — Test DQ per l'area Carichi (silver_carichi_testate).

Verifica:
- check_no_duplicates su CARICO_ID
- check_no_nulls su [CARICO_ID, DATA_CARICO, FORNITORE_ID]
- check_numeric_range su PESO_NETTO (min=0)
- check_referential su FORNITORE_ID: tasso >= 98%
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from logistica_utils import DQHelper, Logger


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def logger_silent():
    """Logger che scrive su stdout (accettabile nei test, output catturato da pytest)."""
    return Logger("test_dq_carichi", area="logistica", layer="silver")


@pytest.fixture()
def silver_carichi_schema():
    return StructType([
        StructField("CARICO_ID", LongType(), nullable=False),
        StructField("DATA_CARICO", DateType(), nullable=True),
        StructField("FORNITORE_ID", IntegerType(), nullable=True),
        StructField("ART_ID", IntegerType(), nullable=True),
        StructField("PESO_NETTO", DecimalType(18, 4), nullable=True),
        StructField("PESO_LORDO", DecimalType(18, 4), nullable=True),
        StructField("QTA_RICEVUTA", DecimalType(18, 4), nullable=True),
    ])


@pytest.fixture()
def dim_fornitore_schema():
    return StructType([
        StructField("FORNITORE_ID", IntegerType(), nullable=False),
        StructField("RAGIONE_SOCIALE", StringType(), nullable=True),
    ])


def _make_carichi(spark, schema, rows):
    return spark.createDataFrame(rows, schema=schema)


# ---------------------------------------------------------------------------
# Test: check_no_duplicates su CARICO_ID
# ---------------------------------------------------------------------------

class TestDQNoduplicates:

    def test_no_duplicates_clean_data(self, spark, silver_carichi_schema, logger_silent):
        """DataFrame senza duplicati → check deve passare."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (2, date(2026, 1, 2), 2, 1, Decimal("200.0"), Decimal("220.0"), Decimal("20.0")),
            (3, date(2026, 1, 3), 3, 2, Decimal("150.0"), Decimal("165.0"), Decimal("15.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_duplicates(["CARICO_ID"]) is True

    def test_duplicates_detected(self, spark, silver_carichi_schema, logger_silent):
        """DataFrame con CARICO_ID duplicato → check deve fallire."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (1, date(2026, 1, 1), 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),  # dup
            (2, date(2026, 1, 2), 2, 1, Decimal("200.0"), Decimal("220.0"), Decimal("20.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_duplicates(["CARICO_ID"]) is False

    def test_duplicate_count_in_results(self, spark, silver_carichi_schema, logger_silent):
        """Il report deve indicare correttamente il numero di duplicati."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (1, date(2026, 1, 2), 2, 1, Decimal("200.0"), Decimal("220.0"), Decimal("20.0")),
            (2, date(2026, 1, 3), 1, 1, Decimal("50.0"), Decimal("55.0"), Decimal("5.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        dq.check_no_duplicates(["CARICO_ID"])
        result = dq._results[-1]
        assert result["duplicate_count"] == 1

    def test_100_unique_rows(self, spark, sample_carichi_df, logger_silent):
        """Il sample_carichi_df da 100 righe non deve avere duplicati."""
        dq = DQHelper(spark, sample_carichi_df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_duplicates(["CARICO_ID"]) is True


# ---------------------------------------------------------------------------
# Test: check_no_nulls su [CARICO_ID, DATA_CARICO, FORNITORE_ID]
# ---------------------------------------------------------------------------

class TestDQNoNulls:

    def test_no_nulls_clean_data(self, spark, sample_carichi_df, logger_silent):
        """DataFrame pulito → nessun NULL su CARICO_ID, DATA_CARICO, FORNITORE_ID."""
        dq = DQHelper(spark, sample_carichi_df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_nulls(["CARICO_ID", "DATA_CARICO", "FORNITORE_ID"]) is True

    def test_null_carico_id_detected(self, spark, silver_carichi_schema, logger_silent):
        """NULL su CARICO_ID deve far fallire il check."""
        # CARICO_ID ha nullable=False nello schema, impostiamo via withColumn
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        # Forza un NULL sostituendo CARICO_ID con null condizionale
        df_with_null = df.withColumn(
            "CARICO_ID",
            F.when(F.col("CARICO_ID") == 1, F.lit(None).cast("long")).otherwise(F.col("CARICO_ID")),
        )
        dq = DQHelper(spark, df_with_null, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_nulls(["CARICO_ID"]) is False

    def test_null_fornitore_detected(self, spark, silver_carichi_schema, logger_silent):
        """NULL su FORNITORE_ID deve far fallire il check."""
        rows = [
            (1, date(2026, 1, 1), None, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (2, date(2026, 1, 2), 1, 2, Decimal("50.0"), Decimal("55.0"), Decimal("5.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_no_nulls(["FORNITORE_ID"]) is False

    def test_null_report_details(self, spark, silver_carichi_schema, logger_silent):
        """Il report deve indicare le colonne con NULL e il relativo conteggio."""
        rows = [
            (1, None, 1, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (2, date(2026, 1, 2), None, 2, Decimal("50.0"), Decimal("55.0"), Decimal("5.0")),
            (3, date(2026, 1, 3), 1, 3, Decimal("75.0"), Decimal("82.5"), Decimal("7.5")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        dq.check_no_nulls(["DATA_CARICO", "FORNITORE_ID"])
        result = dq._results[-1]
        assert result["null_counts"]["DATA_CARICO"] == 1
        assert result["null_counts"]["FORNITORE_ID"] == 1


# ---------------------------------------------------------------------------
# Test: check_numeric_range su PESO_NETTO (min=0)
# ---------------------------------------------------------------------------

class TestDQNumericRange:

    def test_peso_netto_all_positive(self, spark, sample_carichi_df, logger_silent):
        """Tutti i PESO_NETTO > 0 → check deve passare."""
        dq = DQHelper(spark, sample_carichi_df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_numeric_range("PESO_NETTO", min_val=0) is True

    def test_peso_netto_negative_fails(self, spark, silver_carichi_schema, logger_silent):
        """PESO_NETTO negativo → check deve fallire."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("-5.0"), Decimal("110.0"), Decimal("10.0")),
            (2, date(2026, 1, 2), 2, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_numeric_range("PESO_NETTO", min_val=0) is False

    def test_peso_netto_zero_is_valid(self, spark, silver_carichi_schema, logger_silent):
        """PESO_NETTO = 0 è consentito (min=0 inclusivo → >= 0)."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("0.0"), Decimal("5.0"), Decimal("0.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        assert dq.check_numeric_range("PESO_NETTO", min_val=0) is True

    def test_peso_netto_null_ignored(self, spark, silver_carichi_schema, logger_silent):
        """I NULL in PESO_NETTO devono essere ignorati dal range check."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, None, Decimal("5.0"), Decimal("1.0")),
            (2, date(2026, 1, 2), 2, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        # Il NULL non è "fuori range" → check deve passare
        assert dq.check_numeric_range("PESO_NETTO", min_val=0) is True

    def test_out_of_range_count_in_report(self, spark, silver_carichi_schema, logger_silent):
        """Il report deve indicare quante righe sono fuori range."""
        rows = [
            (1, date(2026, 1, 1), 1, 1, Decimal("-1.0"), Decimal("5.0"), Decimal("1.0")),
            (2, date(2026, 1, 2), 2, 1, Decimal("-2.0"), Decimal("5.0"), Decimal("1.0")),
            (3, date(2026, 1, 3), 3, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        dq.check_numeric_range("PESO_NETTO", min_val=0)
        result = dq._results[-1]
        assert result["out_of_range_count"] == 2


# ---------------------------------------------------------------------------
# Test: check_referential su FORNITORE_ID (soglia 98%)
# ---------------------------------------------------------------------------

class TestDQReferential:

    def test_100_percent_match(self, spark, sample_carichi_df, sample_dim_fornitore, logger_silent):
        """FORNITORE_ID 1-10 tutti presenti in dim → tasso = 1.0."""
        dq = DQHelper(spark, sample_carichi_df, "silver.logistica.carichi_testate", logger_silent)
        rate = dq.check_referential("FORNITORE_ID", sample_dim_fornitore, "FORNITORE_ID")
        assert rate == 1.0

    def test_below_98_percent_fails(self, spark, silver_carichi_schema, dim_fornitore_schema, logger_silent):
        """FK missing > 2% → check deve fallire e tasso < 0.98."""
        # 10 righe, 3 con FORNITORE_ID=99 (non esiste) → 70% match
        rows = [
            (i, date(2026, 1, 1), 1 if i <= 7 else 99, 1,
             Decimal("100.0"), Decimal("110.0"), Decimal("10.0"))
            for i in range(1, 11)
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)

        dim_rows = [(1, "Fornitore 1")]
        dim_df = spark.createDataFrame(dim_rows, schema=dim_fornitore_schema)

        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        rate = dq.check_referential("FORNITORE_ID", dim_df, "FORNITORE_ID")
        assert rate < 0.98
        assert dq._results[-1]["passed"] is False

    def test_exactly_98_percent_passes(self, spark, silver_carichi_schema, dim_fornitore_schema, logger_silent):
        """Esattamente 98% di match → check deve passare."""
        # 100 righe, 2 con FK mancante
        rows = [
            (i, date(2026, 1, 1), 1 if i <= 98 else 999, 1,
             Decimal("100.0"), Decimal("110.0"), Decimal("10.0"))
            for i in range(1, 101)
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)

        dim_rows = [(1, "Fornitore OK")]
        dim_df = spark.createDataFrame(dim_rows, schema=dim_fornitore_schema)

        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        rate = dq.check_referential("FORNITORE_ID", dim_df, "FORNITORE_ID")
        assert abs(rate - 0.98) < 0.001
        assert dq._results[-1]["passed"] is True

    def test_referential_null_fk_ignored(self, spark, silver_carichi_schema, dim_fornitore_schema, logger_silent):
        """Le righe con FORNITORE_ID NULL devono essere escluse dal calcolo."""
        rows = [
            (1, date(2026, 1, 1), None, 1, Decimal("100.0"), Decimal("110.0"), Decimal("10.0")),
            (2, date(2026, 1, 2), 1, 1, Decimal("50.0"), Decimal("55.0"), Decimal("5.0")),
            (3, date(2026, 1, 3), 1, 1, Decimal("75.0"), Decimal("82.5"), Decimal("7.5")),
        ]
        df = _make_carichi(spark, silver_carichi_schema, rows)
        dim_rows = [(1, "Fornitore OK")]
        dim_df = spark.createDataFrame(dim_rows, schema=dim_fornitore_schema)

        dq = DQHelper(spark, df, "silver.logistica.carichi_testate", logger_silent)
        rate = dq.check_referential("FORNITORE_ID", dim_df, "FORNITORE_ID")
        # 2 non-null: entrambe trovate → 100%
        assert rate == 1.0

    def test_run_all_carichi_full_suite(self, spark, sample_carichi_df, sample_dim_fornitore, logger_silent):
        """Suite DQ completa su sample_carichi_df deve passare tutti i check."""
        dq = DQHelper(spark, sample_carichi_df, "silver.logistica.carichi_testate", logger_silent)
        report = dq.run_all([
            ("check_no_duplicates", {"key_cols": ["CARICO_ID"]}),
            ("check_no_nulls", {"cols": ["CARICO_ID", "DATA_CARICO", "FORNITORE_ID"]}),
            ("check_numeric_range", {"col": "PESO_NETTO", "min_val": 0}),
        ])
        assert report["all_passed"] is True
        assert report["failed_count"] == 0
