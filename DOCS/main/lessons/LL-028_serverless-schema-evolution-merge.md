---
id: LL-028
titolo: Serverless — schema-evolution nel MERGE con .withSchemaEvolution(), non con spark.conf autoMerge
sintomi:
  - "CONFIG_NOT_AVAILABLE.SERVERLESS_DELTA_SCHEMA_AUTO_MERGE_ENABLED: Configuration spark.databricks.delta.schema.autoMerge.enabled is not available"
  - "Configuration ... is not supported in serverless environments"
tag: [serverless, delta, merge, schema-evolution, spark-conf]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-04
origine: [ACT_9027]
---

## Sintomo
Un bronze/silver con MERGE che evolve lo schema fallisce in serverless con
`CONFIG_NOT_AVAILABLE.SERVERLESS_DELTA_SCHEMA_AUTO_MERGE_ENABLED`: la conf
`spark.databricks.delta.schema.autoMerge.enabled` non e' settabile.

## Strada sbagliata
```python
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
DeltaTable...merge(...).whenMatchedUpdate(...).whenNotMatchedInsertAll().execute()
```
Le spark.conf a livello sessione per Delta autoMerge (come init scripts e altre conf cluster) non sono
disponibili sul serverless. Vale anche per `spark.sql.ansi.enabled` (vedi [[LL-027]]).

## Regola
Abilitare la schema-evolution **per-merge** sul builder (Delta 3.x) e `.option("mergeSchema","true")` sulla
CTAS:
```python
(DeltaTable.forName(spark, TARGET).alias("tgt")
 .merge(src.alias("src"), cond)
 .withSchemaEvolution()               # <-- serverless-safe
 .whenMatchedUpdate(...).whenNotMatchedInsertAll()
 .execute())
```

## Perche'
Il serverless non applica cluster policy/spark_conf a livello cluster: le impostazioni vanno espresse
nell'API del comando (option/builder) o nell'environment del job, non come conf globale. `.withSchemaEvolution()`
e' l'equivalente per-comando della conf autoMerge.

## Conferme e contraddizioni
- 2026-09-04 · Francesco Foconi · `bronze_storico_liste` DEV: rimossa la conf, aggiunto
  `.withSchemaEvolution()` → task verde nel job prep_sped.
