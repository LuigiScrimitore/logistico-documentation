# Mapping PL/SQL → Spark SQL — Area Trasporti

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica del flusso Oracle AS-IS](#1-panoramica-del-flusso-oracle-as-is)
2. [Tabella di mapping procedure](#2-tabella-di-mapping-procedure)
3. [Dettaglio procedure e trasformazioni](#3-dettaglio-procedure-e-trasformazioni)
4. [Logica Fill Rate](#4-logica-fill-rate)
5. [Logica costo trasporto: fasce peso contrattuali](#5-logica-costo-trasporto-fasce-peso-contrattuali)
6. [Gestione SWAP](#6-gestione-swap)
7. [Modello dimensionale gold_f_trasp](#7-modello-dimensionale-gold_f_trasp)
8. [Rischi di migrazione](#8-rischi-di-migrazione)

---

## 1. Panoramica del flusso Oracle AS-IS

```
AtTraspo (sistema ordini trasporto) + Logistix
   ↓  DB Link / Staging
CDT_ESTR.SP_REPLICA_ORDINI    →  ORDINI_TESTATE, ORDINI_RIGHE
CDT_ESTR.SP_REPLICA_TRASP     →  TRASPORTI, ESTRAI_SPEDIZIONI, ESTRAI_RESIDAPDV
CDT_ESTR.SP_REPLICA_TRASP_REC_STORICO → backfill storico trasporti
   ↓  (sorgente SWAP da sistema terzo)
CDT_ESTR.IMPORT_TRASPO92_SNAP →  SWAP (tabelle snapshot da AtTraspo92)
   ↓
CDT_SA.T_ORDINI               →  staging ordini normalizzati
CDT_SA.T_TRASP_*              →  staging trasporti normalizzati
   ↓
CDT_SA.SP_LOAD_F_ORD_FORN_RIGHE    →  staging fact ordini righe
CDT_SA.SP_LOAD_F_ORD_FORN_TESTATE →  staging fact ordini testate
CDT_SA.SP_LOAD_F_TRASP_MTV         →  gold F_TRASP_MTV (movimentazione)
CDT_SA.SP_LOAD_F_TRASP_TRATTA      →  gold F_TRASP_TRATTA (tratte/percorsi)
CDT_SA.SP_LOAD_F_TRASP_TRATTA_BOLLA → gold F_TRASP_TRATTA_BOLLA
   ↓
CDT_DW.F_TRASP_MTV / F_TRASP_TRATTA → Fact tables MicroStrategy
```

**Flusso Databricks target:**

```
Oracle AtTraspo (JDBC incremental)  +  Oracle Logistix (JDBC incremental)
   ↓
bronze_ordini_testate / bronze_ordini_righe
bronze_trasporti / bronze_estrai_spedizioni / bronze_swap
   ↓
silver_ordini      (join testata-riga, normalizzazione)
silver_trasporti   (con calcolo costo fasce peso, fill rate)
   ↓
gold_f_ordini_righe  / gold_f_ordini_testate
gold_f_trasp_mtv     / gold_f_trasp_tratta / gold_f_trasp_tratta_bolla
```

---

## 2. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `SP_REPLICA_ORDINI` | CDT_ESTR | `ORDINI_TESTATE@attraspo`, `ORDINI_RIGHE@attraspo` | `bronze_ordini_testate`, `bronze_ordini_righe` | Bronze | Incrementale via data ordine; gestione ANNULLA_DATE per re-estrazione |
| `SP_REPLICA_TRASP` | CDT_ESTR | `ESTRAI_SPEDIZIONI` (flag `ESTRAI_SP_ESTRATTO_DWH='N'`), `ESTRAI_RESIDAPDV` | `bronze_estrai_spedizioni`, `bronze_residui_pdv` | Bronze | Flag-based: marca `ESTRATTO_DWH='S'` dopo estrazione (NO watermark data) |
| `SP_REPLICA_TRASPORTI` | CDT_ESTR | `TRASPORTI@attraspo` | `bronze_trasporti` | Bronze | Full giornaliero su finestra temporale |
| `IMPORT_TRASPO92_SNAP` | CDT_ESTR | `TRASPO92_SNAP_OBJ_LIST` → tabelle snapshot AtTraspo92 | `bronze_swap` | Bronze | Snapshot periodico tabelle AtTraspo legacy (CREATE OR TRUNCATE+INSERT) |
| `SP_LOAD_F_ORD_FORN_RIGHE` | CDT_SA/DW | Staging `T_ORDINI` | `gold_f_ord_forn_righe` | Gold | Calcolo fill rate riga, lookup dimensioni |
| `SP_LOAD_F_ORD_FORN_TESTATE` | CDT_SA/DW | Staging testate | `gold_f_ord_forn_testate` | Gold | Aggregazione a livello testata |
| `SP_LOAD_F_TRASP_MTV` | CDT_DW | Staging trasporti `T_MOV_CARR_TMP` | `gold_f_trasp_mtv` | Gold | Carico fact movimentazione; STEP2; rebuild indici |
| `SP_LOAD_F_TRASP_TRATTA` | CDT_DW | Staging tratte | `gold_f_trasp_tratta` | Gold | Costo trasporto con fasce peso |
| `SP_LOAD_F_TRASP_TRATTA_BOLLA` | CDT_DW | Staging tratte×bolla | `gold_f_trasp_tratta_bolla` | Gold | Dettaglio costo per bolla |

---

## 3. Dettaglio procedure e trasformazioni

### 3.1 SP_REPLICA_TRASP → bronze_estrai_spedizioni

**Meccanismo di watermark alternativo Oracle:**

A differenza dei carichi (watermark su data), i trasporti usano un flag:

```sql
-- Estrazione:
INSERT INTO ESTRAI_SPEDIZIONI_LOCAL
  SELECT * FROM ESTRAI_SPEDIZIONI
   WHERE ESTRAI_SP_ESTRATTO_DWH = 'N';

-- Marca estratto:
UPDATE ESTRAI_SPEDIZIONI
   SET ESTRAI_SP_ESTRATTO_DWH       = 'S',
       ESTRAI_SP_DATA_ESTRAZIONE_DWH = SYSDATE_NUMBER
 WHERE ESTRAI_SP_ESTRATTO_DWH = 'N';
COMMIT;
```

**Equivalente PySpark:**

```python
# bronze/ingest_trasporti.py
# Legge solo record non ancora estratti

df_spedizioni = (spark.read.format("jdbc")
    .option("url", attraspo_jdbc_url)
    .option("dbtable",
            "(SELECT * FROM ESTRAI_SPEDIZIONI "
            " WHERE ESTRAI_SP_ESTRATTO_DWH = 'N') t")
    .option("numPartitions", 4)
    .load()
    .withColumn("_ingest_ts", F.current_timestamp()))

(df_spedizioni.write.format("delta")
 .mode("append")
 .saveAsTable("logistico.bronze_estrai_spedizioni"))

# Il write-back del flag su Oracle va mantenuto per coerenza con sistema legacy
# durante il periodo shadow mode; dopo il cutover, il flag non sarà più necessario
```

### 3.2 IMPORT_TRASPO92_SNAP → bronze_swap

**Logica Oracle:** Per ogni tabella in `TRASPO92_SNAP_OBJ_LIST` con `FLAG_SNAP_ACTIVE=1`:
1. Se la tabella target non esiste → `CREATE TABLE AS SELECT`
2. Se esiste → `TRUNCATE` + `INSERT`
3. Aggiorna `LAST_SNAP` e `NUM_RECORD`

```python
# bronze/ingest_swap_snapshot.py
# Equivalente Databricks: TRUNCATE + INSERT giornaliero (full-load)

SWAP_TABLES = [
    {"source": "CONTRATTI_CORRIERI", "target": "bronze_swap_contratti_corrieri"},
    {"source": "SWAP",               "target": "bronze_swap_ordini"},
    # ...altri da TRASPO92_SNAP_OBJ_LIST
]

for tbl in SWAP_TABLES:
    df = spark.read.format("jdbc")...load()
    spark.sql(f"DELETE FROM logistico.{tbl['target']} WHERE data_snapshot = '{run_date}'")
    (df.withColumn("data_snapshot", F.lit(run_date))
       .write.format("delta").mode("append")
       .saveAsTable(f"logistico.{tbl['target']}"))
```

---

## 4. Logica Fill Rate

### Definizione

Il Fill Rate misura il livello di soddisfazione degli ordini: quanta parte di ciò che è stato ordinato è stato effettivamente consegnato.

```
Fill Rate = SUM(QTA_CONSEGNATA) / SUM(QTA_ORDINATA)
```

### Perché si calcola sia a livello riga che aggregato

**Fill Rate a livello riga (riga ordine):**

```sql
-- gold/load_f_ord_forn_righe.sql
SELECT
    ordine_id,
    riga_id,
    articolo_id,
    pdv_id,
    data_ordine_id,
    qta_ordinata,
    qta_consegnata,
    qta_ordinata - qta_consegnata                     AS qta_inevasa,
    CASE
      WHEN qta_ordinata = 0 THEN NULL
      ELSE ROUND(qta_consegnata / qta_ordinata, 4)
    END                                               AS fill_rate_riga,
    CASE
      WHEN qta_consegnata >= qta_ordinata THEN 'PIENO'
      WHEN qta_consegnata > 0            THEN 'PARZIALE'
      ELSE                                    'INEVASO'
    END                                               AS stato_riga
FROM logistico.silver_ordini
```

**Motivazione:** Il fill rate a livello riga identifica i **singoli articoli** problematici. Permette di rispondere a domande come "quali articoli hanno fill rate < 90% sistematicamente?".

**Fill Rate aggregato (per testata ordine / per PDV / per periodo):**

```sql
-- gold/load_f_ord_forn_testate.sql
SELECT
    data_ordine_id,
    fornitore_id,
    pdv_id,
    COUNT(DISTINCT ordine_id)                         AS n_ordini,
    SUM(qta_ordinata)                                 AS qta_ordinata_tot,
    SUM(qta_consegnata)                               AS qta_consegnata_tot,
    CASE
      WHEN SUM(qta_ordinata) = 0 THEN NULL
      ELSE ROUND(SUM(qta_consegnata) / SUM(qta_ordinata), 4)
    END                                               AS fill_rate_aggregato,
    -- Fill rate "ordini pieni": % ordini con fill rate = 100%
    ROUND(
      SUM(CASE WHEN qta_consegnata >= qta_ordinata THEN 1 ELSE 0 END)
      / COUNT(*),
      4
    )                                                 AS fill_rate_ordini_pieni
FROM logistico.silver_ordini
GROUP BY data_ordine_id, fornitore_id, pdv_id
```

**Motivazione:** Il fill rate aggregato è la **metrica KPI** di business che appare nei report MicroStrategy. Calcolarlo sia a livello riga che aggregato permette:
1. **Drill-down:** dal KPI aggregato all'articolo specifico che abbassa il fill rate
2. **Coerenza:** `SUM(qta_consegnata_riga) / SUM(qta_ordinata_riga) = fill_rate_aggregato` — verificabile matematicamente
3. **Evitare l'average of averages trap:** fare `AVG(fill_rate_riga)` darebbe un risultato diverso da `SUM/SUM` perché pesa ugualmente righe con quantità molto diverse

---

## 5. Logica costo trasporto: fasce peso contrattuali

### Struttura contrattuale Oracle

I contratti corrieri definiscono fasce di peso con costo unitario differenziato (tariffario a scaglioni). La logica è implementata con `CASE WHEN` nella fase di calcolo del costo tratta.

**Logica Oracle (pseudocodice da LOAD_F_TRASP_TRATTA):**

```sql
-- Calcolo costo trasporto per tratta:
costo_tratta =
  CASE
    WHEN peso_lordo_kg BETWEEN  0   AND  50  THEN peso_lordo_kg * tariffa_0_50
    WHEN peso_lordo_kg BETWEEN  51  AND 100  THEN peso_lordo_kg * tariffa_51_100
    WHEN peso_lordo_kg BETWEEN 101  AND 300  THEN peso_lordo_kg * tariffa_101_300
    WHEN peso_lordo_kg BETWEEN 301  AND 500  THEN peso_lordo_kg * tariffa_301_500
    WHEN peso_lordo_kg BETWEEN 501  AND 1000 THEN peso_lordo_kg * tariffa_501_1000
    WHEN peso_lordo_kg > 1000                THEN peso_lordo_kg * tariffa_oltre_1000
    ELSE 0
  END
  + quota_fissa_viaggio  -- costo fisso per viaggio indipendente dal peso
  + supplemento_pedaggio -- se corridoio autostradale
```

**Implementazione Spark SQL con lookup tabella contratti:**

```sql
-- silver/calc_costo_trasporto.sql
-- La tabella bronze_swap_contratti_corrieri contiene le fasce contrattuali

SELECT
    t.*,
    -- Determina fascia di peso applicabile
    CASE
      WHEN t.peso_lordo_kg BETWEEN c.fascia_peso_da AND c.fascia_peso_a
           AND c.corriere_id = t.corriere_id
           AND c.tratta_id   = t.tratta_id
           AND t.data_trasporto BETWEEN c.data_validita_da AND c.data_validita_a
      THEN t.peso_lordo_kg * c.tariffa_kg
      ELSE 0
    END                                             AS costo_variabile,
    COALESCE(c.quota_fissa, 0)                      AS costo_fisso,
    COALESCE(c.supplemento_pedaggio, 0)             AS costo_pedaggio,
    (t.peso_lordo_kg * COALESCE(c.tariffa_kg, 0))
      + COALESCE(c.quota_fissa, 0)
      + COALESCE(c.supplemento_pedaggio, 0)         AS costo_totale_tratta

FROM logistico.silver_trasporti t
LEFT JOIN logistico.bronze_swap_contratti_corrieri c
    ON  c.corriere_id = t.corriere_id
    AND c.tratta_id   = t.tratta_id
    AND t.peso_lordo_kg BETWEEN c.fascia_peso_da AND c.fascia_peso_a
    AND t.data_trasporto BETWEEN c.data_validita_da AND c.data_validita_a
```

**Nota critica:** Il LEFT JOIN sulle fasce peso può restituire più righe se le fasce si sovrappongono (bug nei dati contrattuali). Aggiungere:

```sql
-- Deduplica: prende la fascia più specifica (range più stretto)
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY t.trasporto_id
    ORDER BY (c.fascia_peso_a - c.fascia_peso_da) ASC
) = 1
```

---

## 6. Gestione SWAP

### Definizione di SWAP

Un ordine SWAP è un ordine sostituto: quando un articolo ordinato non è disponibile, il sistema genera un ordine di sostituzione con un articolo alternativo. L'ordine originale viene marcato come "swappato".

### Logica Oracle

```sql
-- Dalla tabella SWAP (importata via IMPORT_TRASPO92_SNAP):
-- SWAP.ORD_ORIGINALE_ID → ordine originale
-- SWAP.ORD_SOSTITUTO_ID → ordine sostituto
-- SWAP.ART_ORIGINALE_COD → articolo originale
-- SWAP.ART_SOSTITUTO_COD → articolo sostituto

-- Nel caricamento F_ORD_FORN_RIGHE:
UPDATE T_ORDINI
   SET FLAG_SWAPPED      = 'S',
       ORD_SOSTITUTO_ID  = s.ORD_SOSTITUTO_ID,
       ART_SOSTITUTO_COD = s.ART_SOSTITUTO_COD
  FROM T_ORDINI t
  JOIN SWAP s ON s.ORD_ORIGINALE_ID = t.ORD_ID
              AND s.ART_ORIGINALE_COD = t.ART_COD;
```

### Implementazione PySpark

```python
# silver/enrich_ordini_swap.py

df_ordini = spark.table("logistico.silver_ordini")
df_swap   = spark.table("logistico.bronze_swap_ordini")

df_enriched = (df_ordini.alias("o")
    .join(df_swap.alias("s"),
          on=[(F.col("o.ordine_id")   == F.col("s.ord_originale_id")),
              (F.col("o.articolo_cod") == F.col("s.art_originale_cod"))],
          how="left")
    .withColumn("flag_swapped",
                F.when(F.col("s.ord_sostituto_id").isNotNull(), F.lit("S"))
                 .otherwise(F.lit("N")))
    .withColumn("ord_sostituto_id",  F.col("s.ord_sostituto_id"))
    .withColumn("art_sostituto_cod", F.col("s.art_sostituto_cod"))
    .drop("s.*"))
```

### Regole di business SWAP

1. **Fill Rate con SWAP:** L'ordine swappato NON contribuisce al fill rate dell'articolo originale. Contribuisce al fill rate dell'articolo sostituto.
2. **Report analisi SWAP:** Vista dedicata per analizzare frequenza e pattern degli swap per articolo/fornitore:

```sql
CREATE OR REPLACE VIEW logistico.gold_kpi_swap AS
SELECT
    data_ordine_id,
    fornitore_id,
    art_originale_id,
    art_sostituto_id,
    COUNT(*)                           AS n_swap,
    SUM(qta_ordinata)                  AS qta_swappata,
    -- Swap rate: % ordini swappati sul totale per articolo
    ROUND(COUNT(*) * 100.0 /
          SUM(COUNT(*)) OVER (PARTITION BY art_originale_id, data_ordine_id),
          2)                           AS swap_rate_pct
FROM logistico.gold_f_ord_forn_righe
WHERE flag_swapped = 'S'
GROUP BY data_ordine_id, fornitore_id, art_originale_id, art_sostituto_id
;
```

3. **Tracciabilità:** Il link tra ordine originale e sostituto è mantenuto in `gold_f_ord_forn_righe` tramite le colonne `ord_sostituto_id` e `art_sostituto_cod`. È possibile risalire alla catena completa con una self-join.

---

## 7. Modello dimensionale gold_f_trasp

### gold_f_trasp_tratta (grain: 1 riga = 1 tratta trasporto)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `trasporto_id` | BIGINT | Chiave naturale trasporto |
| `tratta_id` | BIGINT | Identificatore tratta/percorso |
| `corriere_id` | BIGINT | FK → gold_dim_corriere |
| `sito_partenza_id` | BIGINT | FK → gold_dim_sito |
| `pdv_destinazione_id` | BIGINT | FK → gold_dim_pdv |
| `data_trasporto_id` | INTEGER | FK → gold_dim_calendario (YYYYMMDD) |
| `peso_lordo_kg` | DECIMAL(10,3) | Peso lordo carico |
| `peso_netto_kg` | DECIMAL(10,3) | Peso netto merce |
| `n_colli` | INTEGER | Numero colli |
| `km_tratta` | DECIMAL(8,2) | Chilometri percorsi |
| `costo_variabile` | DECIMAL(12,2) | Costo in base a fascia peso |
| `costo_fisso` | DECIMAL(12,2) | Quota fissa per viaggio |
| `costo_pedaggio` | DECIMAL(10,2) | Pedaggi autostradali |
| `costo_totale_tratta` | DECIMAL(12,2) | Costo totale tratta |
| `flag_swapped` | CHAR(1) | 'S' se ordine swappato |
| `ord_sostituto_id` | BIGINT | Link a ordine sostituto (se swap) |

---

## 8. Rischi di migrazione

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | Flag `ESTRAI_SP_ESTRATTO_DWH`: write-back su Oracle AtTraspo | Alta | Alto | Stesso approccio carichi: tabella shadow `bronze_ingest_control`; coordinarsi con team AtTraspo |
| 2 | SWAP: dati da AtTraspo92 (sistema legacy) — struttura non documentata | Alta | Alto | Mappatura completa da `TRASPO92_SNAP_OBJ_LIST`; sessione di discovery con DBA AtTraspo |
| 3 | Fasce peso: contratti variano per corriere×tratta×periodo — dati sparsi | Media | Alto | Caricare `CONTRATTI_CORRIERI` come SCD Type 2 in silver; validazione con ufficio acquisti |
| 4 | Fill Rate: definizione "consegnato" vs "spedito" può differire tra sistemi | Media | Alto | Allineare definizione con BA prima del go-live; documentare in glossario metriche |
| 5 | `SP_REPLICA_TRASP_REC_STORICO`: backfill storico per range date | Bassa | Medio | Implementare come job parametrizzato con `run_date_from` / `run_date_to` in Databricks |
