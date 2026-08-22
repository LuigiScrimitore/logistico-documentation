"""
test_regola_30min.py — Test per la "regola 30 minuti attrezzaggio" (Prep Spedizioni).

Logica:
    ORE_PRODUTTIVE = max(0, DURATA_MINUTI - 30) / 60
    PRODUTTIVITA_COLLI_ORA = COLLI_PREPARATI / ORE_PRODUTTIVE
                              (None se ORE_PRODUTTIVE = 0)

La regola si applica a OGNI sessione di un operatore, non all'insieme giornaliero.
"""

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
    TimestampType,
)


# ---------------------------------------------------------------------------
# Logica da testare (in produzione questa vive in un notebook Silver/Gold)
# ---------------------------------------------------------------------------

def apply_regola_30min(spark, df):
    """
    Applica la regola dei 30 minuti di attrezzaggio alle sessioni di preparazione.

    Input DataFrame atteso:
        SESSIONE_ID     LONG
        OPERATORE_ID    INT
        DATA_SESSIONE   DATE
        DURATA_MINUTI   DECIMAL(10,2)  — durata totale della sessione in minuti
        COLLI_PREPARATI INT            — numero colli preparati nella sessione

    Output aggiunge:
        ORE_PRODUTTIVE         DECIMAL(18,6)  — max(0, DURATA - 30) / 60
        PRODUTTIVITA_COLLI_ORA DECIMAL(18,4)  — COLLI / ORE_PRODUTTIVE (None se 0)
    """
    result = df.withColumn(
        "ORE_PRODUTTIVE",
        F.greatest(
            F.lit(Decimal("0.000000")),
            (F.col("DURATA_MINUTI") - F.lit(Decimal("30.00"))) / F.lit(Decimal("60.00")),
        ).cast(DecimalType(18, 6)),
    ).withColumn(
        "PRODUTTIVITA_COLLI_ORA",
        F.when(
            F.col("ORE_PRODUTTIVE") > F.lit(Decimal("0.000000")),
            (F.col("COLLI_PREPARATI").cast(DecimalType(18, 4)) / F.col("ORE_PRODUTTIVE"))
            .cast(DecimalType(18, 4)),
        ).otherwise(F.lit(None).cast(DecimalType(18, 4))),
    )
    return result


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def sessioni_schema():
    return StructType([
        StructField("SESSIONE_ID", LongType(), False),
        StructField("OPERATORE_ID", IntegerType(), False),
        StructField("DATA_SESSIONE", DateType(), False),
        StructField("DURATA_MINUTI", DecimalType(10, 2), False),
        StructField("COLLI_PREPARATI", IntegerType(), False),
    ])


