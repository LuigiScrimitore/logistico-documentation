# Release Kit — Rilascio a fasi Logistico 2.0 (Databricks/Azure)

**Creato:** 2026-07-05 · **Owner:** Team Logistico 2.0
**Scopo:** insieme di artefatti e attività che rendono ogni rilascio in cloud **turnkey**, per un go-live **a fasi** (NON big-bang), una pipeline alla volta, con validazione run-by-run di configurazioni, grant, regolarità dati, timing e costi.

> Documento operativo. Le decisioni di flusso sono interne al team; Reply interviene solo su anagrafiche/setup/standard condivisi ([[reply-scope-governance]]).

---

## 1. Principi guida

1. **Rilascio a fasi, per DAG di dipendenza** — mai big-bang. Ordine: fondamenta → anagrafiche → F_CARICO → altri fact (per wave) → aggregati (per wave, **disaccoppiati** dai fact).
2. **Ogni rilascio è un esperimento controllato**: si rilascia un pezzo, si eseguono run reali, si verificano blocchi (config errate, grant mancanti), regolarità dati, timing e costi; si fa tuning e si procede.
3. **Il tuning locale NON si trasferisce**: driver 12g, spill, `partitionOverwriteMode` sono artefatti single-machine. Su serverless/cluster shuffle, autoscaling e costi vanno **ri-disegnati a fresco**. ⚠️ La **logica** (guard impacted-keys, `full_refresh`, MERGE null-safe, watermark) È trasferibile; il **sizing** no.
4. **Tagging dal primo run**: senza tag di costo non si può monitorare/attribuire la spesa per pipeline → si fa **il prima possibile** (fondamenta).
5. **DQ & alerting interni**: costruiamo una **nostra soluzione** (non ci sono tempistiche né modello dal cliente). Se arriviamo prima noi, il nostro modello può diventare lo standard.
6. **Acceptance criteria espliciti per pipeline**: "funziona?" non è soggettivo (righe attese, orphan-rate, quadratura, SLA).

---

## 2. Ordine di rilascio (DAG)

```
[0] FONDAMENTA (walking skeleton)
     schemi UC + IAM/grant + config/watermark + deploy logistica_utils + TAGGING
        │
[1] ANAGRAFICHE / DIMENSIONI  (LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA,
     LU_AREA, calendario, struttura merceologica)  ← prerequisito dei fact
        │
[2] F_CARICO (pilota end-to-end)  ingestion SFTP → bronze → silver → gold → KPI
        │
[3] ALTRI FACT per wave:  F_PREP_SPED → F_GIACENZE → F_TRASPORTO → F_TURNO →
     F_TRACCIABILITA → F_MOVIMENTAZIONE → F_ORDINI
        │
[4] AGGREGATI A_* per wave (DISACCOPPIATI): rilasciati separatamente, agganciati
     ai fact già in produzione (A_INBOUND dopo F_CARICO, ecc.)
```

**Regole DAG:**
- Le dimensioni **prima** dei fact (altrimenti orphan). Il LAD resolver ([[op32-late-arriving-dimensions]]) copre il late-arriving, non sostituisce l'ordine.
- Gli **aggregati sono disaccoppiati**: ogni A_* si rilascia quando il suo fact sorgente è in produzione e stabile (non insieme al fact).
- F_CARICO come **pilota** perché è il fact più certificato e tocca tutti i layer.

---

## 3. Componenti del Release Kit

### A. Fondamenta / walking skeleton
Valida il plumbing end-to-end "a vuoto" prima dei dati.
- Creazione schemi UC (`bronze/silver/gold/config` + `_dev`/`_prod`, D1-D5).
- IAM/grant **insieme** alla creazione schemi (servono per create/write).
- Tabelle di controllo: `config.logistica_etl` (watermark, parametri).
- Deploy libreria `logistica_utils`.
- **Tagging** (vedi B).
- Smoke-test fondamenta: create/drop tabella dummy per schema, verifica grant read/write.

### B. Tagging & cost monitoring (PRIORITÀ — dal primo run)
- Budget/tag policy `business_unit=logistica` su compute (serverless job) e storage.
- Convenzione tag per **pipeline/wave** (es. `pipeline=f_carico`, `wave=A`) per attribuzione costo granulare.
- Dashboard costi (system tables `system.billing.usage`) filtrata per tag.
- **Obiettivo:** dal 1° run sapere quanto costa ogni pipeline.

