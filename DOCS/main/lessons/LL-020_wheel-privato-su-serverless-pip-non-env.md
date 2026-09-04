---
id: LL-020
titolo: Wheel privato su compute serverless — installalo con %pip in-notebook, non come env-dependency; e non dichiarare pyspark/delta-spark
sintomi:
  - "IllegalStateException: Internal error: notebook command received after detach (dopo ~3 min, notebook_output vuoto)"
  - "Library installation failed: Unable to find or download the required package or its dependencies"
  - "il build dell'environment serverless resta appeso e il task va in retry senza mai eseguire il notebook"
tag: [databricks, serverless, dab, wheel, pip, dbr-05]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-09-01
origine: [smoke-test-carichi-dev]
---

## Sintomo
Deployi un job serverless (DAB) il cui `environments.dependencies` dichiara il wheel privato `logistica_utils`.
Al run il task **non esegue il notebook**: o `Library installation failed: Unable to find or download the
required package` (fail rapido), oppure `notebook command received after detach` dopo ~3 minuti con
`notebook_output` vuoto (`execution_duration ~200s`, poi il compute si stacca e va in retry).

## Strada sbagliata
- Dichiarare `logistica_utils==X` come dipendenza d'ambiente **senza index**: il serverless lo cerca su **PyPI
  pubblico** → 404 (è privato nel Package Registry GitLab, per giunta **on-prem irraggiungibile** dal serverless Azure).
- Passare a un **wheel su Volume UC** come `environments.dependencies` (`/Volumes/.../x.whl`): il build
  dell'environment gira **prima** che il contesto UC/Volume sia disponibile → non lo raggiunge → appeso → detach.
- Lasciare `pyspark`/`delta-spark` in `install_requires` del wheel: il serverless tenta di **reinstallarli** sopra
  lo Spark del runtime (~300 MB) → build lento e instabile → concorre al detach.

## Regola
1. **Install a runtime, non a build**: prima cella del notebook
   ```python
   # MAGIC %pip install /Volumes/landing_dev/logistica/files/_wheels/logistica_utils-1.0.0-py3-none-any.whl
   ```
   Gira nel notebook con identità/accesso UC attivi → legge il Volume e installa in modo affidabile.
2. **Il wheel NON dichiara i runtime forniti**: `pyspark`/`delta-spark` vanno in `extras_require` (uso locale/test),
   `install_requires=[]`. Vedi [[LL-021]] per gli altri scogli UC dei notebook bronze.

## Perché
Il build dell'environment serverless è una fase separata e anticipata: non ha ancora il contesto UC, quindi un
riferimento a un Volume non è risolvibile, e reinstallare pyspark destabilizza l'ambiente. `%pip install` invece
è notebook-scoped e avviene quando compute e credenziali ci sono: è il canale supportato per un wheel privato.

## Conferme e contraddizioni
- 2026-09-01 · luigi.scrimitore · smoke test `logistica_carichi` DEV (sandbox personale): env-dependency da
  Volume → 3 tentativi × ~200s tutti `detach`; passaggio a `%pip` in prima cella → i 4 task bronze e i silver
  con dati vanno **SUCCESS**. Interim adottato: `%pip` per-notebook; provisioning definitivo (env-level via DAB
  artifacts / path Workspace) da validare — vedi ADR-0025 / DBR-05.
