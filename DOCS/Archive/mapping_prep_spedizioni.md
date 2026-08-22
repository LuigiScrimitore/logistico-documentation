# Mapping PL/SQL → Spark SQL — Area Preparazione Spedizioni

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica del flusso Oracle AS-IS](#1-panoramica-del-flusso-oracle-as-is)
2. [Tabella di mapping procedure](#2-tabella-di-mapping-procedure)
3. [Dettaglio procedure e trasformazioni](#3-dettaglio-procedure-e-trasformazioni)
4. [SEZIONE SPECIALE: Regola 30 minuti attrezzaggio](#4-sezione-speciale-regola-30-minuti-attrezzaggio)
5. [Modello dimensionale gold_f_prep_sped](#5-modello-dimensionale-gold_f_prep_sped)
6. [Rischi di migrazione](#6-rischi-di-migrazione)

---

## 1. Panoramica del flusso Oracle AS-IS

```
Logistix (sorgente operativa)
   ↓  DB Link
CDT_ESTR.SP_REPLICA_PREP_SPED  →  RIEPILOGHI, TESTATE_BOLLE, (RIGHE_BOLLE via STORICO)
   ↓
CDT_ESTR (staging area)
   ↓  (fase check/arricchimento anagrafiche)
CDT_SA.SP_AGG_ANAG_PREP_SPED3A / 4A  →  S_OPER_SPED, S_OPER_PREP, S_AUTOM_SPED, ecc.
CDT_SA.SP_CHECK_PREP_SPED_NEW         →  check_f_prep_sped_new (quadratura)
   ↓
CDT_SA.SP_LOAD_F_PREP_SPED    →  T_PREP_SPED_TMP_P6 (STEP0→STEP1→...→STEP6)
CDT_SA.SP_LOAD_F_PREP_PROD_OPER_NETTA → F_PREP_PROD_OPER_NETTA (produttività operatori)
   ↓
CDT_DW.F_PREP_SPED            →  Fact table esposta a MicroStrategy
```

Il flusso prep spedizioni è il più complesso del sistema: comprende 6 step di caricamento, la gestione dell'attrezzaggio operatori, e la quadratura con i valori Logistix (procedura `SP_CHECK_PREP_SPED_NEW`).

**Flusso Databricks target:**

```
Oracle Logistix (JDBC incremental su TESTATE_BOLLE, RIEPILOGHI)
   ↓
bronze_riepiloghi / bronze_testate_bolle
   ↓
silver_anag_prep_sped         (anagrafiche operatori/autisti/automezzi — Late-Arriving)
silver_prep_sped_staging      (join + normalizzazione)
silver_prep_sped_check        (quadratura con sorgente)
   ↓
gold_f_prep_sped              (partizione per mese_bolla_sped)
gold_f_prep_prod_oper         (produttività operatori per turno)
```

---

## 2. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `SP_REPLICA_PREP_SPED` | CDT_ESTR | `RIEPILOGHI@<link>`, `STORICO_RIEPILOGHI@<link>`, `TESTATE_BOLLE@<link>` | `bronze_riepiloghi`, `bronze_storico_riepiloghi`, `bronze_testate_bolle` | Bronze | Incrementale via `RPLPR_DATA_ESTRAZIONE_DWH`, `TEBO_DATA_ESTRAZIONE_DWH`; multi-sito |
| `SP_AGG_ANAG_PREP_SPED3A` | CDT_SA | `E_PREP_SPED` (err 270607/270608/270610/270611) | `silver_anag_prep_sped` (S_OPER_PREP, S_OPER_SPED, S_AUTISTA_SPED, S_AUTOM_SPED) | Silver | Recupero anagrafiche mancanti da tabella errori; INSERT con "Non definito" come descrizione |
| `SP_AGG_ANAG_PREP_SPED4A` | CDT_SA | `E_PREP_SPED` (err 270612/270613/270614) | `silver_anag_prep_sped` (S_AUTOM_SPED, S_VETTORE_SPED) | Silver | Aggiunta automezzi e vettori mancanti |
| `SP_CHECK_PREP_SPED_NEW` | CDT_SA | `CDT_DW.F_PREP_SPED` vs `LOGISTIX.RIEPILOGHI` | `silver_check_f_prep_sped` | Silver | Quadratura colli, valore cessione, costo per sito×data; alert via email se delta > soglia |
| `SP_LOAD_F_PREP_SPED` STEP0-6 | CDT_SA | `T_PREP_SPED` → `S_PREP_SPED` → staging | `gold_f_prep_sped` | Gold | 6 step: recovery errori, staging, lookup dim, calcolo campi, insert partizione |
| `SP_LOAD_F_PREP_PROD_OPER_NETTA` | CDT_SA/DW | `F_PREP_SPED_WEEK` + logica attrezzaggio | `gold_f_prep_prod_oper_netta` | Gold | Calcolo produttività netta operatori con regola 30 min attrezzaggio |

---

## 3. Dettaglio procedure e trasformazioni

### 3.1 SP_AGG_ANAG_PREP_SPED3A/4A → silver_anag_prep_sped

**Logica Oracle:**

Le procedure 3A e 4A intervengono dopo lo STEP0 di `SP_LOAD_F_PREP_SPED` quando vengono trovate FK mancanti nelle anagrafiche operatori, autisti, automezzi, vettori. Inseriscono il codice mancante con descrizione "Non definito" per non bloccare il caricamento.

```sql
-- SP_AGG_ANAG_PREP_SPED3A: inserisce operatori sped mancanti
INSERT INTO s_oper_sped (oper_sped_id, oper_sped_cod, oper_sped_mag_sito_id, ...)
  SELECT seq_s_oper_sped.NEXTVAL, oper_sped_cod, mag_sito_id, ...,
         'Non definito' oper_sped_des
    FROM (SELECT DISTINCT ingrp1.mag_sito_cod, mag_sito_id, ingrp1.oper_sped_cod, ...
            FROM e_prep_sped ingrp1, s_mag_sito magsito
           WHERE err_id = 270608 AND ingrp1.mag_sito_cod = magsito.mag_sito_cod(+));
-- Analoga per OPER_PREP (err 270607), AUTISTA_SPED (270610/270609), AUTOM_SPED (270611)
```

**Equivalente PySpark:**

```python
# silver/agg_anag_prep_sped.py
# Viene eseguita DOPO lo STEP0 di load_f_prep_sped, se ci sono FK mancanti

def resolve_missing_anagrafica(spark, error_codes: list, target_table: str, 
                               cod_col: str, id_col: str, des_col: str):
    """Inserisce anagrafiche mancanti con descrizione 'Non definito'."""
    missing_df = (spark.table("logistico.silver_prep_sped_quarantine")
                  .filter(F.col("error_code").isin(error_codes))
                  .select(F.col(cod_col), F.col("sito_cod"))
                  .distinct()
                  .join(spark.table("logistico.gold_dim_sito"),
                        on="sito_cod", how="left")
                  .withColumn(des_col, F.lit("Non definito"))
                  .withColumn("_auto_inserted", F.lit(True))
                  .withColumn("_insert_ts", F.current_timestamp()))
    
    (missing_df.write.format("delta")
     .mode("append")
     .saveAsTable(target_table))

# Eseguire nell'ordine: OPER_PREP (270607) → OPER_SPED (270608) → 
#                       AUTISTA_SPED (270609/270610) → AUTOM_SPED (270611/270612)
#                       → VETTORE_SPED (270613/270614)
```

### 3.2 SP_LOAD_F_PREP_SPED → gold_f_prep_sped

Il flusso STEP0-6 in Oracle gestisce:
- **STEP0:** Recovery errori ciclo precedente
- **STEP1:** Caricamento in `T_PREP_SPED_TMP` con lookup FK
- **STEP2-4:** Calcolo campi derivati (tempi, valori, flag)
- **STEP5-6:** Caricamento in `T_PREP_SPED_TMP_P6` (staging finale) + insert in `F_PREP_SPED`

Campi chiave calcolati:

```sql
-- Calcolati in STEP2-4:
SEC_PREP_PREL    -- secondi totali di prelievo per riga bolla
VAL_PREP_CES     -- valore a prezzo di cessione (QTA_PREP × PREZZO_CESSIONE)
VAL_PREP_VEN     -- valore a prezzo di vendita
COSTO            -- costo unitario di picking (da CONTRATTI o tabella parametri)
```

**Equivalente Spark SQL (gold_f_prep_sped — merge incrementale):**

```sql
-- gold/load_f_prep_sped.sql
MERGE INTO logistico.gold_f_prep_sped AS target
USING (
  SELECT
    s.bolla_id,
    s.art_id,
    s.oper_prep_id,
    s.mag_sito_id,
    s.pdv_id,
    s.giorno_bolla_sped_id,
    s.giorno_stat_prep_id,
    -- Misure operative
    s.qta_daprep,
    s.qta_prep,
    s.num_imb_prep,
    s.num_imb_nuco_prep,
    s.pes_prep,
    -- Misure finanziarie
    s.val_prep_ces,
    s.val_prep_ven,
    s.costo,
    -- Tempi
    s.sec_prep_prel,
    s.data_prel_iniz,
    s.data_prel_fine,
    s.ora_prel_iniz,
    s.ora_prel_fine,
    -- Attributi classificazione
    s.tipo_prep_cod,
    s.tipo_prel_cod,
    s.mappa_zona_cod,
    s.area_mercl_logis_cod,
    -- Partizione
    DATE_FORMAT(CAST(s.giorno_bolla_sped_id AS STRING), 'yyyyMM') AS mese_bolla_sped_id
  FROM logistico.silver_prep_sped_staging s
  WHERE s.silver_load_ts > (SELECT MAX(gold_load_ts) FROM logistico.gold_f_prep_sped_audit)
    AND s.oper_prep_id IS NOT NULL
    AND s.art_id       IS NOT NULL
    AND s.pdv_id       IS NOT NULL
) AS source
ON target.bolla_id = source.bolla_id
   AND target.art_id = source.art_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
;
```

---

## 4. SEZIONE SPECIALE: Regola 30 minuti attrezzaggio

### 4.1 Business rule completa come da sistema Oracle

La regola dell'attrezzaggio è implementata in `CDT_DW` nel package `LOAD_F_PREP_PROD_NETTA10.SP_MAIN` (richiamato da `SP_LOAD_F_PREP_PROD_OPER_NETTA`).

**Logica Oracle estratta dal codice CDT_DW (procedure PROVA_CONT2/LOAD_F_PREP_PROD_OPER):**

```
Per ogni combinazione (sito, operatore, giorno, area_mercl, tipo_prel):
  - Ordina le missioni per DATA_PREL_INIZ ASC
  - Per ogni missione, calcola la pausa rispetto alla missione SUCCESSIVA:
    n_pause = ABS((DATA_PREL_FINE_corrente - DATA_PREL_INIZ_successiva) * 1440)
              SE la missione successiva è nello STESSO GIORNO SOLARE
              ALTRIMENTI n_pause = 0

  - CLASSIFICAZIONE della pausa:
    IF n_pause > 30 minuti:
        → hh_oper_non_prod (tempo non produttivo / pausa lunga)
        → incrementa TURNO (cambio turno: la sequenza delle missioni ricomincia)
    IF n_pause <= 30 minuti:
        → oper_attrezzaggio (attrezzaggio: tempo accettabile tra una missione e l'altra)

  - oper_missioni = (DATA_PREL_FINE - DATA_PREL_INIZ) * 1440  (durata in minuti)
```

**Codice Oracle originale (semplificato per chiarezza):**

```sql
-- Da CDT_DW procedura LOAD_F_PREP_PROD_OPER / PROVA_CONT2:
SELECT
  ...
  CASE
    WHEN LAG(n_pause, 0) OVER (PARTITION BY oper_prep_cod ORDER BY data_prel_iniz ASC NULLS LAST) > 30
      THEN fn_return_seq(1, 'SEQ_F_PREP_PROD_OPER_OP')   -- cambio turno
    ELSE   fn_return_seq(0, 'SEQ_F_PREP_PROD_OPER_OP')   -- stesso turno
  END turno,
  CASE WHEN n_pause > 30 THEN ROUND(n_pause, 1) ELSE 0 END hh_oper_non_prod,
  CASE WHEN n_pause < 30 THEN ROUND(n_pause, 1) ELSE 0 END oper_attrezzaggio,
  (data_prel_fine - data_prel_iniz) * 1440               oper_missioni

FROM (
  SELECT ...,
    CASE
      WHEN TO_CHAR(data_prel_fine, 'YYYYMMDD') =
           LEAD(TO_CHAR(data_prel_iniz,'YYYYMMDD'), 1)
             OVER (PARTITION BY oper_prep_cod ORDER BY data_prel_iniz ASC NULLS LAST)
        THEN NVL(ABS((data_prel_fine
               - LEAD(data_prel_iniz, 1) OVER (...)) * 1440), 0)
      ELSE 0
    END n_pause
  FROM f_prep_sped_week
  WHERE tipo_prep_cod IN ('S')
  ORDER BY data_prel_iniz
)
```

**Significato delle variabili:**

| Variabile Oracle | Tipo | Significato |
|---|---|---|
| `n_pause` | FLOAT (minuti) | Intervallo tra fine missione corrente e inizio missione successiva |
| `oper_attrezzaggio` | FLOAT (minuti) | Tempo tra missioni <= 30 min: considerato attrezzaggio (produttivo) |
| `hh_oper_non_prod` | FLOAT (minuti) | Tempo tra missioni > 30 min: pausa non produttiva |
| `oper_missioni` | FLOAT (minuti) | Durata effettiva della missione (prelievo) |
| `turno` | INTEGER | Identificatore turno: cambia ogni volta che n_pause > 30 min |

---

### 4.2 Implementazione con Window Function in PySpark

```python
# Notebook: gold/load_f_prep_prod_oper_netta.py

from pyspark.sql import functions as F
from pyspark.sql import Window

# --- Step 1: Carica le missioni ordinate per operatore×giorno ---
missioni_df = spark.sql("""
    SELECT
        giorno_stat_prep_id,
        mag_sito_cod,
        mag_sito_id,
        oper_prep_cod,
        oper_prep_id,
        tipo_prep_cod,
        tipo_prep_id,
        tipo_prel_cod,
        tipo_prel_id,
        area_mercl_logis_cod,
        area_mercl_logis_id,
        mappa_zona_cod,
        mappa_zona_id,
        pdv_id,
        pdv_cod,
        data_prel_iniz,
        data_prel_fine,
        num_riep,
        num_etich,
        num_imb_nuco_prep,
        num_imb_prep
    FROM logistico.gold_f_prep_sped
    WHERE tipo_prep_cod IN ('S')
      AND giorno_stat_prep_id = CAST(REPLACE('${run_date}', '-', '') AS INT)
""")

# Partition window per calcolo pausa con LEAD
w_oper = (Window
          .partitionBy("oper_prep_cod", "giorno_stat_prep_id",
                       "mag_sito_cod", "area_mercl_logis_cod", "tipo_prel_cod")
          .orderBy("data_prel_iniz"))

# --- Step 2: Calcola n_pause (minuti tra fine missione e inizio della successiva) ---
# La condizione "stesso giorno solare" replica il CASE WHEN TO_CHAR(...) Oracle
missioni_df = (missioni_df
    .withColumn("data_prel_fine_str",
                F.date_format("data_prel_fine", "yyyyMMdd"))
    .withColumn("next_data_prel_iniz",
                F.lead("data_prel_iniz", 1).over(w_oper))
    .withColumn("next_data_str",
                F.date_format(F.lead("data_prel_iniz", 1).over(w_oper), "yyyyMMdd"))
    .withColumn("n_pause",
                F.when(
                    # Solo se la missione successiva è nello stesso giorno solare
                    F.col("data_prel_fine_str") == F.col("next_data_str"),
                    F.abs(
                        (F.unix_timestamp("data_prel_fine")
                         - F.unix_timestamp("next_data_prel_iniz")) / 60.0
                    )
                ).otherwise(F.lit(0.0)))
)

# --- Step 3: Classifica pausa e identifica cambio turno ---
missioni_df = (missioni_df
    .withColumn("is_cambio_turno",
                F.when(F.col("n_pause") > 30, F.lit(1)).otherwise(F.lit(0)))
    .withColumn("oper_attrezzaggio",
                F.when(F.col("n_pause") < 30, F.round("n_pause", 1))
                 .otherwise(F.lit(0.0)))
    .withColumn("hh_oper_non_prod",
                F.when(F.col("n_pause") > 30, F.round("n_pause", 1))
                 .otherwise(F.lit(0.0)))
    .withColumn("oper_missioni",
                (F.unix_timestamp("data_prel_fine")
                 - F.unix_timestamp("data_prel_iniz")) / 60.0)
)

# --- Step 4: Calcola ID turno cumulativo ---
# Equivalente di fn_return_seq in Oracle: somma cumulativa dei cambio_turno
w_turno = (Window
           .partitionBy("oper_prep_cod", "giorno_stat_prep_id",
                        "mag_sito_cod", "area_mercl_logis_cod", "tipo_prel_cod")
           .orderBy("data_prel_iniz")
           .rowsBetween(Window.unboundedPreceding, 0))

missioni_df = missioni_df.withColumn(
    "turno_id",
    F.sum("is_cambio_turno").over(w_turno)
)

# --- Step 5: Aggrega per turno ---
result_df = (missioni_df
    .groupBy("giorno_stat_prep_id", "mag_sito_cod", "mag_sito_id",
             "oper_prep_cod", "oper_prep_id", "turno_id",
             "tipo_prep_cod", "tipo_prep_id", "tipo_prel_cod", "tipo_prel_id",
             "area_mercl_logis_cod", "area_mercl_logis_id",
             "mappa_zona_cod", "mappa_zona_id", "pdv_id", "pdv_cod")
    .agg(
        F.min("data_prel_iniz").alias("turno_inizio"),
        F.max("data_prel_fine").alias("turno_fine"),
        F.sum("oper_missioni").alias("min_missioni"),
        F.sum("oper_attrezzaggio").alias("min_attrezzaggio"),
        F.sum("hh_oper_non_prod").alias("min_non_prod"),
        F.count("*").alias("n_missioni"),
        F.sum("num_imb_nuco_prep").alias("num_imb_nuco_prep"),
        F.sum("num_imb_prep").alias("num_imb_prep")
    )
    .withColumn("run_date", F.lit("${run_date}"))
)

# Scrivi in gold
(result_df.write.format("delta")
 .mode("append")
 .partitionBy("giorno_stat_prep_id")
 .saveAsTable("logistico.gold_f_prep_prod_oper_netta"))
```

---

### 4.3 Casi edge e gestione

#### Caso 1: Sessioni < 30 minuti (missione unica o molto ravvicinata)

**Scenario:** Un operatore completa una sola missione nel turno, o due missioni con pausa < 30 min.

**Comportamento Oracle:** `n_pause = 0` (non c'è missione successiva) → `oper_attrezzaggio = 0`, `hh_oper_non_prod = 0`.

**Comportamento PySpark:** `LEAD` restituisce NULL quando non c'è missione successiva; la condizione `F.when(...).otherwise(0.0)` gestisce correttamente il caso con `n_pause = 0`.

**Test atteso:**

| Operatore | Missione | data_prel_iniz | data_prel_fine | n_pause | oper_attrezzaggio | hh_oper_non_prod |
|---|---|---|---|---|---|---|
| OP001 | M1 | 08:00 | 08:25 | 0 (no succ.) | 0 | 0 |

#### Caso 2: Turni a cavallo di mezzanotte

**Scenario:** Un operatore inizia una missione alle 23:45 e la termina alle 00:15 del giorno successivo.

**Comportamento Oracle:** La condizione `TO_CHAR(data_prel_fine,'YYYYMMDD') = LEAD(TO_CHAR(data_prel_iniz,...))` impone che la pausa sia calcolata solo se le due missioni sono nello **stesso giorno solare**. Se la missione successiva è in un giorno diverso, `n_pause = 0`.

**Comportamento PySpark:** Identico. La colonna `data_prel_fine_str` vs `next_data_str` implementa lo stesso controllo.

**Implicazione:** Una missione che inizia il 23:50 e finisce il 00:05 viene attribuita al giorno della DATA_PREL_INIZ. Il cambio di mezzanotte non crea un cambio turno artificiale.

**Test atteso:**

| Operatore | Missione | data_prel_iniz | data_prel_fine | n_pause | Cambio turno |
|---|---|---|---|---|---|
| OP002 | M1 | 23:40 | 23:58 | 0 (succ. giorno dopo) | NO |
| OP002 | M2 | 00:10 | 00:35 | N/A (inizio nuovo giorno) | N/A |

#### Caso 3: Più sessioni per operatore nello stesso giorno (turno diviso)

**Scenario:** Un operatore lavora 08:00-13:00, pausa pranzo 60 min, poi 14:00-18:00.

**Comportamento Oracle/PySpark:** La pausa di 60 min > 30 min → `hh_oper_non_prod = 60`, `is_cambio_turno = 1` → il secondo blocco avrà `turno_id = 1` (diverso da `turno_id = 0` del mattino).

**Test atteso:**

| Operatore | Missione | data_prel_fine | next_data_prel_iniz | n_pause | hh_oper_non_prod | oper_attrezzaggio | turno_id |
|---|---|---|---|---|---|---|---|
| OP003 | M1 (08:00-09:00) | 09:00 | 09:15 | 15 | 0 | 15 | 0 |
| OP003 | M2 (09:15-10:30) | 10:30 | 11:00 | 30 | 0 | 30* | 0 |
| OP003 | M3 (11:00-13:00) | 13:00 | 14:00 | 60 | 60 | 0 | 0 |
| OP003 | M4 (14:00-15:30) | 15:30 | — | 0 | 0 | 0 | 1 |

*Nota: 30 min esatti. La condizione Oracle è `n_pause < 30` (stretto) per attrezzaggio e `> 30` (stretto) per non_prod. Con esattamente 30 min: entrambe le condizioni sono false → attrezzaggio = 0, non_prod = 0. Questo è un caso limite da verificare con il business.

---

### 4.4 Tabella riepilogativa casi test con valori attesi

```
Scenario                    | n_pause | attrezzaggio | non_prod | cambio_turno
----------------------------|---------|--------------|----------|-------------
Missione unica              |    0    |      0       |    0     |     NO
Pausa 10 min (< 30)         |   10    |     10       |    0     |     NO
Pausa 30 min (= 30, border) |   30    |      0*      |    0*    |     NO
Pausa 45 min (> 30)         |   45    |      0       |   45     |     SI
Pausa 120 min (> 30)        |  120    |      0       |  120     |     SI
Mezzanotte (stesso giorno)  |    0    |      0       |    0     |     NO
Missione prima e dopo mnott |    0    |      0       |    0     |     NO (*)
```

(*) La missione a cavallo di mezzanotte: la pausa verso la missione del giorno dopo non viene calcolata (diverso giorno solare). Verificare con business se il comportamento è corretto o se si vuole il turno notturno.

---

## 5. Modello dimensionale gold_f_prep_sped

**Grain:** 1 riga = (BOLLA_ID, ART_ID) per operatore nel turno

| Colonna | Tipo | Descrizione |
|---|---|---|
| `bolla_id` | BIGINT | Chiave naturale bolla spedizione |
| `art_id` | BIGINT | FK → gold_dim_articolo |
| `oper_prep_id` | BIGINT | FK → silver_dim_oper_prep |
| `mag_sito_id` | BIGINT | FK → gold_dim_sito |
| `pdv_id` | BIGINT | FK → gold_dim_pdv |
| `giorno_bolla_sped_id` | INTEGER | FK → gold_dim_calendario (YYYYMMDD) |
| `qta_daprep` | DECIMAL(12,3) | Quantità da preparare |
| `qta_prep` | DECIMAL(12,3) | Quantità effettivamente preparata |
| `num_imb_prep` | INTEGER | Numero imballi preparati |
| `num_imb_nuco_prep` | INTEGER | Numero colli NUCO (unità consumatore) |
| `pes_prep` | DECIMAL(12,3) | Peso preparato in kg |
| `val_prep_ces` | DECIMAL(15,2) | Valore a prezzo di cessione |
| `val_prep_ven` | DECIMAL(15,2) | Valore a prezzo di vendita |
| `costo` | DECIMAL(15,2) | Costo di picking |
| `sec_prep_prel` | INTEGER | Secondi impiegati per il prelievo |
| `data_prel_iniz` | TIMESTAMP | Inizio prelievo |
| `data_prel_fine` | TIMESTAMP | Fine prelievo |
| `tipo_prep_cod` | VARCHAR(2) | Tipo preparazione (S=Standard, ecc.) |
| `mese_bolla_sped_id` | INTEGER | Partizione: YYYYMM |

---

## 6. Rischi di migrazione

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | `fn_return_seq` Oracle: sequenza non è thread-safe in Spark | Alta | Alto | Sostituita con `SUM(is_cambio_turno) OVER (... ROWS UNBOUNDED PRECEDING)` |
| 2 | Regola 30 min: boundary esatto (= 30) non gestito esplicitamente in Oracle | Media | Basso | Definire con business: aggiungere condizione `>= 30` per non_prod o mantenere gap |
| 3 | `TIPO_PREP_COD = 'S'`: solo tipo Standard incluso nel calcolo produttività | Alta | Medio | Confermare con business se altri tipi (es. 'P' = Promo, 'R' = Reso) devono essere inclusi |
| 4 | Volume F_PREP_SPED: tabella più grande del sistema (~500M righe storiche) | Alta | Alto | Z-ORDER su (giorno_bolla_sped_id, mag_sito_cod); partizione mensile obbligatoria |
| 5 | Quadratura con Logistix: `SP_CHECK_PREP_SPED_NEW` invia email manuale | Alta | Medio | Sostituire con alert Databricks + dashboard quadratura in gold_f_check_prep_sped |
| 6 | Turni a cavallo di mezzanotte: comportamento Oracle da validare con operatori | Media | Medio | Eseguire test con dati reali nei giorni T-7 prima del go-live |