### C. Script send SFTP (testabile in dev ORA)
- Script di **send dati → area SFTP Azure** (`stdevdataplatformweudata...:22`), struttura `YYYY/MM/DD`, CSV+Parquet.
- Sorgente: estrazioni Oracle READ-ONLY → landing (Oracle resta read-only, mai update).
- Testabile contro endpoint dev prima della CI/CD.
- Idempotenza upload + retry + logging.

### D. Workflow/DAB per pipeline (dichiarativo)
- Una definizione workflow (Databricks Asset Bundle) **per wave/pipeline**, così il rilascio è dichiarativo e versionato.
- Job cluster **serverless** (confermato Reply/Ippazio 2026-07-03; niente node_type/VM).
- Scheduling che rispetta il DAG (dim → fact → agg); LAD resolver post-refresh dim.

### E. Template acceptance-criteria + smoke-test per pipeline — ✅ KIT-02 IMPLEMENTATO (2026-07-05)
Framework `lib/logistica_utils/acceptance.py`: criteri **dichiarativi** per pipeline + runner che verifica e registra via `dq_monitor`.
- **`AcceptanceCriteria`** (dataclass): min/max righe, `not_null`, `unique_keys` (grana), `orphan_fks`+soglia, `measures_nonneg`, `volume_max_dev_pct`, `sla_seconds`, `sentinel`.
- **`run_smoke_test(spark, criteria, env, run_date, elapsed_s)`**: esegue 7 famiglie di check (table_exists, row_count, not_null, unique_keys, orphan-rate, misure non-negative, volume-anomaly, timing SLA) → `record` su `dq_monitor` con severità (grana/orphan/row_count = **BLOCKING**; misure/volume/SLA = **WARNING**) → `persist()` + `gate()`.
- **`ACCEPTANCE_REGISTRY`**: template compilato per `gold_f_carico` (pilota, soglie calibrate), `gold_f_movimentazione_carrellisti`, `gold_a_inbound_mensile`; scheletri da estendere per gli altri.
- **Validato in locale** (2026-07-05) su dati reali: F_CARICO 13/13, F_MOVIMENTAZIONE 9/9, A_INBOUND 8/8 — tutti pass.

**Uso a fine run pipeline:**
```python
from acceptance import ACCEPTANCE_REGISTRY, run_smoke_test
dq = run_smoke_test(spark, ACCEPTANCE_REGISTRY["gold_f_carico"],
                    env=env, run_date=run_date, elapsed_s=elapsed)
# -> esiti in control_<env>.etl.dq_results; raise DQBlockingError se un BLOCKING fallisce
```
Copre: righe attese, orphan-rate, grana/duplicati, misure, anomalia volumi, SLA. **Quadratura** vs CDT_DW resta separata (`quadratura_fact.py`, cloud-gated).

### F. DQ & alerting interni (nostra soluzione) — ✅ KIT-03/04 IMPLEMENTATI (2026-07-05)
Non aspettiamo il modello cliente: costruito il nostro in `lib/logistica_utils/dq_monitor.py` sopra `dq_helper`.
- **Persistenza canonica**: `control_<env>.etl.dq_results` (stessa area del watermark OP-35). Schema: run_id, env, pipeline, wave, layer, table_name, check_name, **severity**, passed, metric_value, threshold, run_date, run_timestamp, details(JSON). Helper `ensure_dq_table(spark, env)`.
- **Severità**: `INFO` / `WARNING` / `BLOCKING`. `gate()` solleva `DQBlockingError` se un BLOCKING fallisce (ferma la pipeline).
- **Volume-anomaly**: `check_volume_anomaly(table, current_count, max_dev_pct=30)` confronta il row_count con la media storica letta da `dq_results` (PASS se storico < min_history).
- **Alerting pluggable**: `LogNotifier` (default, zero dipendenze) ora; `WebhookNotifier` (Teams/Slack, URL da secret) da attivare in **cloud** (KIT-04). Interfaccia `Notifier.notify(subject, body, severity)`.
- **Regole per layer** (da comporre per pipeline via `record(...)` + i check di `dq_helper`): bronze (schema/row_count), silver (null-safe keys, dedup), gold (orphan, quadratura, range misure).
- **Validato in locale** (2026-07-05): record/severità, volume-anomaly (+80%→WARNING), gate BLOCKING (raise), persistenza su `config_dev.etl.dq_results`.

