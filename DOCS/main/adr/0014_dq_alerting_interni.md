# ADR-0014 · Data Quality & alerting con soluzione **interna** (non attendere il modello cliente)

**Status**: accepted (2026-07-05)

**Contesto**:
Il rilascio a fasi (ADR-0017) prevede di validare ogni pipeline al run ("gira con regolarità?"). Serve un
framework di **Data Quality + alerting** che dia esiti oggettivi e blocchi i rilasci difettosi. Esiste un
open point (**OP-21**) per un DQ framework "condiviso" lato cliente/Reply, ma è **senza risposta né
tempistiche né modello**. Aspettarlo significherebbe rilasciare alla cieca sulla dimensione qualità.

**Alternative considerate**:
1. **Attendere il modello DQ del cliente (OP-21)** — allineato alla governance, ma **bloccante** e senza
   ETA; rischio di rilasciare senza monitoraggio qualità.
2. **Costruire un DQ/alerting interno** sopra l'esistente `dq_helper`, con persistenza, severità e
   alerting pluggable; se pronto prima, candidabile a **standard** (potremmo "imporre" il nostro modello).

**Decisione**:
DQ & alerting **interni** (KIT-03/04): modulo `lib/logistica_utils/dq_monitor.py`. Persistenza canonica
`config_<env>.etl.dq_results` (pipeline, wave, severity, metric, run_date); severità
**INFO/WARNING/BLOCKING** con `gate()` che ferma la pipeline sui BLOCKING; `check_volume_anomaly` (row_count
vs media storica); alerting pluggable (`LogNotifier` ora, `WebhookNotifier` Teams/Slack in cloud).
Integrato con l'acceptance/smoke-test per pipeline (KIT-02, `acceptance.py`).

**Conseguenze**:
+ Non dipendiamo dal cliente per monitorare la qualità; pronti dal primo run.
+ Se arriviamo prima, il nostro modello DQ può diventare lo standard (chiude OP-21 dal basso).
− Se in futuro il cliente imporrà un modello DQ diverso, andrà armonizzato (nuova ADR).
− Il canale webhook va attivato in cloud (secret) — oggi solo `LogNotifier`.

**Aggiornamento 2026-08-04 (ACT_9010) — entrypoint orchestrabile**:
`dq_monitor`/`acceptance` erano **librerie** senza entrypoint, quindi la DQ non era uno step del DAG.
Aggiunto il notebook **`notebooks/dq/dq_gate.py`** (widget `env`/`run_date`/`pipelines`/`wave`/`gate`) e il
task **`dq_gate`** in coda ai 5 workflow che producono Gold (`max_retries: 0`). `ACCEPTANCE_REGISTRY`
esteso da 3 a **9 pipeline**. Le soglie sono calibrate sui **residui noti** (es. `ART_RADICE_COD` escluso
dagli orphan di F_PREP_SPED perché gated su OP-02) per non generare falsi BLOCKING. Dimensioni `LU_*` e
Bronze non ancora coperte (criteri diversi) → follow-up in [[ACT_9010]].

**Riferimenti**:
- Sezione DQ/alerting: `14_release_kit.md` §F (KIT-03/04) e §E (acceptance KIT-02). `05_open_points.md` (OP-21).
- Codice: `lib/logistica_utils/dq_monitor.py`, `lib/logistica_utils/acceptance.py`, `lib/logistica_utils/dq_helper.py`.
- Memory `release-kit`. Collegate: ADR-0017 (rilascio a fasi).
