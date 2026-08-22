# Mapping PL/SQL → Spark SQL — Area Giacenze (Stock)

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica del flusso Oracle AS-IS](#1-panoramica-del-flusso-oracle-as-is)
2. [Tabella di mapping procedure](#2-tabella-di-mapping-procedure)
3. [Dettaglio procedure e trasformazioni](#3-dettaglio-procedure-e-trasformazioni)
4. [Modello dimensionale gold_f_giacenze](#4-modello-dimensionale-gold_f_giacenze)
5. [KPI Giacenze: definizioni e implementazione](#5-kpi-giacenze-definizioni-e-implementazione)
6. [Rischi di migrazione](#6-rischi-di-migrazione)

---

## 1. Panoramica del flusso Oracle AS-IS

```
Logistix (sorgente operativa — snapshot giornaliero)
   ↓  DB Link (REPLICA_LOGISTIX.SP_MAIN)
CDT_ESTR.SP_REPLICA_LOGISTIX  →  GIACENZE_DAILY, MOVIMENTI_MAGAZZINO, RIEPILOGHI
   ↓
CDT_ESTR.SP_ESTRAI_STOCK      →  ESTRAI_STOCK.SP_MAIN
   ↓
CDT_SA.SP_LOAD_F_STOCK        →  T_STOCK_TMP (STEP0 + STEP1)
   ↓
CDT_DW.F_STOCK                →  Fact table giornaliera + vista mensile
```

Il modello stock in Oracle è uno snapshot point-in-time: ogni giorno vengono fotografate le quantità presenti in magazzino per ogni (sito, articolo, ubicazione). Non è un modello a eventi/delta, ma un'immagine completa della situazione stock al momento dell'estrazione.

**Flusso Databricks target:**

```
Oracle Logistix (JDBC full-load giornaliero per data odierna)
   ↓
bronze_giacenze_snapshot   (append daily, partizione per data_snapshot)
   ↓
silver_giacenze_daily      (normalizzata con dimensioni risolte)
silver_giacenze_aggregata  (aggregata per sito + articolo)
   ↓
gold_f_giacenze_daily      (partizione per anno_mese)
gold_f_giacenze_monthly    (aggregazione mensile per reporting)
```

---

## 2. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `SP_REPLICA_LOGISTIX` | CDT_ESTR | `GIACENZE_DAILY@<link>`, `MOVIMENTI_MAGAZZINO@<link>`, `RIEPILOGHI@<link>` | `bronze_giacenze_snapshot`, `bronze_movimenti_mag`, `bronze_riepiloghi` | Bronze | Full-load giornaliero per data odierna; multi-sito loop |
| `SP_ESTRAI_STOCK` / `ESTRAI_STOCK.SP_MAIN` | CDT_ESTR | Tabelle bronze locali | `silver_giacenze_daily` | Silver | Join sito+articolo, lookup dimensioni, calcolo KPI base |
| `SP_LOAD_F_STOCK` STEP0 | CDT_SA | `E_STOCK` (tabella errori) | `silver_giacenze_quarantine` | Silver | Recovery FK non risolte dal ciclo precedente |
| `SP_LOAD_F_STOCK` STEP1 | CDT_SA | `T_STOCK_TMP` staging | `silver_giacenze_aggregata` | Silver | Aggregazione per (sito, articolo, data); calcolo VALORE_STOCK_EUR |
| Load DW | CDT_DW | `T_STOCK_TMP` | `gold_f_giacenze_daily` | Gold | Insert partizione giornaliera; ANALYZE |

---

## 3. Dettaglio procedure e trasformazioni

### 3.1 SP_REPLICA_LOGISTIX → bronze_giacenze_snapshot

**Logica Oracle originale (pseudocodice):**

```sql
-- Per ogni link in S_LOGISTIX (FLAG_ATTIVO = 1):
-- Snapshot completo della giornata corrente:
INSERT INTO GIACENZE_DAILY
  SELECT *, TRUNC(SYSDATE) AS DATA_SNAPSHOT
    FROM GIACENZE_DAILY@<link>
   WHERE GIA_DATA = TRUNC(SYSDATE);
   
-- Snapshot movimenti del giorno:
INSERT INTO MOVIMENTI_MAGAZZINO
  SELECT * FROM MOVIMENTI_MAGAZZINO@<link>
   WHERE MOV_DATA BETWEEN TRUNC(SYSDATE) AND SYSDATE;
COMMIT;
```

**Equivalente PySpark (bronze ingestion — full-load giornaliero):**

```python
# Notebook: bronze/ingest_giacenze_snapshot.py
# Parametro: run_date (widget Databricks)

run_date = dbutils.widgets.get("run_date")  # formato YYYY-MM-DD

for sito in get_active_siti():
    df = (spark.read.format("jdbc")
          .option("url", sito["jdbc_url"])
          .option("dbtable",
                  f"(SELECT *, '{run_date}' AS DATA_SNAPSHOT "
                  f" FROM GIACENZE_DAILY "
                  f" WHERE TRUNC(GIA_DATA) = TO_DATE('{run_date}','YYYY-MM-DD')) t")
          .option("numPartitions", 4)   # stock non necessita alta parallelizzazione
          .option("fetchsize", 5000)
          .load()
          .withColumn("_sito_cod",  F.lit(sito["cod"]))
          .withColumn("_ingest_ts", F.current_timestamp()))

    (df.write.format("delta")
       .mode("append")
       .partitionBy("DATA_SNAPSHOT", "_sito_cod")
       .saveAsTable("logistico.bronze_giacenze_snapshot"))
```

**Nota importante:** Lo snapshot è idempotente — se il job viene rilancato per lo stesso `run_date`, si usa `MERGE` per evitare duplicati:

```python
# Pattern idempotente con MERGE
spark.sql(f"""
  MERGE INTO logistico.bronze_giacenze_snapshot AS target
  USING staging AS source
  ON target.DATA_SNAPSHOT = source.DATA_SNAPSHOT
     AND target._sito_cod  = source._sito_cod
     AND target.GIA_ART_COD = source.GIA_ART_COD
     AND target.GIA_UBL_COD = source.GIA_UBL_COD
  WHEN NOT MATCHED THEN INSERT *
""")
```

---

### 3.2 SP_ESTRAI_STOCK → silver_giacenze_daily

**Logica Oracle originale:**

```sql
-- Join giacenze con dimensioni:
INSERT INTO T_STOCK_TMP
  SELECT
    g.GIA_COD_SITO,
    g.GIA_ART_COD,
    g.GIA_UBL_COD,
    g.DATA_SNAPSHOT,
    g.GIA_QTA_DISPONIBILE,
    g.GIA_QTA_IMPEGNATA,
    g.GIA_QTA_DISPONIBILE + g.GIA_QTA_IMPEGNATA AS QTA_TOTALE,
    g.GIA_PESO_KG,
    g.GIA_VOLUME_M3,
    g.GIA_QTA_DISPONIBILE * a.ART_PREZZO_COSTO AS VALORE_STOCK_EUR,
    s.MAG_SITO_ID,
    a.ART_ID,
    cal.CALENDARIO_ID
  FROM GIACENZE_DAILY g
  LEFT JOIN S_MAG_SITO s   ON s.MAG_SITO_COD = g.GIA_COD_SITO
  LEFT JOIN S_ARTICOLO  a  ON a.ART_COD      = g.GIA_ART_COD
  LEFT JOIN S_CALENDARIO cal ON cal.CAL_DATA = g.DATA_SNAPSHOT
  WHERE g.DATA_SNAPSHOT = TRUNC(SYSDATE);
  
-- Scarti in E_STOCK per FK non risolte
INSERT INTO E_STOCK
  SELECT g.*, 'FK_SITO_MANCANTE' AS ERR_COD
    FROM T_STOCK_TMP g
   WHERE g.MAG_SITO_ID IS NULL;
```

**Equivalente Spark SQL (silver_giacenze_daily):**

```sql
-- silver/transform_giacenze_daily.sql
CREATE OR REPLACE TABLE logistico.silver_giacenze_daily
USING DELTA
PARTITIONED BY (anno_mese, data_snapshot)
AS
SELECT
    g.DATA_SNAPSHOT                                     AS data_snapshot,
    g.GIA_COD_SITO                                      AS sito_cod,
    g.GIA_ART_COD                                       AS articolo_cod,
    g.GIA_UBL_COD                                       AS ubicazione_cod,
    -- Misure stock
    COALESCE(g.GIA_QTA_DISPONIBILE, 0)                  AS qta_disponibile,
    COALESCE(g.GIA_QTA_IMPEGNATA,   0)                  AS qta_impegnata,
    COALESCE(g.GIA_QTA_DISPONIBILE, 0)
      + COALESCE(g.GIA_QTA_IMPEGNATA, 0)                AS qta_totale,
    COALESCE(g.GIA_PESO_KG,         0.0)                AS peso_kg,
    COALESCE(g.GIA_VOLUME_M3,       0.0)                AS volume_m3,
    COALESCE(g.GIA_QTA_DISPONIBILE, 0)
      * COALESCE(a.art_prezzo_costo, 0.0)               AS valore_stock_eur,
    -- FK dimensioni
    COALESCE(s.sito_id,    -1)                          AS sito_id,
    COALESCE(a.articolo_id,-1)                          AS articolo_id,
    COALESCE(cal.calendario_id, -1)                     AS data_snapshot_id,
    -- Audit
    g._sito_cod                                         AS source_sito,
    CURRENT_TIMESTAMP()                                 AS silver_load_ts,
    DATE_FORMAT(g.DATA_SNAPSHOT, 'yyyyMM')              AS anno_mese

FROM logistico.bronze_giacenze_snapshot g
LEFT JOIN logistico.gold_dim_sito       s
    ON s.sito_cod    = g.GIA_COD_SITO
LEFT JOIN logistico.gold_dim_articolo   a
    ON a.articolo_cod = g.GIA_ART_COD
LEFT JOIN logistico.gold_dim_calendario cal
    ON cal.data_effettiva = g.DATA_SNAPSHOT

WHERE g.DATA_SNAPSHOT = '${run_date}'
;
```

---

### 3.3 silver_giacenze_aggregata

Aggregazione giornaliera per (sito, articolo) — elimina la granularità dell'ubicazione per il reporting:

```sql
CREATE OR REPLACE TABLE logistico.silver_giacenze_aggregata
USING DELTA
PARTITIONED BY (anno_mese)
AS
SELECT
    data_snapshot,
    sito_id,
    sito_cod,
    articolo_id,
    articolo_cod,
    anno_mese,
    SUM(qta_disponibile)   AS qta_disponibile,
    SUM(qta_impegnata)     AS qta_impegnata,
    SUM(qta_totale)        AS qta_totale,
    SUM(peso_kg)           AS peso_kg,
    SUM(volume_m3)         AS volume_m3,
    SUM(valore_stock_eur)  AS valore_stock_eur,
    COUNT(*)               AS n_ubicazioni        -- numero ubicazioni con giacenza
FROM logistico.silver_giacenze_daily
WHERE data_snapshot = '${run_date}'
GROUP BY data_snapshot, sito_id, sito_cod, articolo_id, articolo_cod, anno_mese
;
```

---

### 3.4 gold_f_giacenze_monthly

Aggregazione mensile per KPI di fine mese (es. valore stock medio mensile):

```sql
-- Calcolata mensile con job separato schedulato il 1° del mese
CREATE OR REPLACE TABLE logistico.gold_f_giacenze_monthly
USING DELTA
PARTITIONED BY (anno_mese)
AS
SELECT
    anno_mese,
    sito_id,
    articolo_id,
    AVG(qta_disponibile)   AS qta_disponibile_media,
    MAX(qta_disponibile)   AS qta_disponibile_max,
    MIN(qta_disponibile)   AS qta_disponibile_min,
    AVG(valore_stock_eur)  AS valore_stock_medio_eur,
    MAX(valore_stock_eur)  AS valore_stock_max_eur,
    COUNT(DISTINCT data_snapshot) AS giorni_con_giacenza
FROM logistico.gold_f_giacenze_daily
WHERE anno_mese = DATE_FORMAT(DATE_SUB(CURRENT_DATE(), 1), 'yyyyMM')  -- mese precedente
GROUP BY anno_mese, sito_id, articolo_id
;
```

---

## 4. Modello dimensionale gold_f_giacenze

**Grain:** 1 riga = snapshot point-in-time giornaliero per (data, sito, articolo)

### Misure

| Colonna | Tipo | Descrizione | Fonte Oracle |
|---|---|---|---|
| `QTA_DISPONIBILE` | DECIMAL(12,3) | Quantità disponibile per prelievo | `GIACENZE_DAILY.GIA_QTA_DISPONIBILE` |
| `QTA_IMPEGNATA` | DECIMAL(12,3) | Quantità impegnata da ordini aperti | `GIACENZE_DAILY.GIA_QTA_IMPEGNATA` |
| `QTA_TOTALE` | DECIMAL(12,3) | Disponibile + Impegnata | Calcolato |
| `PESO_KG` | DECIMAL(12,3) | Peso totale giacenza in kg | `GIACENZE_DAILY.GIA_PESO_KG` |
| `VOLUME_M3` | DECIMAL(10,4) | Volume occupato in m³ | `GIACENZE_DAILY.GIA_VOLUME_M3` |
| `VALORE_STOCK_EUR` | DECIMAL(15,2) | Valore economico a costo | Calcolato: QTA × prezzo_costo |

### Dimensioni

| Chiave FK | Dimensione | Join key sorgente |
|---|---|---|
| `sito_id` | `gold_dim_sito` | `GIACENZE_DAILY.GIA_COD_SITO` |
| `articolo_id` | `gold_dim_articolo` | `GIACENZE_DAILY.GIA_ART_COD` |
| `data_snapshot_id` | `gold_dim_calendario` | `DATA_SNAPSHOT` |

---

## 5. KPI Giacenze: definizioni e implementazione

### 5.1 Saturazione Magazzino

**Definizione:** Percentuale di capacità cubica occupata per sito.

**Implementazione Spark SQL:**

```sql
-- Vista gold per KPI saturazione (richiede tabella gold_dim_sito con CAPACITA_M3)
CREATE OR REPLACE VIEW logistico.gold_kpi_saturazione_magazzino AS
SELECT
    g.data_snapshot,
    g.sito_id,
    s.sito_cod,
    s.sito_desc,
    SUM(g.volume_m3)                    AS volume_occupato_m3,
    s.capacita_m3_totale,
    ROUND(
      SUM(g.volume_m3) / s.capacita_m3_totale * 100,
      2
    )                                   AS saturazione_pct,
    CASE
      WHEN SUM(g.volume_m3) / s.capacita_m3_totale > 0.95 THEN 'CRITICO'
      WHEN SUM(g.volume_m3) / s.capacita_m3_totale > 0.85 THEN 'ATTENZIONE'
      ELSE 'OK'
    END                                 AS stato_saturazione
FROM logistico.gold_f_giacenze_daily    g
JOIN logistico.gold_dim_sito            s ON s.sito_id = g.sito_id
GROUP BY g.data_snapshot, g.sito_id, s.sito_cod, s.sito_desc, s.capacita_m3_totale
;
```

### 5.2 Aging Articoli (giorni in giacenza)

**Definizione:** Numero di giorni consecutivi in cui un articolo ha avuto giacenza positiva. Identifica articoli a rischio di obsolescenza.

**Implementazione con Window Function:**

```sql
-- Vista gold per KPI aging articoli
CREATE OR REPLACE VIEW logistico.gold_kpi_aging_articoli AS
WITH giacenze_con_flag AS (
  SELECT
    sito_id,
    articolo_id,
    data_snapshot,
    qta_disponibile,
    -- Flag: l'articolo aveva giacenza il giorno precedente?
    LAG(qta_disponibile, 1, 0)
      OVER (PARTITION BY sito_id, articolo_id
            ORDER BY data_snapshot)        AS qta_giorno_prec
  FROM logistico.gold_f_giacenze_daily
  WHERE qta_disponibile > 0
),
gruppi_continuita AS (
  SELECT *,
    -- Tecnica "gaps and islands": identifica inizio di nuovo periodo continuativo
    ROW_NUMBER() OVER (PARTITION BY sito_id, articolo_id ORDER BY data_snapshot)
    - ROW_NUMBER() OVER (PARTITION BY sito_id, articolo_id, 
                          (CASE WHEN qta_giorno_prec > 0 THEN 1 ELSE 0 END)
                         ORDER BY data_snapshot)  AS island_id
  FROM giacenze_con_flag
)
SELECT
    sito_id,
    articolo_id,
    MIN(data_snapshot)                  AS primo_giorno_giacenza,
    MAX(data_snapshot)                  AS ultimo_giorno_giacenza,
    COUNT(*)                            AS giorni_in_giacenza,
    DATEDIFF(MAX(data_snapshot),
             MIN(data_snapshot)) + 1    AS giorni_range,
    CASE
      WHEN COUNT(*) > 180 THEN 'CRITICO'
      WHEN COUNT(*) > 90  THEN 'ATTENZIONE'
      ELSE 'OK'
    END                                 AS stato_aging
FROM gruppi_continuita
GROUP BY sito_id, articolo_id, island_id
;
```

---

## 6. Rischi di migrazione

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | Snapshot giornaliero: volume stimato 5-10M righe/giorno × siti | Alta | Alto | Partizione per `(DATA_SNAPSHOT, _sito_cod)` su bronze; ottimizzare con Z-ORDER su `articolo_cod` |
| 2 | Full-load giornaliero vs incrementale: nessuna colonna watermark su GIACENZE_DAILY | Alta | Basso | Confermato: il full-load per data è il pattern corretto (snapshot); durata stimata 15-20 min |
| 3 | VALORE_STOCK_EUR: prezzo_costo da ART_ARTICOLI può variare — storico corretto? | Media | Alto | Usare prezzo_costo alla data dello snapshot (SCD Type 2 su gold_dim_articolo) |
| 4 | Capacita_m3_totale per sito: attributo non in sorgente Logistix | Alta | Medio | Acquisire da fonte manuale (Excel) → tabella di riferimento `silver_config_capacita_siti` |
| 5 | Ore di estrazione Logistix: snapshot estratto a fine giornata operativa (es. 23:00), non a mezzanotte | Media | Medio | Configurare run_date = data lavorativa, non data calendario |