**Uso tipico in un notebook gold:**
```python
from dq_monitor import DQMonitor, Severity
dq = DQMonitor(spark, pipeline="gold_f_carico", env=env, run_date=run_date, wave="A")
dq.record("orphan_ART_RADICE_COD", passed=(orphan_rate==0), severity=Severity.BLOCKING,
          layer="gold", table_name="F_CARICO", metric_value=orphan_rate, threshold=0.0)
dq.check_volume_anomaly("F_CARICO", current_count=rows, layer="gold")
dq.persist()   # storicizza in control_<env>.etl.dq_results
dq.gate()      # alert su tutti i fail + raise se BLOCKING
```

- **Nota strategica:** modello DQ interno pronto → candidabile a standard (OP-21) se arriviamo prima del cliente.
- **Da fare in cloud (KIT-04):** attivare `WebhookNotifier` (secret URL Teams/Slack).
- ✅ **Wiring del `gate()` nei workflow — FATTO (ACT_9010, 2026-08-04)**: notebook `notebooks/dq/dq_gate.py`
  + task `dq_gate` in coda a `logistica_carichi|giacenze|prep_sped|trasporti|aggregati`; esiti su
  `config_<env>.logistica_etl.dq_results`; `DQBlockingError` → task FAILED → notifica email del job.
  `ACCEPTANCE_REGISTRY` a 9 pipeline. Resta da verificare l'efficacia end-to-end in cloud.

### G. Tuning cloud (ri-disegno, NON trasferire il locale) — ✅ KIT-08 (checklist)
Checklist di ciò che va ri-tarato sul cloud (partendo dai default serverless):
- Memoria/shuffle: NON portare `SPARK_DRIVER_MEMORY=12g` (locale). Serverless auto-gestisce; osservare spill dai Spark UI.
- `partitionOverwriteMode` dynamic/static: ri-verificare comportamento in job concorrenti.
- Guard anti-degenerazione uniche: **la logica resta**, la soglia va confermata sui volumi cloud.
- Autoscaling, photon on/off, dimensione warehouse SQL per MSTR.
- Baseline timing/costo per pipeline → tuning iterativo.

### H. Rollback & idempotenza per pipeline — ✅ KIT-07 (template)
- Rollback plan: Delta **time-travel / RESTORE** a versione precedente per pipeline.
- Re-test idempotenza su cloud (MERGE, replaceWhere) sul primo rilascio di ogni pattern.
- Backup logico: `big_rerun_report.json` equivalente in cloud (esiti run) + `dq_results`.

**Template rollback per tabella (Delta):**
```sql
-- 1) ispeziona la storia e trova la versione buona precedente
DESCRIBE HISTORY gold_prod.logistica.F_CARICO;
-- 2) verifica cosa conteneva quella versione
SELECT count(*) FROM gold_prod.logistica.F_CARICO VERSION AS OF <v_buona>;
-- 3) RESTORE alla versione buona (atomico)
RESTORE TABLE gold_prod.logistica.F_CARICO TO VERSION AS OF <v_buona>;
```
**Template check idempotenza (2 run stesso run_date):**
```
run#1 -> conta righe (partizione run_date) e SUM misura chiave
run#2 (stesso run_date) -> le stesse righe/SUM = idempotente; crescita = MERGE key errata
```
> Regola: prima di ogni rilascio, annotare la **versione Delta pre-rilascio** di ogni tabella toccata (per RESTORE rapido). Su tabelle partizionate preferire `replaceWhere` alla partizione, non overwrite totale.

---

## 4. Gate di accesso → cosa si sblocca

> **Stato gate al 2026-08-27:** ✅ **Git/GitLab** (subgroup + runner) e ✅ **CI/CD** (pipeline in DEV **via Managed
> Identity**, no secret) sono **passati**: `logistico-workflows` `deploy_dev` verde (7 job in DEV), `logistico-lib`
> wheel `v1.0.4` pubblicato. Restano i gate **Azure** (credenziali SFTP) e **IAM/grant** — quest'ultimo è l'unico
> blocco attivo: grant `CREATE SCHEMA` alla MI per sbloccare l'`apply` infra (**OP-INF-1**). Dettaglio:
> `12_checklist_infra_setup.md` / `16_runbook_multirepo_github_gitlab.md`.

