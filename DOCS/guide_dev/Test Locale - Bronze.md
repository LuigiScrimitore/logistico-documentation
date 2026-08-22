# Test Locale — Bronze (Piano A, parte 2)

**Data:** 2026-06-09 · **Versione:** 1.0.0
**Scopo:** eseguire i notebook Bronze in locale, sui CSV reali estratti con il landing simulator,
senza Databricks. Valida i mapping colonne, la logica MERGE/OVERWRITE/SNAPSHOT e l'idempotenza.

## 1. Prerequisiti

### 1.1 Java JDK 17 (richiesto da PySpark 3.5)
- Su Windows: installare **Eclipse Temurin JDK 17** (https://adoptium.net) oppure Microsoft OpenJDK 17.
- Verifica: `java --version` deve restituire qualcosa come `openjdk 17.x.x`.
- La variabile `JAVA_HOME` deve puntare al JDK (es. `C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot`).

### 1.2 Hadoop on Windows (winutils)
PySpark su Windows richiede `winutils.exe` e `hadoop.dll` per scrivere file su disco locale.
- Scarica i binari per Hadoop 3.3.x: https://github.com/cdarlint/winutils
- Estrai in `C:\hadoop\bin\` (deve esistere `C:\hadoop\bin\winutils.exe`).
- Imposta variabili d'ambiente:
  - `HADOOP_HOME = C:\hadoop`
  - aggiungi `C:\hadoop\bin` al `PATH`
- Riavvia la sessione PowerShell dopo aver impostato le variabili.

> Se ignori questo passo, PySpark mostrera' warning `winutils.exe not found` ma in molti casi
> riesce comunque a scrivere Delta tables locali. Se vedi errori "(null) entry in command string"
> e' il segnale che winutils serve davvero.

### 1.3 Dipendenze Python
```powershell
cd C:\PROGETTI\LOGISTICO
py -m pip install -r tests\local_bronze\requirements.txt
```

Installa: `pyspark==3.5.0`, `delta-spark==3.2.0`, `pyyaml`.

## 2. Layout cartelle

```
C:\PROGETTI\LOGISTICO_DATA\data\
├── landing\                <- CSV prodotti dal landing simulator (Piano A parte 1)
│   ├── logistix-landing\
│   ├── stat-landing\
│   └── cnd-landing\
└── warehouse\              <- Delta tables generate dai notebook Bronze (creata al primo run)
    ├── bronze_dev.db\
    ├── silver_dev.db\
    └── gold_prod.db\
```

Il warehouse Delta vive **fuori dal repository Git** (in `.gitignore` per sicurezza).

## 3. Esecuzione di un Bronze

### 3.1 Smoke test: notebook semplice senza JOIN (FULL_OVERWRITE)

```powershell
cd C:\PROGETTI\LOGISTICO
py tests\local_bronze\run_notebook.py `
   --notebook notebooks\bronze\anagrafiche\bronze_tabgen.py `
   --run-date 2026-06-09 `
   --siti lgax,lgcx
```

Cosa fa: legge `landing\logistix-landing\lgax\tabgen\2026\06\09\tabgen.csv` (+ lgcx),
unisce i due, scrive Delta `bronze_dev.logistica.tabgen` nel warehouse locale.

Tempi attesi: 30-60 secondi (la prima esecuzione include warmup Spark).

### 3.2 Test su delta giornaliero (MODE=DELTA_MERGE)

```powershell
py tests\local_bronze\run_notebook.py `
   --notebook notebooks\bronze\carichi\bronze_carichi_testate.py `
   --run-date 2026-06-09 `
   --siti lgax,lgcx
```

Cosa fa:
- Legge `sto_tes_carichi.csv` da entrambi i siti
- Aggiunge metadati `_bronze_load_date`, `_bronze_insert_ts`, `_source_file`, `_sito_cod`
- MERGE INTO `bronze_dev.logistica.sto_tes_carichi` su chiave naturale
  `MAG_SITO_COD + STCAR_NRO_CARICO + STCAR_COD_MAGAZZINO`

Esegui due volte: la seconda esecuzione **non aggiunge righe** (idempotenza verificata).

### 3.3 Test snapshot (MODE=SNAPSHOT)

```powershell
py tests\local_bronze\run_notebook.py `
   --notebook notebooks\bronze\giacenze\bronze_giacenze_snapshot.py `
   --run-date 2026-06-09
```
(quando la sorgente CND sara' attiva — al momento `disabled` in config: vedi OP-26 / schema CND)

## 4. Ispezione dei risultati

```powershell
# Lista tutte le tabelle Bronze create, con conteggi
py tests\local_bronze\inspect_delta.py --database bronze_dev

# Schema completo + 5 righe campione di una tabella specifica
py tests\local_bronze\inspect_delta.py --database bronze_dev --table sto_tes_carichi --schema --show 5
```

## 5. Override widget (per test mirati)

I widget standard hanno default sensati per il test locale, ma puoi sovrascriverli:

```powershell
# Esegui un solo sito
py tests\local_bronze\run_notebook.py --notebook ... --siti lgax

# Forza formato CSV (anche se ci sono parquet)
py tests\local_bronze\run_notebook.py --notebook ... --file-format csv

# Override widget arbitrario
py tests\local_bronze\run_notebook.py --notebook ... --set merge_keys=COL1,COL2
```

## 6. Limiti noti

- **Multi-sito non in path**: STAT/CND hanno path unico (no sottocartella sito). Lo script di
  estrazione gia' lo gestisce.
- **`_source_file` su filesystem locale** ritorna `file:///...` invece di `abfss://...`.
  Il regex per `_sito_cod` nei Bronze Logistix funziona comunque (cerca `/logistix-landing/.../`).
- **Performance**: Spark locale e' ~5-10x piu' lento di Databricks. Tabelle con &gt; 100k righe
  possono richiedere alcuni minuti. Per Bronze tipici (50k righe max), ok.
- **CND**: i 5 notebook CND non sono testabili finche' lo schema reale (OP-26) non e' confermato.

## 7. Workflow tipico di sviluppo

1. **Estrai dati freschi**: `py scripts\landing_simulator\extract_oracle_to_landing.py --max-rows 50000`
2. **Esegui Bronze area**:
   ```powershell
   py tests\local_bronze\run_notebook.py --notebook notebooks\bronze\carichi\bronze_carichi_testate.py
   py tests\local_bronze\run_notebook.py --notebook notebooks\bronze\carichi\bronze_carichi_dettagli.py
   py tests\local_bronze\run_notebook.py --notebook notebooks\bronze\carichi\bronze_pesate.py
   ```
3. **Verifica**: `py tests\local_bronze\inspect_delta.py --database bronze_dev`
4. Se i conteggi non tornano o ci sono errori, modifica il notebook e ripeti.

## 8. Prossimo step

Quando il Bronze e' validato sui dati reali, si passa al **Silver locale** (stesso pattern: legge
da `bronze_dev.logistica.*` e scrive `silver_dev.logistica.*`). Stesso `run_notebook.py` funzionera'
sui notebook Silver senza modifiche.