def make_sessione_df(spark, rows, schema):
    from datetime import date
    full_rows = [(r[0], r[1], date(2026, 5, 29), Decimal(str(r[2])), r[3]) for r in rows]
    return spark.createDataFrame(full_rows, schema=schema)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestRegola30Min:

    def test_sessione_2_ore_ore_produttive(self, spark, sessioni_schema):
        """Sessione di 120 minuti → ORE_PRODUTTIVE = (120-30)/60 = 1.5."""
        df = make_sessione_df(spark, [(1, 10, 120, 50)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("1.500000")

    def test_sessione_20min_ore_produttive_zero(self, spark, sessioni_schema):
        """Sessione di 20 minuti → ORE_PRODUTTIVE = 0 (non può essere negativo)."""
        df = make_sessione_df(spark, [(1, 10, 20, 5)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("0.000000")

    def test_sessione_esattamente_30min_ore_produttive_zero(self, spark, sessioni_schema):
        """Sessione di esattamente 30 minuti → ORE_PRODUTTIVE = 0."""
        df = make_sessione_df(spark, [(1, 10, 30, 10)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("0.000000")

    def test_sessione_31min_ore_produttive(self, spark, sessioni_schema):
        """Sessione di 31 minuti → ORE_PRODUTTIVE = 1/60 ≈ 0.016667."""
        df = make_sessione_df(spark, [(1, 10, 31, 2)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        # (31 - 30) / 60 = 1/60 ≈ 0.016667
        expected = Decimal("1") / Decimal("60")
        # Tolleranza per arrotondamento decimale
        diff = abs(result["ORE_PRODUTTIVE"] - expected)
        assert diff < Decimal("0.000001"), (
            f"Atteso ≈ {expected:.6f}, ottenuto {result['ORE_PRODUTTIVE']}"
        )

    def test_sessione_20min_produttivita_none(self, spark, sessioni_schema):
        """ORE_PRODUTTIVE = 0 → PRODUTTIVITA_COLLI_ORA deve essere NULL."""
        df = make_sessione_df(spark, [(1, 10, 20, 5)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["PRODUTTIVITA_COLLI_ORA"] is None

    def test_produttivita_calcolata_correttamente(self, spark, sessioni_schema):
        """PRODUTTIVITA = COLLI / ORE_PRODUTTIVE verificata numericamente."""
        # 90 min → (90-30)/60 = 1.0 h; 60 colli → 60 colli/ora
        df = make_sessione_df(spark, [(1, 10, 90, 60)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("1.000000")
        assert result["PRODUTTIVITA_COLLI_ORA"] == Decimal("60.0000")

    def test_produttivita_2h_100_colli(self, spark, sessioni_schema):
        """120 min, 100 colli → ORE_PRODUTTIVE=1.5 → PRODUTTIVITA≈66.6667."""
        df = make_sessione_df(spark, [(1, 10, 120, 100)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("1.500000")
        expected_prod = Decimal("100") / Decimal("1.5")
        diff = abs(result["PRODUTTIVITA_COLLI_ORA"] - expected_prod)
        assert diff < Decimal("0.001")

    def test_regola_applicata_a_ogni_sessione(self, spark, sessioni_schema):
        """La regola si applica a OGNI sessione, non alla somma giornaliera."""
        from datetime import date
        rows = [
            (1, 10, date(2026, 5, 29), Decimal("60"), 20),   # OP10 sessione 1: 30 min produttivi
            (2, 10, date(2026, 5, 29), Decimal("25"), 5),    # OP10 sessione 2: 0 min produttivi
            (3, 10, date(2026, 5, 29), Decimal("90"), 30),   # OP10 sessione 3: 60 min produttivi
        ]
        schema = sessioni_schema
        df = spark.createDataFrame(rows, schema=schema)
        result = {row["SESSIONE_ID"]: row for row in apply_regola_30min(spark, df).collect()}

        # Sessione 1: (60-30)/60 = 0.5h
        assert result[1]["ORE_PRODUTTIVE"] == Decimal("0.500000")
        # Sessione 2: (25-30) < 0 → 0
        assert result[2]["ORE_PRODUTTIVE"] == Decimal("0.000000")
        assert result[2]["PRODUTTIVITA_COLLI_ORA"] is None
        # Sessione 3: (90-30)/60 = 1.0h
        assert result[3]["ORE_PRODUTTIVE"] == Decimal("1.000000")

    def test_operatori_diversi_stessa_data(self, spark, sessioni_schema):
        """Operatori diversi nello stesso giorno devono essere calcolati indipendentemente."""
        from datetime import date
        rows = [
            (1, 1, date(2026, 5, 29), Decimal("60"), 10),
            (2, 2, date(2026, 5, 29), Decimal("20"), 5),
        ]
        df = spark.createDataFrame(rows, schema=sessioni_schema)
        result = {row["SESSIONE_ID"]: row for row in apply_regola_30min(spark, df).collect()}

        assert result[1]["ORE_PRODUTTIVE"] == Decimal("0.500000")
        assert result[2]["ORE_PRODUTTIVE"] == Decimal("0.000000")

    def test_zero_colli_ore_positive(self, spark, sessioni_schema):
        """Sessione con 0 colli ma ore produttive > 0 → PRODUTTIVITA = 0."""
        df = make_sessione_df(spark, [(1, 10, 60, 0)], sessioni_schema)
        result = apply_regola_30min(spark, df).collect()[0]
        assert result["ORE_PRODUTTIVE"] == Decimal("0.500000")
        assert result["PRODUTTIVITA_COLLI_ORA"] == Decimal("0.0000")
