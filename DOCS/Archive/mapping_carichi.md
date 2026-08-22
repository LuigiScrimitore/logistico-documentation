# Mapping PL/SQL → Spark SQL — Area Carichi (Entrata Merci)

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica del flusso Oracle AS-IS](#1-panoramica-del-flusso-oracle-as-is)
2. [Tabella di mapping procedure](#2-tabella-di-mapping-procedure)
3. [Dettaglio procedure e trasformazioni](#3-dettaglio-procedure-e-trasformazioni)
4. [Modello dimensionale gold_f_carico](#4-modello-dimensionale-gold_f_carico)
5. [Late-Arriving Dimensions e gestione scarti](#5-late-arriving-dimensions-e-gestione-scarti)
6. [Rischi di migrazione consolidati](#6-rischi-di-migrazione-consolidati)

---

## 1. Panoramica del flusso Oracle AS-IS

Il flusso Oracle per l'area Carichi si articola su tre schemi:

```
Logistix (sorgente operativa)
   ↓  DB Link
CDT_ESTR.SP_REPLICA_CARICHI  →  STO_TES_CARICHI, STO_DET_CARICHI, PESATE, TRACCIACE178
   ↓
CDT_ESTR.SP_ESTRAI_CARICO    →  ESTRAI_CARICO.SP_MAIN + ESTRAI_OPER_RICEV.SP_MAIN
   ↓
CDT_SA.SP_LOAD_F_CARICO      →  T_CARICO_TMP_P2 (STEP0 → STEP1 → STEP2)
   ↓
CDT_DW.F_CARICO              →  Fact table finale esposta a MicroStrategy
```

Il meccanismo di watermark è basato sulla colonna `STCAR_DATA_ESTRAZIONE_DWH` (e analoghe `PSP_DATA_ESTRAZIONE_DWH`, `CE178_DATA_ESTRAZIONE_DWH`) sulle tabelle sorgente Logistix. La procedura `ANNULLA_DATE` consente di annullare watermark in un intervallo di date per riprocessare i dati.

**Flusso Databricks target:**

```
Oracle Logistix (JDBC incremental)
   ↓
bronze_sto_tes_carichi  /  bronze_sto_det_carichi  /  bronze_pesate
   ↓
silver_carichi  (staging + normalizzazione)
   ↓
gold_f_carico   (Delta Lake, partizione per ANNO_MESE)
```

---

## 2. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `SP_REPLICA_CARICHI` | CDT_ESTR | `STO_TES_CARICHI@<logistix_link>`, `STO_DET_CARICHI@<logistix_link>`, `PESATE@<logistix_link>` | `bronze_sto_tes_carichi`, `bronze_sto_det_carichi`, `bronze_pesate` | Bronze | Copia incrementale via watermark `STCAR_DATA_ESTRAZIONE_DWH`; multi-sito via loop su `S_LOGISTIX` |
| `SP_ESTRAI_CARICO` (delega a `ESTRAI_CARICO.SP_MAIN`) | CDT_ESTR | `STO_TES_CARICHI`, `STO_DET_CARICHI`, `PESATE` (locale post-replica) | `silver_carichi` | Silver | Join testata-dettaglio, arricchimento con PESATE, lookup dimensioni, gestione errori in `E_CARICO` |
| `SP_LOAD_F_CARICO` STEP0 | CDT_SA | `E_CARICO` (tabella errori) | `silver_carichi_recovery` | Silver | Recupero record in errore dal ciclo precedente (retry logic) |
| `SP_LOAD_F_CARICO` STEP1 | CDT_SA | Staging locale | `T_CARICO_TMP` | Silver | Caricamento staging con lookup FK dimensioni; scarti in `E_CARICO` |
| `SP_LOAD_F_CARICO` STEP2 | CDT_SA | `T_CARICO_TMP` | `T_CARICO_TMP_P2` | Silver | Calcolo campi derivati: DELTA_QTA, LEAD_TIME_GG, flags qualità |
| `SP_LOAD_F_CARICO` (caricamento DW) | CDT_DW | `T_CARICO_TMP_P2` | `gold_f_carico` | Gold | Insert/merge nella fact table partita; rebuild indici; ANALYZE |

---

## 3. Dettaglio procedure e trasformazioni

### 3.1 SP_REPLICA_CARICHI → bronze layer

**Logica Oracle originale (pseudocodice):**

```sql
-- Per ogni link in S_LOGISTIX (FLAG_ATTIVO = 1):
INSERT INTO STO_TES_CARICHI
  SELECT * FROM STO_TES_CARICHI@<link>
   WHERE STCAR_DATA_ESTRAZIONE_DWH IS NULL;

-- Marca i record estratti:
UPDATE STO_TES_CARICHI@<link>
   SET STCAR_DATA_ESTRAZIONE_DWH = SYSDATE_NUMBER
 WHERE STCAR_DATA_ESTRAZIONE_DWH IS NULL;

-- Analogo per PESATE (PSP_DATA_ESTRAZIONE_DWH)
-- Analogo per TRACCIACE178 (CE178_DATA_ESTRAZIONE_DWH)
-- Analogo per IMBFMOVIM (IMF_DATA_ESTRAZIONE_DWH)
COMMIT;
```

**Business rule implicita:** Il sistema gestisce più siti logistici (magazzini) con DB Link separati. Ogni sito ha una propria istanza Logistix. La replica è sequenziale per sito.

**Equivalente PySpark/Spark SQL (bronze ingestion):**

```python
# Notebook: bronze/ingest_carichi.py
# Parametro: run_date (default: today)

from pyspark.sql import functions as F
from datetime import date

WATERMARK_COL = "STCAR_DATA_ESTRAZIONE_DWH"
BRONZE_TABLE  = "logistico.bronze_sto_tes_carichi"

# Legge incrementale da Oracle via JDBC per ogni sito
for sito in get_active_siti():  # da tabella config silver_config_siti
    df = (spark.read.format("jdbc")
          .option("url", sito["jdbc_url"])
          .option("dbtable",
                  f"(SELECT * FROM STO_TES_CARICHI "
                  f" WHERE {WATERMARK_COL} IS NULL) t")
          .option("user", sito["user"])
          .option("password", sito["password"])
          .option("numPartitions", 8)
          .option("fetchsize", 10000)
          .load()
          .withColumn("_sito_cod",   F.lit(sito["cod"]))
          .withColumn("_ingest_ts",  F.current_timestamp())
          .withColumn("_source_link", F.lit(sito["link_name"])))

    (df.write.format("delta")
       .mode("append")
       .option("mergeSchema", "false")
       .saveAsTable(BRONZE_TABLE))

# NOTA: il watermark viene aggiornato sulla sorgente Oracle
# tramite job separato CDT_ESTR dopo conferma del caricamento.
# In Databricks la conferma si fa con un flag nella tabella
# bronze_ingest_control invece di aggiornare la sorgente.
```

**Rischi:**
- Il loop multi-sito in Oracle è sequenziale; in Databricks si può parallelizzare con `ThreadPoolExecutor` o più job task in parallelo nel workflow.
- La modifica del watermark sulla sorgente (`UPDATE ... SET STCAR_DATA_ESTRAZIONE_DWH`) implica un write-back su Oracle: va concordato con il team Logistix se mantenere questo meccanismo o adottare un watermark interno Databricks.

---

### 3.2 SP_ESTRAI_CARICO → silver layer

**Logica Oracle originale (pseudocodice):**

```sql
-- ESTRAI_CARICO.SP_MAIN:
-- 1. Join STO_TES_CARICHI (testate) con STO_DET_CARICHI (dettagli)
-- 2. Arricchimento con PESATE (peso lordo/netto per pesata)
-- 3. Lookup DIM_FORNITORE (da ART_ARTICOLI, FORNITORI)
-- 4. Lookup DIM_ARTICOLO
-- 5. Lookup DIM_SITO (da MAG_SITI)
-- 6. Lookup DIM_CALENDARIO (conversione data numerica → ID)
-- 7. Calcolo DELTA_QTA = QTA_RICEVUTA - QTA_ATTESA
-- 8. Calcolo LEAD_TIME_GG = DATA_ARRIVO - DATA_PREVISTA_ARRIVO
-- 9. Scarti in E_CARICO per FK non risolte
```

**Equivalente Spark SQL (silver_carichi):**

```sql
-- silver/transform_carichi.sql
CREATE OR REPLACE TABLE logistico.silver_carichi
USING DELTA
PARTITIONED BY (anno_mese)
AS
SELECT
    t.STCAR_ID                                    AS carico_id,
    t.STCAR_NUM_DOC                               AS num_doc_carico,
    t.STCAR_COD_FORNITORE                         AS fornitore_cod,
    t.STCAR_COD_SITO                              AS sito_cod,
    CAST(t.STCAR_DATA_ARRIVO AS DATE)             AS data_arrivo,
    CAST(t.STCAR_DATA_PREV_ARRIVO AS DATE)        AS data_prev_arrivo,
    d.STDET_COD_ARTICOLO                          AS articolo_cod,
    d.STDET_QTA_ATTESA                            AS qta_attesa,
    d.STDET_QTA_RICEVUTA                          AS qta_ricevuta,
    (d.STDET_QTA_RICEVUTA - d.STDET_QTA_ATTESA)  AS delta_qta,
    DATEDIFF(
        CAST(t.STCAR_DATA_ARRIVO AS DATE),
        CAST(t.STCAR_DATA_PREV_ARRIVO AS DATE)
    )                                             AS lead_time_gg,
    p.PSP_PESO_NETTO                              AS peso_netto,
    p.PSP_PESO_LORDO                              AS peso_lordo,
    -- Lookup dimensioni (LEFT JOIN per gestire LAD)
    f.fornitore_id,
    a.articolo_id,
    s.sito_id,
    cal.calendario_id                             AS data_arrivo_id,
    cal_prev.calendario_id                        AS data_prev_arrivo_id,
    -- Audit
    t._sito_cod                                   AS source_sito,
    t._ingest_ts                                  AS bronze_ingest_ts,
    CURRENT_TIMESTAMP()                           AS silver_load_ts,
    -- Partizione
    DATE_FORMAT(CAST(t.STCAR_DATA_ARRIVO AS DATE), 'yyyyMM') AS anno_mese

FROM logistico.bronze_sto_tes_carichi   t
JOIN logistico.bronze_sto_det_carichi   d
    ON t.STCAR_ID = d.STDET_STCAR_ID
    AND t._sito_cod = d._sito_cod
LEFT JOIN logistico.bronze_pesate       p
    ON p.PSP_STCAR_ID = t.STCAR_ID
    AND p._sito_cod = t._sito_cod
LEFT JOIN logistico.gold_dim_fornitore  f
    ON f.fornitore_cod = t.STCAR_COD_FORNITORE
LEFT JOIN logistico.gold_dim_articolo   a
    ON a.articolo_cod = d.STDET_COD_ARTICOLO
LEFT JOIN logistico.gold_dim_sito       s
    ON s.sito_cod = t.STCAR_COD_SITO
LEFT JOIN logistico.gold_dim_calendario cal
    ON cal.data_effettiva = CAST(t.STCAR_DATA_ARRIVO AS DATE)
LEFT JOIN logistico.gold_dim_calendario cal_prev
    ON cal_prev.data_effettiva = CAST(t.STCAR_DATA_PREV_ARRIVO AS DATE)

WHERE t._ingest_ts > (SELECT MAX(silver_load_ts) FROM logistico.silver_carichi)
  -- solo nuovi record bronze non ancora processati
;
```

**Business rules implicite:**
- Un carico (testata) può avere N righe di dettaglio; ogni riga è una coppia (articolo, quantità).
- Le PESATE possono essere assenti (pesatura non obbligatoria per tutti i fornitori): LEFT JOIN.
- `STCAR_DATA_ESTRAZIONE_DWH` in Oracle è un intero numerico `YYYYMMDDHH24MI`; in Databricks si converte in TIMESTAMP.

---

### 3.3 SP_LOAD_F_CARICO STEP0-2 → gold layer

**Logica Oracle originale — STEP0 (recovery errori):**

```sql
-- Riprende record in errore (FK non risolte) dal ciclo precedente
INSERT INTO T_CARICO_TMP
  SELECT * FROM E_CARICO
   WHERE ERR_ID IN (100, 101, 102)   -- codici errore FK mancante
     AND LOAD_ID = prev_load_id;
```

**Equivalente PySpark — pattern recovery:**

```python
# Invece di E_CARICO, usiamo silver_carichi_quarantine
recovery_df = (spark.table("logistico.silver_carichi_quarantine")
               .filter(F.col("error_code").isin(["DIM_FK_MISSING"])
                     & (F.col("load_id") == prev_load_id))
               .drop("error_code", "quarantine_ts"))

# Tenta re-risoluzione FK (dimensioni potrebbero essere arrivate)
recovery_enriched = resolve_dimensions(recovery_df)
```

**Logica Oracle — STEP2 (campi calcolati):**

```sql
INSERT INTO T_CARICO_TMP_P2
  SELECT t.*,
         t.QTA_RICEVUTA - t.QTA_ATTESA            AS DELTA_QTA,
         TRUNC(t.DATA_ARRIVO) - TRUNC(t.DATA_PREV_ARRIVO)
                                                   AS LEAD_TIME_GG,
         CASE WHEN (t.QTA_RICEVUTA - t.QTA_ATTESA) < 0
              THEN 'MENO'
              WHEN (t.QTA_RICEVUTA - t.QTA_ATTESA) > 0
              THEN 'PIU'
              ELSE 'PARI'
         END                                       AS FLAG_DELTA,
         CASE WHEN p.PSP_PESO_NETTO IS NULL THEN 0
              ELSE p.PSP_PESO_NETTO
         END                                       AS PESO_NETTO_SAFE
    FROM T_CARICO_TMP t
    LEFT JOIN PESATE p ON p.PSP_STCAR_ID = t.CARICO_ID;
```

**Equivalente Spark SQL (gold_f_carico):**

```sql
-- gold/load_f_carico.sql
MERGE INTO logistico.gold_f_carico AS target
USING (
  SELECT
    c.carico_id,
    c.num_doc_carico,
    c.fornitore_id,
    c.articolo_id,
    c.sito_id,
    c.data_arrivo_id,
    c.data_prev_arrivo_id,
    -- Misure
    COALESCE(c.peso_netto,  0.0)      AS peso_netto,
    COALESCE(c.peso_lordo,  0.0)      AS peso_lordo,
    c.qta_ricevuta,
    c.qta_attesa,
    c.delta_qta,
    c.lead_time_gg,
    CASE WHEN c.delta_qta < 0 THEN 'MENO'
         WHEN c.delta_qta > 0 THEN 'PIU'
         ELSE 'PARI'
    END                               AS flag_delta,
    -- Audit
    CURRENT_DATE()                    AS data_load,
    '${run_date}'                     AS run_date
  FROM logistico.silver_carichi c
  WHERE c.fornitore_id  IS NOT NULL  -- solo record con FK risolte
    AND c.articolo_id   IS NOT NULL
    AND c.sito_id       IS NOT NULL
) AS source
ON target.carico_id = source.carico_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

---

## 4. Modello dimensionale gold_f_carico

**Grain:** 1 riga = 1 riga dettaglio carico (combinazione STCAR_ID + STDET_SEQ)

### Misure

| Colonna | Tipo | Descrizione | Fonte Oracle |
|---|---|---|---|
| `PESO_NETTO` | DECIMAL(12,3) | Peso netto in kg dalla pesata | `PESATE.PSP_PESO_NETTO` |
| `PESO_LORDO` | DECIMAL(12,3) | Peso lordo in kg dalla pesata | `PESATE.PSP_PESO_LORDO` |
| `QTA_RICEVUTA` | DECIMAL(12,3) | Quantità effettivamente ricevuta | `STO_DET_CARICHI.STDET_QTA_RICEVUTA` |
| `QTA_ATTESA` | DECIMAL(12,3) | Quantità attesa da ordine | `STO_DET_CARICHI.STDET_QTA_ATTESA` |
| `DELTA_QTA` | DECIMAL(12,3) | QTA_RICEVUTA - QTA_ATTESA | Calcolato (STEP2) |
| `LEAD_TIME_GG` | INTEGER | Giorni tra data prevista e data arrivo | Calcolato (STEP2) |

### Dimensioni

| Chiave FK | Dimensione | Join key sorgente |
|---|---|---|
| `fornitore_id` | `gold_dim_fornitore` | `STO_TES_CARICHI.STCAR_COD_FORNITORE` |
| `articolo_id` | `gold_dim_articolo` | `STO_DET_CARICHI.STDET_COD_ARTICOLO` |
| `sito_id` | `gold_dim_sito` | `STO_TES_CARICHI.STCAR_COD_SITO` |
| `data_arrivo_id` | `gold_dim_calendario` | `STO_TES_CARICHI.STCAR_DATA_ARRIVO` |
| `data_prev_arrivo_id` | `gold_dim_calendario` | `STO_TES_CARICHI.STCAR_DATA_PREV_ARRIVO` |

---

## 5. Late-Arriving Dimensions e gestione scarti

### Problema LAD in Oracle

In Oracle, i record con FK non risolte vengono inseriti in `E_CARICO` (tabella errori). Ad ogni ciclo successivo, lo STEP0 tenta di recuperarli (la dimensione potrebbe essere arrivata nel frattempo). I codici errore tipici:

| Codice errore Oracle | Significato | Gestione Databricks |
|---|---|---|
| 270607 (es.) | `OPER_PREP_COD` non trovata in S_OPER_PREP | Quarantena, retry al ciclo successivo |
| 270608 | `MAG_SITO_COD` non trovata | Quarantena con alert se > 24h |
| FK_FORNITORE | Fornitore non presente in DIM_FORNITORE | Default surrogate key -1 ("Sconosciuto") |
| FK_ARTICOLO | Articolo non presente in DIM_ARTICOLO | Default surrogate key -1 |

### Strategia Databricks per LAD

```python
# Pattern consigliato: surrogate key -1 + tabella quarantena

from pyspark.sql import functions as F

# Risoluzione FK con default -1 per dimensioni mancanti
df_silver = df_bronze.alias("b") \
    .join(dim_fornitore.alias("f"),
          F.col("b.STCAR_COD_FORNITORE") == F.col("f.fornitore_cod"),
          how="left") \
    .withColumn("fornitore_id", 
                F.coalesce(F.col("f.fornitore_id"), F.lit(-1)))

# Scrittura quarantena per record con FK mancante
df_quarantine = df_silver.filter(F.col("fornitore_id") == -1)
df_quarantine.write.format("delta").mode("append") \
    .saveAsTable("logistico.silver_carichi_quarantine")

# Logging metrica quarantena
quarantine_count = df_quarantine.count()
if quarantine_count > 0:
    log_metric("carichi_lad_count", quarantine_count)
    if quarantine_count / total_count > 0.05:
        raise Exception(f"LAD rate {quarantine_count/total_count:.1%} > soglia 5%")
```

### Gestione scarti

I record in quarantena vengono rielaborati quotidianamente dal notebook `silver/retry_lad_carichi.py` che:
1. Legge `silver_carichi_quarantine` ordinato per `bronze_ingest_ts`
2. Ritenta la risoluzione FK
3. Promuove i record risolti in `silver_carichi`
4. Mantiene in quarantena con `retry_count += 1`; dopo 5 tentativi scrive in `silver_carichi_rejected` e notifica via email

---

## 6. Rischi di migrazione consolidati

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | Write-back watermark su Oracle Logistix non autorizzato | Media | Alto | Concordare con team Logistix meccanismo alternativo (es. tabella shadow CDT_ESTR.WATERMARK_CTR) |
| 2 | Date numeriche Oracle (YYYYMMDDHH24MI) in STCAR_DATA_ESTRAZIONE_DWH | Alta | Medio | Cast esplicito nel notebook bronze: `TO_TIMESTAMP(CAST(col AS STRING), 'yyyyMMddHHmm')` |
| 3 | Multi-sito: numero di siti Logistix variabile | Bassa | Medio | Gestire lista siti da tabella config Delta `silver_config_siti`; aggiunta nuovo sito = INSERT in tabella, no deploy |
| 4 | NULL su PESATE (pesatura opzionale) | Alta | Basso | LEFT JOIN + COALESCE a 0 già previsto |
| 5 | Volume STO_DET_CARICHI: stimato 50M+ righe storiche | Alta | Alto | Partitionamento JDBC per DATA_ARRIVO; `numPartitions=16` per backfill storico |
| 6 | Parallelismo JDBC vs connessioni Oracle | Media | Medio | Negoziare con DBA Oracle il numero max connessioni; usare connection pool |
