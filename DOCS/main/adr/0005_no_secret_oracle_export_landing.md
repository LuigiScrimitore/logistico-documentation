# ADR-0005 · Nessun segreto Oracle in Databricks: pattern "estrazione → export su landing"

**Status**: accepted (retroactive) (2026-07-02)

**Contesto**:
L'as-is estrae i dati dal gestionale **Logistix/Oracle** (e dal DWH CDT_DW per le master). Serve
decidere **come** i dati raggiungono Databricks e **dove** risiedono le credenziali sorgente. Due
vincoli forti di progetto: (1) **Oracle è READ-ONLY** — la pipeline non deve mai scrivere/aggiornare
la sorgente (nemmeno flag di "letto"); (2) **nessun segreto sensibile** (credenziali Oracle) deve
risiedere nel workspace Databricks (superficie di attacco + governance). La scelta determina se il
compute Databricks è accoppiato alla sorgente e chi custodisce le credenziali.

**Alternative considerate**:
1. **Connessione diretta Databricks→Oracle via JDBC**, con segreti Oracle in Key Vault + Secret Scope
   — semplice concettualmente, ma **espone credenziali** nel workspace, **accoppia** il compute alla
   disponibilità/rete di Oracle e viola il vincolo "no segreti sorgente".
2. **Export su landing**: un processo di estrazione **fuori Databricks** deposita file (CSV/Parquet)
   sulla landing (SFTP → UC Volume, ADR-0003); Databricks legge **solo file**. Nessun segreto Oracle
   nel workspace; l'unica auth nel workspace è verso storage/deploy (via GitLab CI/CD).

**Decisione**:
Decisione **D5**: pattern **export su landing**. Databricks **non** si connette a Oracle e **non**
custodisce segreti Oracle. L'auth del workspace riguarda solo storage/deploy (`ARM_*`,
`DATABRICKS_TOKEN`, gestiti come variabili CI/CD mascherate). Key Vault/Secret Scope per Oracle
**soppressi** (l'attività 0.1.4 è stata ridisegnata di conseguenza).

**Conseguenze**:
+ Sicurezza: nessun segreto sorgente nel workspace; Oracle intatto (read-only garantito by-design,
  non c'è nemmeno il canale di scrittura).
+ Disaccoppiamento: la pipeline dipende da **file**, non dalla connettività/finestra di Oracle;
  ingestion e trasformazione hanno cicli indipendenti.
− Introduce la dipendenza dal **meccanismo di export/SFTP** (KIT-01, `send_to_sftp.py`) e dalla sua
  **schedulazione/convenzione path** (OP-07, pending): senza quei file la pipeline non ha input.
− La freschezza del dato dipende dalla cadenza dell'export (fuori dal nostro controllo diretto).

**Riferimenti**:
- Sezione ingestion/landing e sicurezza: `01_architettura.md` (flusso ingestion) e `14_release_kit.md` §C (send SFTP) / §3.A (fondamenta).
- Codice: `scripts/sftp/send_to_sftp.py` (KIT-01). Backlog I-04 (Key Vault soppresso), I-08 (secret CI/CD). OP-07.
- Memory `project-d1-d5-decisions`. Collegate: ADR-0003 (UC Volume), ADR-0016 (multi-repo/CI-CD).
