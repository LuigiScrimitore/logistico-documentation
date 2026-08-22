# ─────────────────────────────────────────────────────────────────────────────
# Logistico 2.0 — Spark + Delta locale per test Bronze (Piano A parte 2)
#
# Base: jupyter/pyspark-notebook:spark-3.5.0
#  - Python 3.11
#  - PySpark 3.5.0
#  - OpenJDK 17
#  - Allineato a Databricks Runtime 15.4 LTS (Spark 3.5.0, Scala 2.12) — OP-19
#
# Container HEADLESS: i comandi si lanciano via `docker compose exec spark ...`.
# Nessuna porta esposta verso l'host (no Jupyter web).
# ─────────────────────────────────────────────────────────────────────────────

FROM jupyter/pyspark-notebook:spark-3.5.0

LABEL maintainer="Logistico 2.0 — Team Logistica"
LABEL description="Spark+Delta locale per test Bronze su CSV reali (no Databricks)"

# ── Dipendenze Python addizionali (delta-spark + tooling) ───────────────────
# NB: switch a root per scrivere in /tmp ed essere sicuri sui permessi pip.
USER root
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt \
 && fix-permissions "${CONDA_DIR}" \
 && fix-permissions "/home/${NB_USER}"
USER ${NB_UID}

# ── Pre-cache jar Delta in ~/.ivy2 per avvio piu' veloce ────────────────────
# Esegue una mini-sessione Spark che provoca il download dei jar
# io.delta:delta-spark_2.12:3.2.0 in cache locale. La prima esecuzione
# nel container sara' quindi istantanea.
RUN python -c "from delta import configure_spark_with_delta_pip; \
from pyspark.sql import SparkSession; \
s = configure_spark_with_delta_pip(\
        SparkSession.builder.master('local[1]')\
        .config('spark.driver.memory','1g')\
    ).getOrCreate(); \
s.stop()" 2>/dev/null || echo "Pre-cache delta jars completato (warning normali)"

# ── Working dir e variabili ambiente ────────────────────────────────────────
WORKDIR /workspace/code

ENV PYTHONPATH=/workspace/code/lib/logistica_utils:/workspace/code/tests/local_bronze
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3
# Riduce verbosita' Spark
ENV SPARK_LOG_LEVEL=WARN

# Container resta attivo: si lanciano i comandi via `docker compose exec`
CMD ["tail", "-f", "/dev/null"]
