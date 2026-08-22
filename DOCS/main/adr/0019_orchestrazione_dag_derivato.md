# ADR-0019 · Orchestrazione: il DAG dei workflow si **deriva** dal codice, non si scrive a mano

**Status**: accepted (2026-08-04)

**Contesto**:
I `workflows/*.yml` (Databricks Asset Bundles) sono stati scritti a mano a giugno 2026 e **non sono stati
aggiornati** durante le riscritture successive della pipeline (standard 2-notebook ADR-0007, catena
rebuilt-from-raw, rimozione rami secchi RS-01..08). Risultato misurato il 2026-08-04 ([[ACT_9014]]):
**6 `notebook_path` puntavano a notebook inesistenti** e **52 notebook su 104 non erano orchestrati** —
tra cui un fact certificato (`gold_f_turno_prep_sito`), il LAD resolver e l'intera catena silver curated.

Il problema è strutturale, non un refuso: `databricks bundle validate` **non verifica** che i notebook
esistano, quindi il deploy passa e il guasto emerge a runtime. Inoltre la "verità" operativa era finita nel
runner locale (`tests/local_bronze/run_big_rerun.py`), creando **due descrizioni divergenti** della stessa
pipeline.

**Alternative considerate**:
1. **Correggere i YML a mano** (una volta): risolve il sintomo, ma il disallineamento si riformerà alla
   prossima riscrittura — è già successo.
2. **Generare i YML interamente da codice a ogni build**: massima coerenza, ma i YML smettono di essere
   leggibili/versionabili come artefatto rivedibile e si perde il controllo su schedule, retry, timeout.
3. **DAG derivato + guardrail in test** (scelta): i task e le loro dipendenze si derivano dal **grafo
   read/write reale** dei notebook; i YML restano artefatti versionati e leggibili; un test impedisce la
   regressione.

**Decisione**:
**Il DAG si deriva dal codice, il YML resta l'artefatto.**
1. **Dipendenze**: `depends_on` derivate dal grafo *chi-scrive-cosa* / *chi-legge-cosa* estratto dai notebook
   (`spark.read.table` / `saveAsTable` / `SOURCE_TABLE`/`TARGET_TABLE`). Per i Bronze — che scrivono su
   tabella a nome dinamico — la tabella si ricava dalla costante `TABLE_NAME`, abilitando le dipendenze
   bronze→silver che altrimenti mancherebbero.
2. **Parametri**: i `base_parameters` si derivano dai **widget realmente dichiarati** nel notebook: nessun
   parametro inventato e nessuno dimenticato.
3. **Assegnazione ai workflow per dominio**, con due scelte esplicite:
   - le **anagrafiche condivise** (incluse `artdgene`/`apvpunto_vendita`) stanno in
     `logistica_landing_ingestion` (00:30) perché servono al `dim_refresh` (01:00), non al dominio in cui
     erano finite per collocazione di cartella;
   - il **LAD resolver** (OP-32) gira **tra i fact e gli aggregati** — in testa a `logistica_aggregati` — così
     gli `A_*` leggono fact con le FK già risolte (chiude il residuo L-03).
4. **Guardrail**: `tests/test_workflows_alignment.py` verifica a ogni run che ogni `notebook_path` esista,
   che le `depends_on` puntino a task esistenti, che non ci siano cicli, che il compute sia serverless
   (ADR-0009) e che **nessun notebook resti orfano** fuori da una allow-list motivata.

**Conseguenze**:
+ Una sola descrizione della pipeline: i YML non possono più divergere dal codice senza far fallire i test.
+ Le dipendenze sono quelle vere (derivate dai dati letti/scritti), non quelle ricordate da chi scrive il YML.
+ Aggiungere/rinominare un notebook produce un test rosso finché non è orchestrato o esplicitamente escluso.
− Le dipendenze **cross-workflow** non sono esprimibili con `depends_on` (job distinti): restano garantite
  dagli **schedule sfalsati** (00:30 → 01:00 → 02:00 …). Miglioramento futuro: `run_job_task` o trigger su
  aggiornamento tabella per legarli esplicitamente.
− L'allow-list degli orfani va mantenuta con disciplina: è il punto dove si può nascondere un buco.

**Riferimenti**:
- Esecuzione e audit: [[ACT_9014]]. Compute serverless: ADR-0009 ([[ACT_9007]]). DQ gate: ADR-0014 ([[ACT_9010]]).
- Standard notebook: ADR-0007. Incrementale/idempotenza: ADR-0010. LAD: ADR-0011, OP-32.
- Fonte di verità usata per la ricostruzione: `tests/local_bronze/run_big_rerun.py` (flusso validato sui 22 siti).
