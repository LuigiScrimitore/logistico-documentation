"""
test_dim_calendario.py — Test per la logica di generazione DIM_CALENDARIO.

Verifica:
- Range date 2018-01-01 a 2030-12-31
- Nessun buco di date
- Festività italiane corrette
- FLAG_LAVORATIVO = False per domeniche
- SETTIMANA_ISO corretta
"""

from datetime import date, timedelta

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DateType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


# ---------------------------------------------------------------------------
# Generazione DIM_CALENDARIO (logica da testare)
# ---------------------------------------------------------------------------

def build_dim_calendario(spark, date_from: date, date_to: date):
    """
    Genera il DataFrame DIM_CALENDARIO con le colonne standard.

    In produzione questa logica vive in un notebook Silver/Gold.
    Qui la duplichiamo per consentire i test unitari.

    Colonne prodotte:
        DATA_CALENDARIO     DATE
        ANNO                INT
        MESE                INT
        GIORNO              INT
        GIORNO_SETTIMANA    INT     (1=Lunedì ... 7=Domenica, ISO)
        NOME_GIORNO         STRING
        SETTIMANA_ISO       INT
        ANNO_ISO            INT
        TRIMESTRE           INT
        FLAG_LAVORATIVO     BOOLEAN  (False per sabato, domenica, festività IT)
        FLAG_FESTIVO_IT     BOOLEAN  (True per festività nazionali italiane)
        DESCRIZIONE_FESTIVO STRING   (Nome festività o null)
    """
    # Genera sequenza di date
    days = (date_to - date_from).days + 1
    dates = [date_from + timedelta(days=i) for i in range(days)]

    # Festività italiane fisse (mese, giorno) → nome
    FESTIVITA_FISSE = {
        (1, 1): "Capodanno",
        (1, 6): "Epifania",
        (4, 25): "Festa della Liberazione",
        (5, 1): "Festa dei Lavoratori",
        (6, 2): "Festa della Repubblica",
        (8, 15): "Ferragosto",
        (11, 1): "Ognissanti",
        (12, 8): "Immacolata Concezione",
        (12, 25): "Natale",
        (12, 26): "Santo Stefano",
    }

    # Pasqua con algoritmo di Butcher
    def easter(year: int) -> date:
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    NOMI_GIORNO = {
        1: "Lunedì", 2: "Martedì", 3: "Mercoledì",
        4: "Giovedì", 5: "Venerdì", 6: "Sabato", 7: "Domenica",
    }

    rows = []
    for d in dates:
        iso_cal = d.isocalendar()
        giorno_settimana = iso_cal[2]  # 1=Lunedì, 7=Domenica

        # Festività fisse
        desc_festivo = FESTIVITA_FISSE.get((d.month, d.day))

        # Pasquetta (lunedì dopo Pasqua)
        pasqua = easter(d.year)
        pasquetta = pasqua + timedelta(days=1)
        if d == pasqua:
            desc_festivo = "Pasqua"
        elif d == pasquetta:
            desc_festivo = "Pasquetta"

        flag_festivo = desc_festivo is not None
        flag_lavorativo = (giorno_settimana <= 5) and (not flag_festivo)

        rows.append((
            d,
            d.year,
            d.month,
            d.day,
            giorno_settimana,
            NOMI_GIORNO[giorno_settimana],
            iso_cal[1],   # settimana ISO
            iso_cal[0],   # anno ISO
            (d.month - 1) // 3 + 1,  # trimestre
            flag_lavorativo,
            flag_festivo,
            desc_festivo,
        ))

    schema = StructType([
        StructField("DATA_CALENDARIO", DateType(), False),
        StructField("ANNO", IntegerType(), False),
        StructField("MESE", IntegerType(), False),
        StructField("GIORNO", IntegerType(), False),
        StructField("GIORNO_SETTIMANA", IntegerType(), False),
        StructField("NOME_GIORNO", StringType(), False),
        StructField("SETTIMANA_ISO", IntegerType(), False),
        StructField("ANNO_ISO", IntegerType(), False),
        StructField("TRIMESTRE", IntegerType(), False),
        StructField("FLAG_LAVORATIVO", BooleanType(), False),
        StructField("FLAG_FESTIVO_IT", BooleanType(), False),
        StructField("DESCRIZIONE_FESTIVO", StringType(), True),
    ])

    return spark.createDataFrame(rows, schema=schema)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dim_cal(spark):
    """DIM_CALENDARIO completa 2018-2030 (condivisa tra i test del modulo)."""
    return build_dim_calendario(spark, date(2018, 1, 1), date(2030, 12, 31))


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestDimCalendario:

    def test_range_date_start(self, dim_cal):
        """La data minima deve essere 2018-01-01."""
        min_date = dim_cal.agg(F.min("DATA_CALENDARIO")).collect()[0][0]
        assert min_date == date(2018, 1, 1)

    def test_range_date_end(self, dim_cal):
        """La data massima deve essere 2030-12-31."""
        max_date = dim_cal.agg(F.max("DATA_CALENDARIO")).collect()[0][0]
        assert max_date == date(2030, 12, 31)

    def test_no_date_gaps(self, dim_cal):
        """Non devono esserci buchi nella sequenza di date."""
        count = dim_cal.count()
        expected_days = (date(2030, 12, 31) - date(2018, 1, 1)).days + 1
        assert count == expected_days

    def test_no_duplicate_dates(self, dim_cal):
        """Non devono esserci date duplicate."""
        total = dim_cal.count()
        distinct = dim_cal.select("DATA_CALENDARIO").distinct().count()
        assert total == distinct

    # -- Festività italiane --

    def test_capodanno_2026(self, dim_cal):
        """2026-01-01 deve essere FLAG_FESTIVO_IT=True con descrizione Capodanno."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 1, 1))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True
        assert row["DESCRIZIONE_FESTIVO"] == "Capodanno"

    def test_liberazione_2026(self, dim_cal):
        """2026-04-25 (Festa della Liberazione) deve essere festivo."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 4, 25))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True
        assert "Liberazione" in row["DESCRIZIONE_FESTIVO"]

    def test_festa_repubblica_2026(self, dim_cal):
        """2026-06-02 (Festa della Repubblica) deve essere festivo."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 6, 2))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True
        assert "Repubblica" in row["DESCRIZIONE_FESTIVO"]

    def test_natale_2026(self, dim_cal):
        """2026-12-25 (Natale) deve essere festivo."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 12, 25))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True

    def test_pasqua_2026(self, dim_cal):
        """2026-04-05 è Pasqua (per il 2026) — verifica festivo."""
        # Pasqua 2026 cade il 5 aprile
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 4, 5))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True
        assert row["DESCRIZIONE_FESTIVO"] == "Pasqua"

    def test_pasquetta_2026(self, dim_cal):
        """2026-04-06 è Pasquetta — verifica festivo."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 4, 6))).collect()[0]
        assert row["FLAG_FESTIVO_IT"] is True
        assert row["DESCRIZIONE_FESTIVO"] == "Pasquetta"

    # -- Domeniche --

    def test_domenica_not_lavorativo(self, dim_cal):
        """Le domeniche devono avere FLAG_LAVORATIVO=False."""
        domeniche = dim_cal.filter(F.col("GIORNO_SETTIMANA") == 7)
        non_lavorative = domeniche.filter(F.col("FLAG_LAVORATIVO") == False)
        assert domeniche.count() == non_lavorative.count()

    def test_domeniche_have_nome_domenica(self, dim_cal):
        """Le domeniche devono avere NOME_GIORNO = 'Domenica'."""
        domeniche = dim_cal.filter(F.col("GIORNO_SETTIMANA") == 7)
        non_domenica = domeniche.filter(F.col("NOME_GIORNO") != "Domenica")
        assert non_domenica.count() == 0

    def test_lunedi_can_be_lavorativo(self, dim_cal):
        """I lunedì non festivi devono essere lavorativi."""
        lunedi_non_festivi = dim_cal.filter(
            (F.col("GIORNO_SETTIMANA") == 1) & (F.col("FLAG_FESTIVO_IT") == False)
        )
        non_lavorativi = lunedi_non_festivi.filter(F.col("FLAG_LAVORATIVO") == False)
        assert non_lavorativi.count() == 0

    # -- SETTIMANA_ISO --

    def test_settimana_iso_2026_01_01(self, dim_cal):
        """2026-01-01 è giovedì, SETTIMANA_ISO = 1."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 1, 1))).collect()[0]
        assert row["SETTIMANA_ISO"] == 1
        assert row["GIORNO_SETTIMANA"] == 4  # Giovedì

    def test_settimana_iso_2026_12_28(self, dim_cal):
        """2026-12-28 è lunedì della settimana 53 del 2026."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 12, 28))).collect()[0]
        assert row["SETTIMANA_ISO"] == 53
        assert row["GIORNO_SETTIMANA"] == 1  # Lunedì

    def test_settimana_iso_2020_01_01(self, dim_cal):
        """2020-01-01 è mercoledì, SETTIMANA_ISO = 1."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2020, 1, 1))).collect()[0]
        assert row["SETTIMANA_ISO"] == 1
        assert row["GIORNO_SETTIMANA"] == 3  # Mercoledì

    # -- Trimestri --

    def test_trimestre_gennaio(self, dim_cal):
        """Gennaio deve essere trimestre 1."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 1, 15))).collect()[0]
        assert row["TRIMESTRE"] == 1

    def test_trimestre_luglio(self, dim_cal):
        """Luglio deve essere trimestre 3."""
        row = dim_cal.filter(F.col("DATA_CALENDARIO") == F.lit(date(2026, 7, 1))).collect()[0]
        assert row["TRIMESTRE"] == 3