| Gate | Sblocca | Attività kit abilitate |
|------|---------|------------------------|
| **Azure** (utenza/RG) | area SFTP, storage, workspace | C (send SFTP), B (tagging), A (schemi) |
| **Git/GitLab** (subgroup+runner) | repo, test script, creazione schemi | D (DAB), test end-to-end, A |
| **IAM/grant** (gruppo UC) | create/write schemi, RBAC | A (fondamenta complete) |
| **CI/CD** (secrets, pipeline) | deploy automatico per fasi | D (rilascio dichiarativo), rollout wave |

**Ordine consigliato:** Azure → (IAM+schemi insieme) → Git/test → CI/CD → rollout per wave.

---

## 5. Attività da mettere in piedi (checklist)

### Ora (pre-accesso — azionabile in locale/dev)
- [x] **KIT-01** Script send SFTP `scripts/sftp/send_to_sftp.py` (dry-run testato: 8419 file/31GB; layout mirror|datefirst; idempotente+retry; import lazy paramiko). ✅ 2026-07-05 — restano da integrare i **parametri SFTP** (host/user/cred via env) + `paramiko` nei requirements
- [x] **KIT-02** Acceptance-criteria + smoke-test: `acceptance.py` (criteri dichiarativi + runner + registry). ✅ 2026-07-05 (validato locale F_CARICO/MOV/A_INBOUND)
- [x] **KIT-03** DQ interno: `dq_monitor.py` — tabella `control_<env>.etl.dq_results`, severità, volume-anomaly. ✅ 2026-07-05 (validato locale)
- [x] **KIT-04** Alerting: interfaccia `Notifier` + `LogNotifier` + `gate()` bloccante; `WebhookNotifier` da attivare in cloud. ✅ 2026-07-05 (design+base; webhook in cloud)
- [x] **KIT-05** Convenzione tag costo `lib/logistica_utils/cost_tags.py` (build_tags + TBLPROPERTIES + apply_table_tags). ✅ 2026-07-05 — da cablare nella budget policy Terraform + default_tags DAB
- [x] **KIT-06** Bozza DAB/workflow per wave `infra/databricks_bundle/` (databricks.yml + wave A template: DAG dim→F_CARICO→smoke-test→LAD, serverless, tag). ✅ 2026-07-05 — host/secret + `run_acceptance.py` wrapper da completare al gate
- [x] **KIT-07** Template rollback/idempotenza per pipeline (Delta RESTORE + check idempotenza). ✅ 2026-07-05 (§3.H)
- [x] **KIT-08** Checklist tuning cloud (cosa NON portare dal locale: memoria/spill/partitionOverwriteMode; ri-tarare su serverless). ✅ 2026-07-05 (§3.G)

### Al gate Azure
- [ ] **KIT-09** Provisioning area SFTP + test upload reale (KIT-01)
- [ ] **KIT-10** Applicazione tag/budget policy (KIT-05) + dashboard costi

### Al gate IAM+schemi
- [ ] **KIT-11** Creazione schemi UC + grant + config/watermark + deploy lib (fondamenta A)
- [ ] **KIT-12** Smoke-test fondamenta (create/drop + grant read/write)

### Al gate Git/CI-CD → rollout per wave
- [ ] **KIT-13** Rilascio **anagrafiche/dim** + acceptance + tuning + costo
- [ ] **KIT-14** Rilascio **F_CARICO** (pilota) + acceptance + quadratura + tuning + costo
- [ ] **KIT-15..N** Rilascio **altri fact** per wave (DAG)
- [ ] **KIT-agg** Rilascio **aggregati A_*** per wave (disaccoppiati, dopo fact stabile)

---

## 6. Rischi presidiati (dal confronto 2026-07-05)

| Rischio | Presidio |
|---------|----------|
| Tuning locale non trasferibile | comp. G — ri-disegno cloud, solo la logica migra |
| DQ/alerting assente (OP-21 senza risposta) | comp. F — soluzione interna, non si aspetta il cliente |
| Costo per fase invisibile | comp. B — tagging dal 1° run |
| Orphan da dipendenze cross-pipeline | §2 DAG — dim prima dei fact |
| "Funziona?" soggettivo | comp. E — acceptance criteria espliciti |
| Idempotenza/rollback su cloud | comp. H — time-travel + re-test |

---

## 7. Riferimenti
`12_checklist_infra_setup.md` (prerequisiti infra + mail), `04_piano_sviluppo.md` (sprint/fasi), `07_certifica_gold_vs_cdtdw.md` (stato fact), `10_piano_migrazione_databricks.md`, `11_devops_handoff_databricks.md`.
