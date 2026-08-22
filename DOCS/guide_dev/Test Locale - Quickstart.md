# Test Locale — Quickstart (Piano A)

**Data:** 2026-06-08 · **Versione:** 1.0.0
**Scopo:** simulare la landing zone su PC prima dell'infrastruttura cloud, per testare i mapping colonne e la correttezza dei flussi Bronze/Silver/Gold con **dati reali** estratti dagli schemi Oracle Logistix/STAT/CND.

## 1. Concetto

Lo script `scripts/landing_simulator/extract_oracle_to_landing.py` si collega a Oracle in **sola lettura** ed estrae i dati dai sorgenti (Logistix via db-link multi-sito, STAT via db-link, CND diretto) producendo file CSV nella cartella locale che simula ADLS Gen2:

```
C:\PROGETTI\LOGISTICO_DATA\data\landing\
├── logistix-landing\
│   ├── lgax\<tabella>\YYYY\MM\DD\<tabella>.csv
│   ├── lgcx\<tabella>\YYYY\MM\DD\<tabella>.csv
│   └── lccx\<tabella>\YYYY\MM\DD\<tabella>.csv
├── stat-landing\
│   └── <tabella>\YYYY\MM\DD\<tabella>.csv
└── cnd-landing\
    └── <tabella>\YYYY\MM\DD\<tabella>.csv
```

**Garanzie di sicurezza:**
- Lo script esegue **esclusivamente query SELECT**: nessun UPDATE/INSERT/DELETE sui sorgenti.
- I flag `*_DATA_ESTRAZIONE_DWH` **non vengono mai aggiornati** (per le delta usiamo `NVL(flag,0)=0` come WHERE, oppure il filtro per `date_column` con bind variables).
- Identificatori di tabella, colonna e db-link sono validati su whitelist regex (no SQL injection).
- La sessione Oracle è in autocommit OFF + `ALTER SESSION SET ISOLATION_LEVEL = SERIALIZABLE` (best effort) e termina sempre con `rollback()`.
- I dati estratti sono **fuori dal repo Git** (`C:\PROGETTI\LOGISTICO_DATA\`) e la cartella `data/` è in `.gitignore` di backup.

## 2. Setup (one-time)

```bash
cd C:\PROGETTI\LOGISTICO\scripts\landing_simulator

# 1) Installa dipendenze Python
py -m pip install -r requirements.txt

# 2) Copia .env.example -> .env e compila con le credenziali Oracle
copy .env.example .env
# Apri .env con notepad/VSCode e inserisci ORACLE_HOST / ORACLE_USER / ORACLE_PASSWORD

# 3) Verifica config (apri config.yaml: db-link sito, tabelle, modalita')
notepad config.yaml
```

L'utente Oracle deve avere:
- `SELECT ANY TABLE` su `CDT_SOURCE.*` (per CND) — oppure SELECT puntuali su CNDSTOSTOCK, T_PDV, T_VETTORI, T_TRASP_MTV, T_PREP_SPED.
- Accesso ai db-link `LOG_LGAX`, `LOG_LGCX`, `LOG_LCCX` (e `STAT`) con grant SELECT sulle tabelle remote.

## 3. Esecuzione

### 3.1 Dry-run (raccomandato la prima volta)
Mostra le query che verranno eseguite senza connettersi (utile per validare la config):
```bash
py extract_oracle_to_landing.py --dry-run
```

### 3.2 Estrazione singolo giorno (delta = oggi)
```bash
py extract_oracle_to_landing.py --run-date 2026-06-08
```
- Le tabelle in modalita' **delta** vengono lette con `NVL(flag,0)=0`.
- Le tabelle in modalita' **full** / **snapshot** vengono lette per intero.
- I file landing finiscono in `.../2026/06/08/`.

### 3.3 Backfill su intervallo (lettura piu' profonda del delta giornaliero)
```bash
py extract_oracle_to_landing.py --from-date 2026-05-01 --to-date 2026-06-08
```
- Per le tabelle delta con `date_column` configurata, applica `date_column BETWEEN :from AND :to`.
- Il file landing finisce nella cartella di `--to-date` (ANNO_MESE rappresentativo).
- Le tabelle full/snapshot vengono comunque lette per intero (insensibile al range).

### 3.4 Filtri (utili per testare un sottoinsieme)
```bash
# Solo carichi su 2 siti
py extract_oracle_to_landing.py \
    --systems logistix \
    --sites lgax,lgcx \
    --tables sto_tes_carichi,sto_righe_carico,pesate

# Solo STAT (i 3 Bronze prep-spedizioni di OP-16)
py extract_oracle_to_landing.py --systems stat

# Solo CND
py extract_oracle_to_landing.py --systems cnd
```

### 3.5 Override path output
```bash
py extract_oracle_to_landing.py --output-dir D:\test\landing
```

## 4. Output: file e log

- **File estratti**: in `C:\PROGETTI\LOGISTICO_DATA\data\landing\...`, struttura ADLS-compatibile (`<source>-landing/[sito/]<tabella>/YYYY/MM/DD/<tabella>.csv`).
- **Log esecuzione**: in `C:\PROGETTI\LOGISTICO_DATA\data\logs\extract_<timestamp>.log` con conteggi righe per tabella/sito.
- File con 0 righe: di default **non vengono creati** (`--skip-empty`, comportamento realistico di un push reale). Usare `--no-skip-empty` se si vuole comunque il file con solo header.

## 5. Step successivo: testare il Bronze sul landing locale

Una volta che la landing simulata e' popolata, i notebook Bronze possono leggere da `file:///C:/PROGETTI/LOGISTICO_DATA/data/landing` invece che da `abfss://...`. Modifica solo il widget `landing_base_path` quando esegui localmente in PySpark.

Esempio (PySpark locale, sessione interattiva):
```python
import os, sys
os.environ["LANDING_BASE_PATH"] = "file:///C:/PROGETTI/LOGISTICO_DATA/data/landing"
# poi esegui il notebook Bronze con questo path nel widget
```

Lo stack di test locale (Spark + Delta + stub di dbutils) e' la prossima tappa: vedi spec in `DOCS/Workflow - Revision Spec.md` e il modulo `tests/e2e/` (in arrivo).

## 6. Open points operativi

- **OP-08** — separatore CSV. Lo script usa `;` (default config). Se la sorgente reale userà `,`, basta modificare `config.yaml > csv.separator`.
- **OP-10** — `AREE_MERCEOLOGICHE` ha `WHERE ARM_TIPO_AREA = 1` per default (replica filtro AS-IS). Per landare tutto: rimuovere la riga `where_clause` dal config.
- **OP-11** — carichi SWAP: la query estrae anche i record con `STCAR_TRASFERITO_SWAP` valorizzato. Da chiarire con la sorgente come tracciarli univocamente nel delta.
- **OP-17** — `T_PREP_SPED`: se l'oggetto sorgente non esiste con quel nome (AS-IS lo costruisce internamente), lo script registra un errore e prosegue con le altre tabelle.

## 7. Riferimenti
- `scripts/landing_simulator/config.yaml` — configurazione tabelle/sorgenti
- `scripts/landing_simulator/extract_oracle_to_landing.py` — script di estrazione
- `scripts/landing_simulator/.env.example` — template credenziali Oracle
- `DOCS/Landing & Bronze - Revision Spec.md` — spec Bronze (per i widget e i path)
- `DOCS/Analisi AS-IS Estrazione - CDT_ESTR.md` — meccanismi DELTA/FULL/SNAPSHOT verificati
- `DOCS/Tabelle Sorgenti - Logistico 2.0.xlsx` — inventario sorgenti con tipo caricamento
