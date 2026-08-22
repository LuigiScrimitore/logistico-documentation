# Mapping PL/SQL → Spark SQL — Area Movimentazione Carrellisti

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica del flusso Oracle AS-IS](#1-panoramica-del-flusso-oracle-as-is)
2. [Tabella di mapping procedure](#2-tabella-di-mapping-procedure)
3. [Struttura tabelle sorgente](#3-struttura-tabelle-sorgente)
4. [Logica calcolo ORE_PRODUTTIVE](#4-logica-calcolo-ore_produttive)
5. [KPI Missioni/ora](#5-kpi-missioniora)
6. [TIPOLOGIA_PRINCIPALE: missione più frequente](#6-tipologia_principale-missione-più-frequente)
7. [Modello dimensionale gold_f_mov_carr](#7-modello-dimensionale-gold_f_mov_carr)
8. [Rischi di migrazione](#8-rischi-di-migrazione)

---

## 1. Panoramica del flusso Oracle AS-IS

```
Logistix (sorgente operativa — terminali carrellisti)
   ↓  DB Link
CDT_ESTR.SP_REPLICA_CARRELLISTI  →  DETTAGLIO_CARR, CARTELLINO, ABB_TOLTI
   ↓
CDT_ESTR.SP_ESTRAI_CARRELLISTI   →  ESTRAI_CARR.SP_MAIN
   ↓
CDT_SA.SP_LOAD_F_MOV_CARR        →  T_MOV_CARR_TMP (step partitioned by mese)
CDT_SA.SP_LOAD_F_MOV_ANN_CARR    →  F_MOV_ANN_CARR (aggregazione annuale)
CDT_SA.SP_LOAD_F_OPER_CARR_LAV   →  F_OPER_CARR_LAV (ore lavorate operatori)
   ↓
CDT_DW.F_MOV_CARR                →  Fact table movimentazione carrellisti
CDT_DW.F_OPER_CARR_LAV           →  Fact table ore lavorate
```

I carrellisti sono gli operatori di magazzino che eseguono missioni di movimentazione con carrelli elevatori. Il sistema registra ogni missione (inizio-fine, tipo, zona magazzino) e le presenze (cartellino timbrature + abbonamenti tolti per pause/riunioni).

**Flusso Databricks target:**

```
Oracle Logistix (JDBC incremental)
   ↓
bronze_dettaglio_carr / bronze_cartellino / bronze_abb_tolti
   ↓
silver_movimenti_carr   (missioni normalizzate con dimensioni)
silver_presenze_carr    (ore presenti da cartellino - abbonamenti tolti)
   ↓
gold_f_mov_carr              (fact missioni partizione mensile)
gold_f_oper_carr_lav         (fact ore lavorate giornaliera)
gold_kpi_carrellisti         (KPI aggregati: missioni/ora, tipologia principale)
```

---

## 2. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `SP_REPLICA_CARRELLISTI` | CDT_ESTR | `DETTAGLIO_CARR@<link>` (watermark `DTCRL_DATA_ESTRAZIONE_DWH`), `ABB_TOLTI@<link>` (`ABT_DATA_ESTRAZIONE_DWH`), `CARTELLINO@<link>` (`CARTE_DATA_ESTRAZIONE_DWH`) | `bronze_dettaglio_carr`, `bronze_abb_tolti`, `bronze_cartellino` | Bronze | Incrementale multi-sito; stesso meccanismo watermark dei carichi |
| `SP_ESTRAI_CARRELLISTI` | CDT_ESTR | Tabelle bronze locali | `silver_movimenti_carr` | Silver | Arricchimento con dimensioni operatori e missioni |
| `SP_LOAD_F_MOV_CARR` | CDT_SA/DW | `T_MOV_CARR_TMP` staging | `gold_f_mov_carr` | Gold | Partitionamento mensile (loop su mesi); calcolo KPI missioni |
| `SP_LOAD_F_MOV_ANN_CARR` | CDT_SA/DW | `F_MOV_CARR` | `gold_f_mov_ann_carr` | Gold | Aggregazione annuale per reporting YTD |
| `SP_LOAD_F_OPER_CARR_LAV` | CDT_SA/DW | `CARTELLINO` + `ABB_TOLTI` | `gold_f_oper_carr_lav` | Gold | Calcolo ORE_PRODUTTIVE con sottrazione ABB_TOLTI |

---

## 3. Struttura tabelle sorgente

### DETTAGLIO_CARR (missioni carrellista)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `DTCRL_ID` | NUMBER | PK missione |
| `DTCRL_OPER_COD` | VARCHAR2(20) | Codice operatore carrellista |
| `DTCRL_SITO_COD` | VARCHAR2(10) | Magazzino |
| `DTCRL_DATA_MISSIONE` | NUMBER | Data missione (YYYYMMDD) |
| `DTCRL_ORA_INIZIO` | NUMBER | Ora inizio missione (HH24MI) |
| `DTCRL_ORA_FINE` | NUMBER | Ora fine missione (HH24MI) |
| `DTCRL_TIPO_MISSIONE` | VARCHAR2(20) | Tipo: PRELIEVO, RIFORNIMENTO, TRASFERIMENTO, INVENTARIO, ecc. |
| `DTCRL_ZONA_COD` | VARCHAR2(10) | Zona magazzino |
| `DTCRL_UDC_COD` | VARCHAR2(30) | Unità di carico movimentata |
| `DTCRL_NUM_MISSIONI` | NUMBER | Numero missioni nel record (spesso = 1) |
| `DTCRL_DATA_ESTRAZIONE_DWH` | NUMBER | Watermark (YYYYMMDDHH24MI) |

### CARTELLINO (presenze/timbrature)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `CARTE_ID` | NUMBER | PK timbratura |
| `CARTE_OPER_COD` | VARCHAR2(20) | Codice operatore |
| `CARTE_SITO_COD` | VARCHAR2(10) | Magazzino |
| `CARTE_DATA` | NUMBER | Data (YYYYMMDD) |
| `CARTE_ORA_ENTRATA` | NUMBER | Ora inizio turno (HH24MI) |
| `CARTE_ORA_USCITA` | NUMBER | Ora fine turno (HH24MI) |
| `CARTE_ORE_PRESENTI` | NUMBER(5,2) | Ore totali presenti (decimale) |
| `CARTE_DATA_ESTRAZIONE_DWH` | NUMBER | Watermark |

### ABB_TOLTI (abbonamenti sottratti — pause e riunioni)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `ABT_ID` | NUMBER | PK |
| `ABT_OPER_COD` | VARCHAR2(20) | Codice operatore |
| `ABT_SITO_COD` | VARCHAR2(10) | Magazzino |
| `ABT_DATA` | NUMBER | Data (YYYYMMDD) |
| `ABT_TIPO` | VARCHAR2(20) | Tipo: PAUSA, RIUNIONE, FORMAZIONE, MENSA |
| `ABT_MINUTI` | NUMBER | Minuti da sottrarre alle ore produttive |
| `ABT_DATA_ESTRAZIONE_DWH` | NUMBER | Watermark |

---

## 4. Logica calcolo ORE_PRODUTTIVE

### Definizione

```
ORE_PRODUTTIVE = ORE_PRESENTI (da CARTELLINO)
               - PAUSE (da ABB_TOLTI dove TIPO='PAUSA')
               - RIUNIONI (da ABB_TOLTI dove TIPO='RIUNIONE')
               - FORMAZIONE (da ABB_TOLTI dove TIPO='FORMAZIONE')
               - MENSA (da ABB_TOLTI dove TIPO='MENSA')
```

### Logica Oracle (pseudocodice da SP_LOAD_F_OPER_CARR_LAV):

```sql
INSERT INTO F_OPER_CARR_LAV
SELECT
    c.CARTE_OPER_COD,
    c.CARTE_SITO_COD,
    c.CARTE_DATA,
    c.CARTE_ORE_PRESENTI,
    -- Somma minuti sottratti da ABB_TOLTI
    NVL(a.minuti_pause,      0) AS min_pause,
    NVL(a.minuti_riunioni,   0) AS min_riunioni,
    NVL(a.minuti_formazione, 0) AS min_formazione,
    NVL(a.minuti_mensa,      0) AS min_mensa,
    -- ORE_PRODUTTIVE calcolate
    c.CARTE_ORE_PRESENTI
      - (NVL(a.minuti_pause, 0)
         + NVL(a.minuti_riunioni, 0)
         + NVL(a.minuti_formazione, 0)
         + NVL(a.minuti_mensa, 0)) / 60.0    AS ORE_PRODUTTIVE

FROM CARTELLINO c
LEFT JOIN (
    SELECT
        ABT_OPER_COD, ABT_SITO_COD, ABT_DATA,
        SUM(CASE WHEN ABT_TIPO = 'PAUSA'      THEN ABT_MINUTI ELSE 0 END) AS minuti_pause,
        SUM(CASE WHEN ABT_TIPO = 'RIUNIONE'   THEN ABT_MINUTI ELSE 0 END) AS minuti_riunioni,
        SUM(CASE WHEN ABT_TIPO = 'FORMAZIONE' THEN ABT_MINUTI ELSE 0 END) AS minuti_formazione,
        SUM(CASE WHEN ABT_TIPO = 'MENSA'      THEN ABT_MINUTI ELSE 0 END) AS minuti_mensa
    FROM ABB_TOLTI
    GROUP BY ABT_OPER_COD, ABT_SITO_COD, ABT_DATA
) a ON a.ABT_OPER_COD = c.CARTE_OPER_COD
    AND a.ABT_SITO_COD = c.CARTE_SITO_COD
    AND a.ABT_DATA     = c.CARTE_DATA
WHERE c.CARTE_DATA = <giorno_corrente>
;
```

### Equivalente Spark SQL (gold_f_oper_carr_lav):

```sql
-- gold/load_f_oper_carr_lav.sql
CREATE OR REPLACE TABLE logistico.gold_f_oper_carr_lav
USING DELTA
PARTITIONED BY (anno_mese)
AS
WITH abb_aggregati AS (
    SELECT
        ABT_OPER_COD                    AS oper_cod,
        ABT_SITO_COD                    AS sito_cod,
        ABT_DATA                        AS data_num,
        SUM(CASE WHEN ABT_TIPO = 'PAUSA'      THEN ABT_MINUTI ELSE 0 END) AS min_pause,
        SUM(CASE WHEN ABT_TIPO = 'RIUNIONE'   THEN ABT_MINUTI ELSE 0 END) AS min_riunioni,
        SUM(CASE WHEN ABT_TIPO = 'FORMAZIONE' THEN ABT_MINUTI ELSE 0 END) AS min_formazione,
        SUM(CASE WHEN ABT_TIPO = 'MENSA'      THEN ABT_MINUTI ELSE 0 END) AS min_mensa,
        SUM(ABT_MINUTI)                                                     AS min_tolti_totali
    FROM logistico.bronze_abb_tolti
    WHERE ABT_DATA = CAST(REPLACE('${run_date}', '-', '') AS INT)
    GROUP BY ABT_OPER_COD, ABT_SITO_COD, ABT_DATA
)
SELECT
    c.CARTE_OPER_COD                                    AS oper_cod,
    c.CARTE_SITO_COD                                    AS sito_cod,
    TO_DATE(CAST(c.CARTE_DATA AS STRING), 'yyyyMMdd')   AS data_presenza,
    -- Ore presenti da cartellino
    c.CARTE_ORE_PRESENTI                                AS ore_presenti,
    -- Abbonamenti per tipologia (in ore)
    COALESCE(a.min_pause,      0) / 60.0                AS ore_pausa,
    COALESCE(a.min_riunioni,   0) / 60.0                AS ore_riunioni,
    COALESCE(a.min_formazione, 0) / 60.0                AS ore_formazione,
    COALESCE(a.min_mensa,      0) / 60.0                AS ore_mensa,
    COALESCE(a.min_tolti_totali, 0) / 60.0              AS ore_tolte_totali,
    -- ORE_PRODUTTIVE: ore presenti meno tutte le sottrazioni
    GREATEST(
        c.CARTE_ORE_PRESENTI - COALESCE(a.min_tolti_totali, 0) / 60.0,
        0.0   -- non può essere negativo
    )                                                   AS ore_produttive,
    -- Flag per anomalie
    CASE
      WHEN c.CARTE_ORE_PRESENTI - COALESCE(a.min_tolti_totali, 0) / 60.0 < 0
      THEN TRUE ELSE FALSE
    END                                                 AS flag_ore_negative,
    -- FK dimensioni
    COALESCE(op.operatore_id, -1)                       AS operatore_id,
    COALESCE(s.sito_id,       -1)                       AS sito_id,
    COALESCE(cal.calendario_id, -1)                     AS data_presenza_id,
    -- Partizione
    DATE_FORMAT(TO_DATE(CAST(c.CARTE_DATA AS STRING), 'yyyyMMdd'), 'yyyyMM') AS anno_mese

FROM logistico.bronze_cartellino                        c
LEFT JOIN abb_aggregati                                 a
    ON  a.oper_cod = c.CARTE_OPER_COD
    AND a.sito_cod = c.CARTE_SITO_COD
    AND a.data_num = c.CARTE_DATA
LEFT JOIN logistico.gold_dim_operatore                  op ON op.operatore_cod = c.CARTE_OPER_COD
LEFT JOIN logistico.gold_dim_sito                       s  ON s.sito_cod        = c.CARTE_SITO_COD
LEFT JOIN logistico.gold_dim_calendario                 cal
    ON cal.data_effettiva = TO_DATE(CAST(c.CARTE_DATA AS STRING), 'yyyyMMdd')

WHERE c.CARTE_DATA = CAST(REPLACE('${run_date}', '-', '') AS INT)
;
```

---

## 5. KPI Missioni/ora

### Definizione

```
MISSIONI_ORA = NUM_MISSIONI / ORE_PRODUTTIVE
```

Dove `NUM_MISSIONI` è il conteggio delle missioni eseguite dall'operatore nel giorno e `ORE_PRODUTTIVE` è calcolato come sopra.

### Implementazione Spark SQL:

```sql
-- gold/kpi_carrellisti.sql
CREATE OR REPLACE VIEW logistico.gold_kpi_carrellisti AS
SELECT
    m.data_missione,
    m.sito_id,
    m.operatore_id,
    -- Missioni per tipo
    SUM(m.num_missioni)                             AS num_missioni_totali,
    SUM(CASE WHEN m.tipo_missione_cod = 'PRELIEVO'
             THEN m.num_missioni ELSE 0 END)         AS missioni_prelievo,
    SUM(CASE WHEN m.tipo_missione_cod = 'RIFORNIMENTO'
             THEN m.num_missioni ELSE 0 END)         AS missioni_rifornimento,
    SUM(CASE WHEN m.tipo_missione_cod = 'TRASFERIMENTO'
             THEN m.num_missioni ELSE 0 END)         AS missioni_trasferimento,
    -- Ore produttive dal join con f_oper_carr_lav
    MAX(l.ore_produttive)                           AS ore_produttive,
    -- KPI: missioni/ora (protegge da divisione per zero)
    CASE
      WHEN MAX(l.ore_produttive) > 0
      THEN ROUND(SUM(m.num_missioni) / MAX(l.ore_produttive), 2)
      ELSE NULL
    END                                             AS missioni_per_ora,
    -- Classificazione performance operatore
    CASE
      WHEN ROUND(SUM(m.num_missioni) / NULLIF(MAX(l.ore_produttive), 0), 2) >= 20 THEN 'ALTA'
      WHEN ROUND(SUM(m.num_missioni) / NULLIF(MAX(l.ore_produttive), 0), 2) >= 12 THEN 'MEDIA'
      WHEN ROUND(SUM(m.num_missioni) / NULLIF(MAX(l.ore_produttive), 0), 2) >= 0  THEN 'BASSA'
      ELSE NULL
    END                                             AS classe_performance

FROM logistico.gold_f_mov_carr                      m
LEFT JOIN logistico.gold_f_oper_carr_lav            l
    ON  l.operatore_id  = m.operatore_id
    AND l.sito_id       = m.sito_id
    AND l.data_presenza = m.data_missione

GROUP BY m.data_missione, m.sito_id, m.operatore_id
;
```

---

## 6. TIPOLOGIA_PRINCIPALE: missione più frequente

### Definizione

La `TIPOLOGIA_PRINCIPALE` è la tipologia di missione più frequente per un dato operatore nel giorno. Serve per classificare gli operatori per ruolo prevalente (es. "questo operatore oggi ha fatto principalmente rifornimenti").

### Implementazione con Window Function (pattern "mode"):

```sql
-- Tecnica: ROW_NUMBER su conteggio decrescente per tipologia
CREATE OR REPLACE VIEW logistico.gold_tipologia_principale_carr AS
WITH missioni_per_tipo AS (
    SELECT
        data_missione,
        sito_id,
        operatore_id,
        tipo_missione_cod,
        SUM(num_missioni)                             AS n_missioni_tipo
    FROM logistico.gold_f_mov_carr
    GROUP BY data_missione, sito_id, operatore_id, tipo_missione_cod
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY data_missione, sito_id, operatore_id
            ORDER BY n_missioni_tipo DESC,
                     tipo_missione_cod ASC   -- tiebreak alfabetico per determinismo
        ) AS rn
    FROM missioni_per_tipo
)
SELECT
    data_missione,
    sito_id,
    operatore_id,
    tipo_missione_cod                               AS tipologia_principale,
    n_missioni_tipo                                 AS n_missioni_tipologia_principale,
    SUM(n_missioni_tipo) OVER (
        PARTITION BY data_missione, sito_id, operatore_id
    )                                               AS n_missioni_totali,
    ROUND(
        n_missioni_tipo * 100.0 /
        SUM(n_missioni_tipo) OVER (PARTITION BY data_missione, sito_id, operatore_id),
        1
    )                                               AS pct_tipologia_principale
FROM ranked
WHERE rn = 1   -- solo la tipologia più frequente
;
```

**Nota:** In caso di parità (stesso numero di missioni per due tipologie), viene scelta quella con codice alfabeticamente minore. Questo è il comportamento deterministico equivalente a come Oracle gestisce il tiebreak con la funzione aggregata `MAX()` o `MIN()` usata in questo contesto.

---

## 7. Modello dimensionale gold_f_mov_carr

**Grain:** 1 riga = 1 missione carrellista (inizio-fine) per operatore×giorno×tipo

| Colonna | Tipo | Descrizione |
|---|---|---|
| `mov_carr_id` | BIGINT | PK surrogate |
| `operatore_id` | BIGINT | FK → gold_dim_operatore |
| `sito_id` | BIGINT | FK → gold_dim_sito |
| `data_missione_id` | INTEGER | FK → gold_dim_calendario (YYYYMMDD) |
| `data_missione` | DATE | Data missione |
| `tipo_missione_cod` | VARCHAR(20) | Tipo: PRELIEVO, RIFORNIMENTO, TRASFERIMENTO, INVENTARIO |
| `zona_cod` | VARCHAR(10) | Zona magazzino |
| `udc_cod` | VARCHAR(30) | Unità di carico |
| `ora_inizio` | SMALLINT | Ora inizio HH24MI |
| `ora_fine` | SMALLINT | Ora fine HH24MI |
| `durata_minuti` | DECIMAL(6,2) | Durata missione in minuti |
| `num_missioni` | INTEGER | Numero missioni (tipicamente 1) |
| `anno_mese` | INTEGER | Partizione YYYYMM |

---

## 8. Rischi di migrazione

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | ABB_TOLTI: tipologie (`ABT_TIPO`) non standardizzate tra siti | Alta | Medio | Normalizzazione in silver: mapping tabella `silver_mapping_abb_tolti` |
| 2 | ORE_PRODUTTIVE negative: ABT_MINUTI > ORE_PRESENTI × 60 | Bassa | Alto | `GREATEST(..., 0)` + flag `flag_ore_negative`; alert se > 1% operatori nel giorno |
| 3 | Soglie KPI (20 missioni/ora): valori hardcodati, variano per sito/tipo magazzino | Media | Medio | Esternalizzare soglie in tabella `silver_config_kpi_carrellisti` |
| 4 | Tiebreak TIPOLOGIA_PRINCIPALE: comportamento deterministico diverso tra Oracle e Spark | Bassa | Basso | Documentare regola tiebreak; usare `tipo_missione_cod ASC` come tiebreak fisso |
| 5 | Carrellisti multi-sito (stesso operatore lavora su più magazzini) | Media | Medio | Grain include `sito_id`: un operatore può avere record distinti per sito nello stesso giorno |
| 6 | Ore timbratura registrate in HH24MI (intero) vs decimal in altri sistemi | Alta | Basso | Conversione: `FLOOR(ORA_INT / 100) + (ORA_INT MOD 100) / 60.0` per avere ore decimali |
