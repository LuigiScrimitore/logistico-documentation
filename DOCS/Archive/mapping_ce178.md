# Mapping PL/SQL → Spark SQL — Area Tracciabilità CE 178/2002

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Normativa CE 178/2002: contesto e requisiti](#1-normativa-ce-1782002-contesto-e-requisiti)
2. [Panoramica del flusso Oracle AS-IS](#2-panoramica-del-flusso-oracle-as-is)
3. [Tabella di mapping procedure](#3-tabella-di-mapping-procedure)
4. [Struttura TRACCIACE178: ciclo vita del lotto](#4-struttura-tracciace178-ciclo-vita-del-lotto)
5. [Dettaglio trasformazioni verso gold_f_tracciabilita_lotti](#5-dettaglio-trasformazioni-verso-gold_f_tracciabilita_lotti)
6. [Vista compliance: lotti scaduti con giacenza residua](#6-vista-compliance-lotti-scaduti-con-giacenza-residua)
7. [Processo di audit: risposta a ispezioni](#7-processo-di-audit-risposta-a-ispezioni)
8. [Rischi di migrazione](#8-rischi-di-migrazione)

---

## 1. Normativa CE 178/2002: contesto e requisiti

Il **Regolamento CE 178/2002** stabilisce i principi generali della legislazione alimentare nell'Unione Europea. Per i distributori alimentari, l'articolo 18 impone:

> *"In tutte le fasi della produzione, della trasformazione e della distribuzione è predisposta la rintracciabilità degli alimenti... Le imprese alimentari devono essere in grado di identificare chi ha fornito loro un alimento... e le imprese alle quali i propri prodotti sono stati forniti."*

**Requisiti operativi per il sistema DWH:**

| Requisito | Obbligatorio | Descrizione |
|---|---|---|
| Tracciabilità lotto a monte | SI | Per ogni lotto in magazzino: chi ha fornito, quando, con quale documento |
| Tracciabilità lotto a valle | SI | Per ogni lotto uscito: a quale PDV/cliente consegnato, quando |
| Data di scadenza | SI | Monitoraggio lotti con scadenza imminente o passata |
| Gestione ritiro/recall | SI | Capacità di identificare tutti i lotti interessati in < 4 ore |
| Conservazione dati | SI | Minimo 5 anni dalla data di produzione |
| Risposta a ispezioni | SI | Report pronti per autorità sanitarie (NAS, ASL) |

---

## 2. Panoramica del flusso Oracle AS-IS

```
Logistix (movimenti lotti in magazzino)
   ↓  DB Link
CDT_ESTR (ANNULLA_DATE / SP_ESTRAI_CARICO)
   → TRACCIACE178 viene estratta insieme ai carichi
   → Colonna watermark: CE178_DATA_ESTRAZIONE_DWH
   ↓
CDT_SA.SP_LOAD_F_TRACC     →  T_TRACC_TMP (STEP0 + STEP1)
   ↓
CDT_DW.F_TRACC             →  Fact table tracciabilità
```

La tabella `TRACCIACE178` registra ogni evento che coinvolge un lotto: ingresso in magazzino (CARICO), movimentazione interna (STOCCAGGIO, TRASFERIMENTO), e uscita (USCITA per consegna o reso).

**Flusso Databricks target:**

```
Oracle Logistix (JDBC incremental su TRACCIACE178)
   ↓
bronze_tracciace178         (append incrementale, partizione per anno_mese)
   ↓
silver_tracciabilita_lotti  (eventi con dimensioni risolte)
   ↓
gold_f_tracciabilita_lotti  (ciclo vita completo per lotto)
gold_v_compliance_ce178     (vista compliance per ispezioni)
```

---

## 3. Tabella di mapping procedure

| Procedura Oracle | Schema | Tabella sorgente | Tabella target Databricks | Layer | Trasformazioni chiave |
|---|---|---|---|---|---|
| `ANNULLA_DATE` (pkg CARICHI) | CDT_ESTR | `TRACCIACE178@<link>` | — | — | Annulla watermark per re-estrazione; in Databricks gestito con `DELETE FROM bronze WHERE run_id = X` |
| Estrazione contestuale a SP_REPLICA_CARICHI | CDT_ESTR | `TRACCIACE178@<link>` (watermark `CE178_DATA_ESTRAZIONE_DWH`) | `bronze_tracciace178` | Bronze | Incrementale; un record per ogni evento su un lotto |
| `SP_LOAD_F_TRACC` STEP0 | CDT_SA | `E_TRACC` (tabella errori) | `silver_tracciabilita_quarantine` | Silver | Recovery FK non risolte (lotto, articolo, sito) |
| `SP_LOAD_F_TRACC` STEP1 | CDT_SA | `T_TRACC_TMP` | `silver_tracciabilita_lotti` | Silver | Join con dimensioni, calcolo QTA_RESIDUA, stato lotto |
| Load DW | CDT_DW | `T_TRACC_TMP` | `gold_f_tracciabilita_lotti` | Gold | Ciclo vita completo con pivot CARICO→USCITA; DATA_SCADENZA |

---

## 4. Struttura TRACCIACE178: ciclo vita del lotto

### Schema della tabella sorgente

| Colonna Oracle | Tipo | Descrizione |
|---|---|---|
| `CE178_ID` | NUMBER | PK evento tracciabilità |
| `CE178_LOTTO_ID` | VARCHAR2(50) | Identificatore lotto (LOT_ID) |
| `CE178_ART_COD` | VARCHAR2(20) | Codice articolo |
| `CE178_TIPO_EVENTO` | VARCHAR2(10) | Tipo: CARICO, STOCCAGGIO, USCITA, RESO, SCARTO |
| `CE178_COD_SITO` | VARCHAR2(10) | Magazzino coinvolto |
| `CE178_DATA_EVENTO` | NUMBER | Data evento (YYYYMMDD numerico) |
| `CE178_ORA_EVENTO` | NUMBER | Ora evento (HH24MI numerico) |
| `CE178_QTA_EVENTO` | NUMBER | Quantità coinvolta (+ in, - out) |
| `CE178_NUM_DOC` | VARCHAR2(30) | Documento di riferimento |
| `CE178_COD_FORNITORE` | VARCHAR2(20) | Fornitore (per evento CARICO) |
| `CE178_COD_PDV` | VARCHAR2(10) | PDV destinatario (per evento USCITA) |
| `CE178_DATA_SCADENZA` | NUMBER | Data scadenza lotto (YYYYMMDD) |
| `CE178_DATA_PRODUZIONE` | NUMBER | Data produzione (YYYYMMDD) |
| `CE178_DATA_ESTRAZIONE_DWH` | NUMBER | Watermark estrazione (YYYYMMDDHH24MI) |

### Ciclo vita di un lotto (stati)

```
[CARICO] → [STOCCAGGIO]* → [USCITA]
    ↓                           ↓
[SCARTO]                    [RESO] → [STOCCAGGIO]* → [USCITA]
```

| Tipo Evento | QTA_EVENTO | Significato | Genera |
|---|---|---|---|
| CARICO | Positiva | Lotto entra in magazzino da fornitore | +QTA_RESIDUA |
| STOCCAGGIO | Zero o null | Movimentazione interna (cambio ubicazione) | neutro |
| TRASFERIMENTO | Positiva→Negativa | Uscita da sito A + Entrata in sito B | bilancio 0 |
| USCITA | Negativa | Lotto esce per consegna a PDV | -QTA_RESIDUA |
| RESO | Positiva | Reso da PDV: rientra in magazzino | +QTA_RESIDUA |
| SCARTO | Negativa | Lotto scartato (non commerciabile) | -QTA_RESIDUA |

---

## 5. Dettaglio trasformazioni verso gold_f_tracciabilita_lotti

### 5.1 Silver: normalizzazione eventi

```sql
-- silver/transform_tracciabilita.sql
CREATE OR REPLACE TABLE logistico.silver_tracciabilita_lotti
USING DELTA
PARTITIONED BY (anno_mese_evento)
AS
SELECT
    t.CE178_ID                                      AS traccia_id,
    t.CE178_LOTTO_ID                                AS lotto_id,
    t.CE178_TIPO_EVENTO                             AS tipo_evento,
    t.CE178_NUM_DOC                                 AS num_doc,
    -- Conversione date numeriche Oracle → DATE
    TO_DATE(CAST(t.CE178_DATA_EVENTO AS STRING), 'yyyyMMdd')
                                                    AS data_evento,
    TO_DATE(CAST(t.CE178_DATA_SCADENZA AS STRING), 'yyyyMMdd')
                                                    AS data_scadenza,
    TO_DATE(CAST(t.CE178_DATA_PRODUZIONE AS STRING), 'yyyyMMdd')
                                                    AS data_produzione,
    -- Calcolo vita residua rispetto ad oggi
    DATEDIFF(
        TO_DATE(CAST(t.CE178_DATA_SCADENZA AS STRING), 'yyyyMMdd'),
        CURRENT_DATE()
    )                                               AS giorni_alla_scadenza,
    -- Quantità con segno normalizzato
    t.CE178_QTA_EVENTO                              AS qta_evento,
    -- FK dimensioni
    COALESCE(a.articolo_id, -1)                     AS articolo_id,
    COALESCE(s.sito_id,     -1)                     AS sito_id,
    COALESCE(f.fornitore_id,-1)                     AS fornitore_id,
    COALESCE(p.pdv_id,      -1)                     AS pdv_id,
    COALESCE(cal.calendario_id, -1)                 AS data_evento_id,
    -- Audit
    CURRENT_TIMESTAMP()                             AS silver_load_ts,
    DATE_FORMAT(
        TO_DATE(CAST(t.CE178_DATA_EVENTO AS STRING), 'yyyyMMdd'),
        'yyyyMM'
    )                                               AS anno_mese_evento

FROM logistico.bronze_tracciace178 t
LEFT JOIN logistico.gold_dim_articolo   a ON a.articolo_cod = t.CE178_ART_COD
LEFT JOIN logistico.gold_dim_sito       s ON s.sito_cod     = t.CE178_COD_SITO
LEFT JOIN logistico.gold_dim_fornitore  f ON f.fornitore_cod = t.CE178_COD_FORNITORE
LEFT JOIN logistico.gold_dim_pdv        p ON p.pdv_cod       = t.CE178_COD_PDV
LEFT JOIN logistico.gold_dim_calendario cal
    ON cal.data_effettiva = TO_DATE(CAST(t.CE178_DATA_EVENTO AS STRING), 'yyyyMMdd')
;
```

### 5.2 Gold: ciclo vita completo per lotto (aggregazione per LOT_ID)

```sql
-- gold/load_f_tracciabilita_lotti.sql
CREATE OR REPLACE TABLE logistico.gold_f_tracciabilita_lotti
USING DELTA
PARTITIONED BY (anno_mese_carico)
AS
SELECT
    lotto_id,
    articolo_id,
    fornitore_id,
    -- Data e documento di carico iniziale
    MIN(CASE WHEN tipo_evento = 'CARICO' THEN data_evento END)  AS data_carico,
    MIN(CASE WHEN tipo_evento = 'CARICO' THEN num_doc END)      AS num_doc_carico,
    MIN(CASE WHEN tipo_evento = 'CARICO' THEN sito_id END)      AS sito_carico_id,
    -- Data scadenza (costante per lotto)
    MAX(data_scadenza)                                           AS data_scadenza,
    MAX(data_produzione)                                         AS data_produzione,
    -- Quantità totali per tipo evento
    SUM(CASE WHEN tipo_evento = 'CARICO'   THEN qta_evento ELSE 0 END) AS qta_caricata,
    SUM(CASE WHEN tipo_evento = 'USCITA'   THEN ABS(qta_evento) ELSE 0 END) AS qta_uscita,
    SUM(CASE WHEN tipo_evento = 'RESO'     THEN qta_evento ELSE 0 END) AS qta_resa,
    SUM(CASE WHEN tipo_evento = 'SCARTO'   THEN ABS(qta_evento) ELSE 0 END) AS qta_scartata,
    -- QTA_RESIDUA = somma algebrica di tutti gli eventi
    SUM(qta_evento)                                              AS qta_residua,
    -- Data e documento prima uscita
    MIN(CASE WHEN tipo_evento = 'USCITA' THEN data_evento END)  AS data_prima_uscita,
    -- PDV di prima destinazione
    MIN(CASE WHEN tipo_evento = 'USCITA' THEN pdv_id END)       AS pdv_prima_uscita_id,
    -- Numero eventi totali (profondità traccia)
    COUNT(*)                                                     AS n_eventi,
    -- Stato finale del lotto
    CASE
      WHEN SUM(qta_evento) <= 0                          THEN 'ESAURITO'
      WHEN MAX(data_scadenza) < CURRENT_DATE()           THEN 'SCADUTO'
      WHEN MAX(data_scadenza) < DATE_ADD(CURRENT_DATE(), 30) THEN 'IN_SCADENZA'
      ELSE                                                    'ATTIVO'
    END                                                          AS stato_lotto,
    -- Partizione
    DATE_FORMAT(MIN(CASE WHEN tipo_evento = 'CARICO' THEN data_evento END), 'yyyyMM')
                                                                 AS anno_mese_carico

FROM logistico.silver_tracciabilita_lotti
GROUP BY lotto_id, articolo_id, fornitore_id
;
```

---

## 6. Vista compliance: lotti scaduti con giacenza residua

Questa è la vista critica per la compliance CE 178/2002: identifica i lotti con data di scadenza passata che hanno ancora quantità in magazzino. È un indicatore di non conformità che deve essere gestito immediatamente.

```sql
-- gold/view_compliance_ce178.sql
CREATE OR REPLACE VIEW logistico.gold_v_compliance_ce178 AS
SELECT
    f.lotto_id,
    a.articolo_cod,
    a.articolo_desc,
    a.categoria_merceologica,
    s.sito_cod                                      AS sito_giacenza,
    s.sito_desc,
    forn.fornitore_cod,
    forn.fornitore_desc,
    f.data_carico,
    f.data_scadenza,
    -- Giorni di scaduto
    DATEDIFF(CURRENT_DATE(), f.data_scadenza)       AS giorni_scaduto,
    f.qta_residua,
    -- Stima valore economico merce scaduta
    f.qta_residua * COALESCE(a.prezzo_costo, 0)     AS valore_scaduto_eur,
    f.num_doc_carico,
    -- Classificazione gravità
    CASE
      WHEN DATEDIFF(CURRENT_DATE(), f.data_scadenza) > 90  THEN '3-CRITICO'
      WHEN DATEDIFF(CURRENT_DATE(), f.data_scadenza) > 30  THEN '2-GRAVE'
      WHEN DATEDIFF(CURRENT_DATE(), f.data_scadenza) > 0   THEN '1-ATTENZIONE'
    END                                             AS livello_criticita,
    -- Timestamp rilevamento
    CURRENT_TIMESTAMP()                             AS ts_rilevamento

FROM logistico.gold_f_tracciabilita_lotti         f
JOIN logistico.gold_dim_articolo                   a ON a.articolo_id  = f.articolo_id
JOIN logistico.gold_dim_sito                       s ON s.sito_id      = f.sito_carico_id
LEFT JOIN logistico.gold_dim_fornitore          forn ON forn.fornitore_id = f.fornitore_id

WHERE f.stato_lotto = 'SCADUTO'
  AND f.qta_residua > 0
  AND f.data_scadenza < CURRENT_DATE()

ORDER BY livello_criticita DESC, giorni_scaduto DESC
;
```

### Alert automatico lotti scaduti

```python
# Job Databricks schedulato: compliance_check_ce178.py
# Esecuzione: ogni giorno alle 06:00

df_compliance = spark.table("logistico.gold_v_compliance_ce178")
critico_count = df_compliance.filter(F.col("livello_criticita") == "3-CRITICO").count()
totale_count  = df_compliance.count()

if totale_count > 0:
    # Notifica via Teams/email
    send_alert(
        subject=f"CE178 ALERT: {totale_count} lotti scaduti con giacenza residua",
        body=df_compliance.limit(50).toPandas().to_html(),
        severity="CRITICAL" if critico_count > 0 else "WARNING",
        recipients=["qualita@conad.it", "magazzino@conad.it"]
    )
    
    # Log metrica per dashboard
    log_metric("ce178_lotti_scaduti_con_giacenza", totale_count)
    log_metric("ce178_lotti_critici", critico_count)
```

---

## 7. Processo di audit: risposta a ispezioni

### Scenario tipico di ispezione

Un ispettore NAS o ASL richiede: *"Mostrateci tutti i movimenti del lotto XYZ-2025-001 dell'articolo 'Latte Intero 1L' dal momento dell'ingresso in magazzino fino alla consegna ai punti vendita."*

### Procedura di risposta in Databricks (< 30 minuti)

**Step 1: Ricerca lotto per caratteristiche**

```sql
-- Ricerca per articolo + finestra temporale
SELECT lotto_id, data_carico, data_scadenza, qta_caricata, stato_lotto
FROM logistico.gold_f_tracciabilita_lotti f
JOIN logistico.gold_dim_articolo a ON a.articolo_id = f.articolo_id
WHERE a.articolo_desc ILIKE '%latte intero 1l%'
  AND f.data_carico BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY f.data_carico DESC;
```

**Step 2: Dettaglio completo ciclo vita**

```sql
-- Tutti gli eventi per il lotto identificato
SELECT
    s.tipo_evento,
    s.data_evento,
    s.num_doc,
    s.qta_evento,
    sito.sito_desc       AS sito,
    pdv.pdv_desc         AS pdv_destinazione,
    forn.fornitore_desc  AS fornitore
FROM logistico.silver_tracciabilita_lotti s
LEFT JOIN logistico.gold_dim_sito       sito ON sito.sito_id    = s.sito_id
LEFT JOIN logistico.gold_dim_pdv        pdv  ON pdv.pdv_id      = s.pdv_id
LEFT JOIN logistico.gold_dim_fornitore  forn ON forn.fornitore_id = s.fornitore_id
WHERE s.lotto_id = 'XYZ-2025-001'
ORDER BY s.data_evento, s.traccia_id
;
```

**Step 3: Report per ispezione (export CSV/Excel)**

```python
# Il report viene esportato in formato leggibile dall'ispettore
df_report = spark.sql("""
    SELECT 
        lotto_id                    AS "Lotto ID",
        tipo_evento                 AS "Tipo Evento",
        data_evento                 AS "Data Evento",
        num_doc                     AS "Documento",
        qta_evento                  AS "Quantita",
        sito_desc                   AS "Magazzino",
        pdv_desc                    AS "Punto Vendita",
        fornitore_desc              AS "Fornitore",
        data_scadenza               AS "Data Scadenza"
    FROM logistico.silver_tracciabilita_lotti s
    ...
    WHERE s.lotto_id = '{lotto_id}'
    ORDER BY data_evento
""")

# Export su ADLS2 in formato CSV
df_report.coalesce(1).write.csv(
    f"abfss://reports@<storage>.dfs.core.windows.net/ce178/audit_{lotto_id}_{today}.csv",
    header=True
)
```

### SLA per risposta a ispezione

| Tipo richiesta | SLA Oracle attuale | SLA Databricks target |
|---|---|---|
| Ciclo vita singolo lotto | 2-4 ore (query manuale DBA) | < 5 minuti (query self-service) |
| Tutti i lotti di un articolo in periodo | 4-8 ore | < 15 minuti |
| Recall: tutti PDV coinvolti da un lotto | 4+ ore | < 30 minuti (incluso export) |
| Report per autorità (formato istituzionale) | 1 giorno lavorativo | < 1 ora |

---

## 8. Rischi di migrazione

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| 1 | Conservazione dati 5 anni: `silver_tracciabilita_lotti` deve coprire storico completo | Alta | Critico | Backfill completo da Oracle prima del cutover; retention policy Delta: NO cancellazione automatica |
| 2 | DATA_SCADENZA come intero Oracle (YYYYMMDD): conversione | Alta | Medio | Cast esplicito `TO_DATE(CAST(CE178_DATA_SCADENZA AS STRING), 'yyyyMMdd')` già nel silver |
| 3 | QTA_RESIDUA negativa: possibile se USCITA > CARICO (reso non registrato) | Media | Alto | Alert su `qta_residua < 0`; log in tabella `silver_anomalie_ce178` |
| 4 | Lotti senza evento CARICO: resi da PDV pre-sistema | Media | Medio | Gestire con evento sintetico CARICO-IMPLICITO; flag `is_carico_sintetico = TRUE` |
| 5 | Ispezioni durante finestra di manutenzione Databricks | Bassa | Critico | Mantenere accesso di sola lettura su Oracle DWH per almeno 12 mesi post-cutover |
| 6 | GDPR + CE178: dati di tracciabilità non vanno cancellati su richiesta GDPR | Bassa | Critico | Separare identificatori personali (operatori) dai dati lotto; i lotti non contengono PII |
