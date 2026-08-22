# Runbook Operativo — Monitoring e Operations Logistico 2.0

**Progetto:** Logistico 2.0 — Migrazione Oracle → Databricks  
**Destinatari:** Team Operations, Team BI, DBA Oracle (in caso di rollback)  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0

---

## Indice

1. [Panoramica workflow e scheduling](#1-panoramica-workflow-e-scheduling)
2. [Come leggere i log Databricks](#2-come-leggere-i-log-databricks)
3. [Alert e soglie configurate](#3-alert-e-soglie-configurate)
4. [Procedure per anomalie comuni](#4-procedure-per-anomalie-comuni)
5. [Come sospendere un workflow](#5-come-sospendere-un-workflow)
6. [Come eseguire un backfill manuale](#6-come-eseguire-un-backfill-manuale)
7. [Contatti e escalation path](#7-contatti-e-escalation-path)
8. [SLA e obiettivi operativi](#8-sla-e-obiettivi-operativi)

---

## 1. Panoramica workflow e scheduling

### Architettura workflow

I workflow Databricks sono organizzati per layer (Bronze → Silver → Gold) con dipendenze sequenziali. Ogni workflow riceve il parametro `run_date` (default: ieri).

```
03:00 ┌─────────────────────────────────────────────────────────┐
      │ wf_bronze_all_daily                                     │
      │   Task 1: bronze_carichi   (15 min, n.partitions=8)     │
      │   Task 2: bronze_giacenze  (20 min, n.partitions=4)     │
      │   Task 3: bronze_prep_sped (25 min, n.partitions=16)    │
      │   Task 4: bronze_trasporti (15 min, n.partitions=4)     │
      │   Task 5: bronze_carrellisti (10 min, n.partitions=4)   │
      │   (Tasks 1-5 in parallelo; stima totale: 25 min)        │
      └─────────────────────────────────────────────────────────┘
03:30 ┌─────────────────────────────────────────────────────────┐
      │ wf_silver_all_daily  [dipende da wf_bronze_all_daily]   │
      │   Task 1: silver_carichi     (15 min)                   │
      │   Task 2: silver_giacenze    (20 min)                   │
      │   Task 3: silver_prep_sped   (30 min) — più complessa   │
      │   Task 4: silver_trasporti   (15 min)                   │
      │   Task 5: silver_carrellisti (10 min)                   │
      │   Task 6: silver_tracciabilita (10 min)                 │
      │   (Tasks in parallelo; stima totale: 35 min)            │
      └─────────────────────────────────────────────────────────┘
04:15 ┌─────────────────────────────────────────────────────────┐
      │ wf_gold_all_daily  [dipende da wf_silver_all_daily]     │
      │   Task 1: gold_f_carico             (10 min)            │
      │   Task 2: gold_f_giacenze_daily     (15 min)            │
      │   Task 3: gold_f_prep_sped          (25 min) — grande   │
      │   Task 4: gold_f_trasp              (15 min)            │
      │   Task 5: gold_f_mov_carr           (10 min)            │
      │   Task 6: gold_f_tracciabilita_lotti (10 min)           │
      │   Task 7: gold_f_prep_prod_oper     (15 min)            │
      │   (stima totale: 30 min)                                │
      └─────────────────────────────────────────────────────────┘
04:50 ┌─────────────────────────────────────────────────────────┐
      │ wf_checks_daily  [dipende da wf_gold_all_daily]         │
      │   Task 1: check_quadratura_kpi    (10 min)              │
      │   Task 2: check_compliance_ce178  (5 min)               │
      │   Task 3: check_dq_gold_tables    (10 min)              │
      └─────────────────────────────────────────────────────────┘
05:10  Fine ciclo giornaliero — tutti i dati disponibili

07:00  wf_giacenze_monthly [1° del mese] — aggregazione mensile stock
07:00  wf_dq_report_weekly [lunedì] — report DQ settimanale
```

### Tabella scheduling

| Workflow | Scheduling | Durata stimata | SLA completamento |
|---|---|---|---|
| `wf_bronze_all_daily` | Ogni giorno ore 03:00 | 25 min | 03:30 |
| `wf_silver_all_daily` | Ogni giorno ore 03:30 | 35 min | 04:15 |
| `wf_gold_all_daily` | Ogni giorno ore 04:15 | 30 min | 04:50 |
| `wf_checks_daily` | Ogni giorno ore 04:50 | 20 min | 05:15 |
| `wf_giacenze_monthly` | 1° del mese ore 07:00 | 45 min | 07:50 |
| `wf_compliance_ce178_alert` | Ogni giorno ore 06:00 | 5 min | 06:10 |
| `wf_dq_report_weekly` | Lunedì ore 07:00 | 20 min | 07:25 |

---

## 2. Come leggere i log Databricks

### Dove trovare i log

**Via UI Databricks:**
1. Navigare: **Workflows** → selezionare il workflow → **Runs**
2. Cliccare sull'ultima run → visualizzare lo stato dei task
3. Cliccare su un task → **Logs** → selezionare `stdout` o `stderr`

**Via Log strutturati JSON (Azure Monitor):**
I notebook scrivono log strutturati nel seguente formato:

```json
{
  "timestamp": "2026-05-29T03:45:12Z",
  "workflow":  "wf_silver_all_daily",
  "task":      "silver_carichi",
  "step":      "resolve_dimensions",
  "level":     "INFO",
  "rows_in":   125432,
  "rows_out":  125398,
  "rows_quarantine": 34,
  "duration_sec": 42,
  "run_date":  "2026-05-28",
  "message":   "Silver carichi completato"
}
```

**Query su Azure Log Analytics:**

```kusto
// Tutti i log delle ultime 24h per workflow:
DatabricksJobs
| where TimeGenerated > ago(24h)
| where WorkflowName contains "wf_gold"
| project TimeGenerated, TaskName, Status, Duration, ErrorMessage
| order by TimeGenerated desc

// Errori delle ultime 24h:
DatabricksJobs
| where TimeGenerated > ago(24h) and Status == "FAILED"
| project TimeGenerated, WorkflowName, TaskName, ErrorMessage
| order by TimeGenerated desc
```

### Interpretare lo stato dei task

| Stato | Colore UI | Significato | Azione |
|---|---|---|---|
| `SUCCESS` | Verde | Task completato correttamente | Nessuna |
| `RUNNING` | Azzurro | Task in esecuzione | Attendere |
| `FAILED` | Rosso | Task fallito con errore | Vedere Sezione 4 |
| `SKIPPED` | Grigio | Task saltato (dipendenza fallita) | Analizzare task precedente |
| `BLOCKED` | Arancione | In attesa di una dipendenza | Normale se dipendenza in RUNNING |
| `TIMEDOUT` | Rosso scuro | Timeout superato | Aumentare timeout o ridurre numPartitions |

### Metriche chiave da monitorare nei log

Per ogni task, verificare nei log:

| Metrica | Campo log | Soglia di attenzione |
|---|---|---|
| Righe quarantena | `rows_quarantine` | > 5% di `rows_in` |
| Durata task | `duration_sec` | > 2× durata baseline |
| Righe output | `rows_out` | < 90% di `rows_in` senza quarantena |
| Errori FK | `lad_count` (Late-Arriving Dim) | > 1% |

---

## 3. Alert e soglie configurate

Gli alert sono configurati su Azure Monitor e inviano notifiche via email e Teams al gruppo `ops-logistico@conad.it`.

| Alert Name | Trigger | Soglia | Severità | Destinatari |
|---|---|---|---|---|
| `ALERT_WF_FAILED` | Qualsiasi workflow in stato FAILED | 1 failure | CRITICO | Cloud Architect + PM |
| `ALERT_SLA_BREACH` | Workflow gold non completato entro le 05:30 | Orario > 05:30 | ALTO | Cloud Architect + PM |
| `ALERT_QUARANTINE_HIGH` | Rate quarantena > soglia | > 5% righe in quarantena | MEDIO | Cloud Architect |
| `ALERT_LAD_RATE` | FK non risolte > soglia | > 1% righe con FK = -1 | MEDIO | Cloud Architect + BA |
| `ALERT_KPI_DELTA` | Delta KPI Databricks vs Oracle > soglia | > 1% su qualsiasi KPI principale | ALTO | Cloud Architect + BA + PM |
| `ALERT_CE178_SCADUTI` | Lotti scaduti con giacenza > 0 | Qualsiasi | CRITICO | Qualità + Magazzino |
| `ALERT_DISK_ADLS` | Utilizzo ADLS2 > soglia | > 85% capacità | MEDIO | Cloud Architect |
| `ALERT_CLUSTER_AUTOSCALE` | Cluster raggiunge max workers | Max workers raggiunti per > 30 min | INFO | Cloud Architect |

**Configurazione alert (Azure Monitor → Alert Rules):**
Navigare: `portal.azure.com` → Resource Group `rg-logistico-prod` → Monitor → Alert Rules

---

## 4. Procedure per anomalie comuni

---

### Anomalia 4.1 — Job fallito per timeout JDBC

**Sintomo:** Task bronze fallisce con errore:
```
java.sql.SQLTimeoutException: ORA-01013: user requested cancel of current operation
```
o
```
com.databricks.backend.daemon.driver.DriverClient$DriverTimeoutException
```

**Causa:** La query JDBC verso Oracle supera il timeout configurato, spesso per numPartitions troppo alto che causa troppe connessioni simultanee, o per carico su Oracle nelle ore notturne.

**Soluzione — step-by-step:**

```
1. Identificare il task fallito: Workflows → ultima run → task FAILED
2. Aprire il log del task e annotare: tabella, numPartitions usato, ora del fallimento
3. Navigare su Databricks: Jobs → Edit Job → selezionare il task
4. Aprire il notebook del task (es. bronze/ingest_carichi.py)
5. Aggiungere override widget: "num_partitions_override" = METÀ del valore attuale
   Esempio: se era 8, impostare a 4
6. Lanciare manualmente il task: "Run now" con parametro num_partitions_override=4
7. Monitorare fino al completamento
8. Se ancora timeout: ridurre ulteriormente a 2, o scaglionare per finestra temporale:
   - Prima finestra: date BETWEEN ieri-1 AND ieri
   - Seconda finestra: date = ieri
9. Dopo il ripristino: creare ticket per ottimizzazione stabile del numPartitions
```

**Prevenzione:** Configurare il parametro `numPartitions` nella tabella `silver_config_ingestion` invece che hardcodato nel notebook.

---

### Anomalia 4.2 — Quadratura fuori soglia

**Sintomo:** Alert `ALERT_KPI_DELTA` attivato, oppure report in MicroStrategy mostra valori diversi da quelli attesi dal business. Esempio: `gold_f_carico` riporta 125.000 righe vs 126.000 di Oracle CDT_DW.

**Causa possibile:** (a) LAD non risolte accumulate, (b) silver non completato correttamente, (c) gold caricato parzialmente, (d) filtro data errato, (e) bug nel notebook.

**Procedura di investigazione (6 step):**

```
STEP 1 — Quantificare il delta
  Query Databricks:
    SELECT COUNT(*) AS cnt_databricks, SUM(qta_ricevuta) AS tot_databricks
    FROM logistico.gold_f_carico
    WHERE data_arrivo = DATE_SUB(CURRENT_DATE(), 1);

  Query Oracle (da DBA):
    SELECT COUNT(*) AS cnt_oracle, SUM(QTA_RICEVUTA) AS tot_oracle
    FROM CDT_DW.F_CARICO
    WHERE TRUNC(DATA_CARICO) = TRUNC(SYSDATE-1);

  Annotare: delta_righe = cnt_databricks - cnt_oracle
            delta_pct   = ABS(delta_righe) / cnt_oracle * 100

STEP 2 — Identificare il layer dove il delta si materializza
  SELECT COUNT(*) FROM logistico.bronze_sto_tes_carichi WHERE DATE(STCAR_DATA_ARRIVO) = DATE_SUB(...);
  SELECT COUNT(*) FROM logistico.silver_carichi WHERE DATE(data_arrivo) = DATE_SUB(...);
  SELECT COUNT(*) FROM logistico.gold_f_carico WHERE data_arrivo = DATE_SUB(...);
  -- Confrontare con Oracle a ciascun livello

STEP 3 — Se delta è in Bronze (bronze < Oracle):
  → Estrazione JDBC incompleta
  → Verificare: ultimo watermark letto; confrontare con Oracle
  → Soluzione: rilanciare bronze con forza reload per la data interessata

STEP 4 — Se delta è in Silver (silver < bronze):
  → Righe in quarantena non conteggiate
  → Query: SELECT COUNT(*) FROM logistico.silver_carichi_quarantine WHERE DATE(bronze_ingest_ts) = ...;
  → Se quarantena alta: vedere Anomalia 4.3

STEP 5 — Se delta è in Gold (gold < silver):
  → Merge parziale o errore nel gold
  → Verificare: log del task gold_f_carico per la data interessata
  → Soluzione: RESTORE TABLE e rilanciare gold

STEP 6 — Se delta non identificato dopo i 5 step precedenti:
  → Escalation a Cloud Architect Senior
  → Non modificare dati; documentare tutto per post-mortem
  → Se impatto su utenti: valutare rollback temporaneo MicroStrategy a Oracle
```

---

### Anomalia 4.3 — Missing dimension log > 5% (Late-Arriving Dimensions)

**Sintomo:** Alert `ALERT_LAD_RATE` attivato. Log silver mostra `lad_count > 5%`. Tabella `silver_carichi_quarantine` cresce anomalmente.

**Causa:** Una dimensione sorgente (fornitore, articolo, sito) non è stata caricata prima della silver transformation, oppure il codice nella sorgente operativa non è ancora presente nelle dimensioni DWH.

**Procedura refresh dimensioni urgente:**

```
1. Identificare quale dimensione manca (leggere log silver o query):
   SELECT error_code, COUNT(*) AS n
   FROM logistico.silver_carichi_quarantine
   WHERE DATE(quarantine_ts) = CURRENT_DATE()
   GROUP BY error_code
   ORDER BY n DESC;
   -- Output esempio: DIM_FK_MISSING_FORNITORE: 1234 righe

2. Per la dimensione mancante, eseguire refresh urgente:
   dbutils.notebook.run("bronze/ingest_dim_fornitore", 0, {"force_reload": "true"})
   dbutils.notebook.run("silver/transform_dim_fornitore", 0, {})
   dbutils.notebook.run("gold/load_dim_fornitore", 0, {})

3. Dopo il refresh, lanciare il processo di retry LAD:
   dbutils.notebook.run("silver/retry_lad_carichi", 0, {
       "run_date": "<data interessata>",
       "max_retry_age_days": "2"
   })

4. Verificare che la quarantena si svuoti:
   SELECT COUNT(*) FROM logistico.silver_carichi_quarantine
   WHERE DATE(quarantine_ts) = '<data interessata>'
   AND resolved = FALSE;

5. Rilanciare gold transformation per la data interessata:
   dbutils.notebook.run("gold/load_f_carico", 0, {"run_date": "<data>"})

6. Se la dimensione mancante è un nuovo fornitore/articolo non ancora inserito:
   → Contattare BA Funzionale per inserimento manuale in gold_dim_fornitore
   → Inserimento: INSERT INTO logistico.gold_dim_fornitore VALUES (...)
   → Ripetere dal step 3
```

---

### Anomalia 4.4 — Delta Lake corruption (DELTA_INVALID o SNAPSHOT_NOT_FOUND)

**Sintomo:** Query su una gold table restituisce:
```
AnalysisException: [DELTA_INVALID_SNAPSHOT] The snapshot version X for table
logistico.gold_f_carico does not exist or has been deleted.
```
o un task fallisce con `DeltaErrors: Failed to find log entry for version X`.

**Causa:** Write parziale interrotto (crash durante scrittura), retention troppo aggressiva, o modifica concorrente non autorizzata.

**Procedura RESTORE TABLE:**

```
-- PASSO 1: Identificare le versioni disponibili
DESCRIBE HISTORY logistico.gold_f_carico;
-- Output: lista di versioni con timestamp e operazione

-- PASSO 2: Verificare l'ultima versione stabile
SELECT * FROM logistico.gold_f_carico VERSION AS OF <N-1>
LIMIT 10;
-- Se restituisce dati: la versione N-1 è valida

-- PASSO 3: Eseguire il RESTORE
RESTORE TABLE logistico.gold_f_carico
TO VERSION AS OF <N-1>;
-- Oppure per data:
RESTORE TABLE logistico.gold_f_carico
TO TIMESTAMP AS OF '2026-05-28T04:00:00';

-- PASSO 4: Verificare integrità dopo restore
SELECT COUNT(*), MAX(data_load) FROM logistico.gold_f_carico;

-- PASSO 5: Rilanciare il gold notebook per recuperare i dati mancanti
-- (quelli che erano nella versione corrotta)
dbutils.notebook.run("gold/load_f_carico", 0, {
    "run_date": "<data dei dati mancanti>",
    "merge_mode": "APPEND"
})

-- PASSO 6: Eseguire VACUUM per rimuovere file orfani
VACUUM logistico.gold_f_carico RETAIN 168 HOURS;
-- NOTA: non ridurre sotto 168 ore (7 giorni) per sicurezza
```

**ATTENZIONE:** Non eseguire RESTORE senza prima aver verificato che la versione target sia effettivamente stabile. Aprire un ticket su Azure Support se la versione stabile non è identificabile.

---

## 5. Come sospendere un workflow

### Via UI Databricks

```
1. Navigare: https://<workspace>.azuredatabricks.net
2. Menu laterale: Workflows → Jobs
3. Trovare il workflow da sospendere (es. wf_gold_all_daily)
4. Click sul nome del workflow
5. In alto a destra: pulsante "Pause" (simbolo ⏸)
6. Confermare la sospensione
7. Verificare: status del workflow diventa "PAUSED"
```

### Via CLI Databricks

```bash
# Installare Databricks CLI: pip install databricks-cli
# Configurare: databricks configure --token

# Elencare tutti i job con ID
databricks jobs list

# Sospendere un job specifico (es. job_id = 12345)
databricks jobs update --job-id 12345 '{"schedule": {"pause_status": "PAUSED"}}'

# Verificare stato
databricks jobs get --job-id 12345 | grep pause_status

# Sospendere tutti i job (script bash):
databricks jobs list --output JSON | jq -r '.jobs[].job_id' | while read id; do
    databricks jobs update --job-id $id '{"schedule": {"pause_status": "PAUSED"}}'
    echo "Paused job $id"
done
```

### Via API REST

```python
import requests

WORKSPACE_URL = "https://<workspace>.azuredatabricks.net"
TOKEN = dbutils.secrets.get("logistico", "databricks_pat")

headers = {"Authorization": f"Bearer {TOKEN}"}

# Lista job
response = requests.get(f"{WORKSPACE_URL}/api/2.1/jobs/list", headers=headers)
jobs = response.json()["jobs"]

# Pausa job specifico
job_id = 12345
requests.post(
    f"{WORKSPACE_URL}/api/2.1/jobs/update",
    headers=headers,
    json={"job_id": job_id, "new_settings": {"schedule": {"pause_status": "PAUSED"}}}
)
```

---

## 6. Come eseguire un backfill manuale

Il backfill manuale serve per rielaborare una data specifica (es. a seguito di un fix o dopo un rollback).

### Procedura standard

```
1. Accedere a Databricks Workspace
2. Navigare: Notebooks → ops/backfill_manuale.py
3. Aprire il notebook
4. Impostare i widget (in alto al notebook):
   - run_date: data da rielaborare (es. 2026-05-28)
   - area: ALL / CARICHI / GIACENZE / PREP_SPED / TRASPORTI / CARRELLISTI
   - layer: ALL / BRONZE / SILVER / GOLD
   - force_reload: TRUE per cancellare dati esistenti e ricaricare
5. Cliccare "Run all" (▶▶)
6. Monitorare l'output del notebook
7. Al termine, verificare i conteggi nelle gold tables
```

### Via workflow parametrizzato (metodo raccomandato)

```
1. Navigare: Workflows → Jobs → wf_bronze_all_daily
2. Cliccare "Run now" (pulsante ▶)
3. Nel dialog "Run with parameters":
   - run_date: "2026-05-28"       ← data da rielaborare
   - force_reload: "true"          ← sovrascrive dati esistenti
4. Cliccare "Confirm"
5. Il workflow si avvia manualmente; monitorare su "Runs"
6. Ripetere per wf_silver_all_daily e wf_gold_all_daily nello stesso ordine
```

### Backfill per range di date (più giorni)

```python
# Eseguire nel notebook ops/backfill_range.py
# ATTENZIONE: può richiedere ore su range lunghi

from datetime import date, timedelta

start_date = date(2026, 5, 20)
end_date   = date(2026, 5, 28)

current = start_date
while current <= end_date:
    run_date = current.strftime("%Y-%m-%d")
    print(f"Processing {run_date}...")
    
    dbutils.notebook.run("bronze/ingest_carichi", timeout_seconds=3600,
                         arguments={"run_date": run_date, "force_reload": "true"})
    dbutils.notebook.run("silver/transform_carichi", timeout_seconds=1800,
                         arguments={"run_date": run_date})
    dbutils.notebook.run("gold/load_f_carico", timeout_seconds=1800,
                         arguments={"run_date": run_date})
    
    current += timedelta(days=1)
    print(f"Completed {run_date}")
```

---

## 7. Contatti e escalation path

### Team operativo

| Ruolo | Nome | Email | Mobile | Disponibilità |
|---|---|---|---|---|
| Operations Lead (L1) | [INSERIRE] | ops@conad.it | [mobile] | 06:00-22:00 |
| Cloud Architect (L2) | [INSERIRE] | [email] | [mobile] | Reperibile H24 |
| DBA Oracle (L2) | [INSERIRE] | [email] | [mobile] | Reperibile H24 |
| BA Funzionale (L2) | [INSERIRE] | [email] | [mobile] | 08:00-18:00 |
| PM Progetto (L3) | [INSERIRE] | [email] | [mobile] | 08:00-20:00 |

### Escalation path

```
Problema rilevato (alert automatico o segnalazione utente)
    ↓
L1 - Operations Lead (entro 15 min)
    ↓ se non risolto in 30 min
L2 - Cloud Architect (entro 15 min dalla chiamata)
    ↓ se non risolto in 30 min
L3 - PM Progetto + decisione rollback se necessario
    ↓ se impatto critico business
Responsabile Business (Direzione Logistica)
```

### Canali di comunicazione

| Priorità | Canale | Quando usare |
|---|---|---|
| Critico (SLA a rischio, impatto utenti) | Chiamata diretta | Immediatamente |
| Alto (job falliti, alert attivati) | Teams — canale "Logistico Ops" | Entro 5 min da alert |
| Medio (anomalie non bloccanti) | Email ops@conad.it | Entro 30 min |
| Basso (informativo, ottimizzazioni) | Ticket JIRA/ServiceNow | Durante orario lavorativo |

---

## 8. SLA e obiettivi operativi

### SLA principali

| Metrica | Obiettivo | Misurazione |
|---|---|---|
| Completamento tutti i workflow | Entro le 05:30 ogni giorno | Azure Monitor: orario ultimo task gold completato |
| Dati disponibili in MicroStrategy | Entro le 06:00 ogni giorno | Test automatico: query MicroStrategy ogni 10 min dalle 05:00 |
| Risposta a incident critico | < 30 min per attivazione L2 | On-call rotation + Azure Monitor alert |
| Risoluzione incident critico | < 2 ore dalla rilevazione | SLA MTTR (Mean Time To Resolve) |
| Disponibilità report MicroStrategy | > 99.5% mensile | Azure Monitor: uptime monitoring |
| Completamento ciclo CE178 alert | Entro le 06:15 ogni giorno | Workflow check completato con 0 errori |

### Monitoraggio SLA

**Dashboard operativa:** Disponibile su Databricks SQL — Dashboard "Logistico Ops Daily":
- URL: `https://<workspace>.azuredatabricks.net/sql/dashboards/...`
- Mostra: stato workflow, conteggi per area, alert attivi, storico 7 gg

**Report settimanale automatico:** Ogni lunedì ore 07:00, workflow `wf_dq_report_weekly` genera e invia via email:
- Statistiche completamento settimana precedente
- Tasso quarantena per area
- Delta KPI vs baseline
- Ticket aperti e risolti

### Definizione "completamento workflow"

Il workflow giornaliero è considerato "completato" quando:
1. Tutti i task gold sono in stato SUCCESS
2. Il check di quadratura ha delta < 1% su tutti i KPI principali
3. Il check CE178 è stato eseguito (indipendentemente dal numero di lotti scaduti)
4. Nessun alert critico attivo al momento del completamento

Se la condizione 2 non è soddisfatta ma il delta è < 2%, il workflow è "completato con warning": gli utenti vengono notificati che i dati potrebbero avere una piccola discrepanza e il team indaga nella mattinata.
