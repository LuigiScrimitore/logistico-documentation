# ADR-0017 · Go-live a **fasi** (no big-bang), per DAG di dipendenza, con validazione run-by-run

**Status**: accepted (2026-07-05)

**Contesto**:
Alla ricezione degli accessi cloud (Azure/GitLab/IAM) bisogna portare in produzione ingestion SFTP,
schemi, pipeline e aggregati. Un rilascio **big-bang** (tutto insieme) su una piattaforma brownfield
condivisa massimizza il rischio: un grant mancante, una config errata o un problema di costo/timing si
manifesterebbero su tutto contemporaneamente, difficili da isolare. Serve una strategia che permetta di
scoprire i problemi su una superficie piccola e calibrare cluster/costi progressivamente.

**Alternative considerate**:
1. **Big-bang** — deploy unico di tutti i workflow. Veloce sulla carta, ma blast radius enorme, tuning
   costi/memoria impossibile da isolare, rollback complicato.
2. **Rilascio a fasi per DAG** — una pipeline alla volta, con run reali di validazione, controllo di
   grant/config/regolarità/timing/costi e tuning tra un rilascio e l'altro.

**Decisione**:
Go-live **a fasi**, nell'ordine del **DAG di dipendenza**:
`fondamenta (schemi+IAM+tagging) → anagrafiche/dim → F_CARICO (pilota) → altri fact per wave →
aggregati A_* (disaccoppiati) per wave`. Ogni rilascio: run → acceptance/smoke-test + DQ gate (ADR-0014)
→ verifica costi (tag, ADR-0004) → tuning (ADR-0015) → avanti. Le dimensioni **prima** dei fact (evita
orphan). Supportato dal **release kit** (KIT-01..08) e dai bundle DAB per wave (ADR-0016).

**Conseguenze**:
+ Blast radius minimo; problemi infra isolati per pipeline; tuning costi/memoria su dati veri e progressivo.
+ Coerente col piano sprint/fasi esistente (fasi 0-8, shadow mode) e con lo standard 2-notebook.
− Go-live più lungo nel tempo (non tutto subito); richiede disciplina di acceptance criteria per pipeline.
− Alcune fasi restano **gated** su esterni (BA/quadratura → PROD; anagrafiche → OP-02).

**Riferimenti**:
- Sezione rilascio a fasi: `14_release_kit.md` (principi §1, ordine DAG §2, componenti §3, gate §4). Piano `04_piano_sviluppo.md` (fasi 0-8).
- Codice/kit: `infra/databricks_bundle/` (DAB per wave), `lib/logistica_utils/acceptance.py`, `dq_monitor.py`, `cost_tags.py`, `scripts/sftp/send_to_sftp.py`.
- Memory `release-kit`. Collegate: ADR-0009, ADR-0014, ADR-0015, ADR-0016.
