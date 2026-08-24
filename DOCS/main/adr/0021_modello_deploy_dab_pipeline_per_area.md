# ADR-0021 · Modello di deploy DAB — pipeline per-area (non "wave")

**Status**: accepted (2026-08-22)

**Contesto**:
Con lo split multi-repo (ADR-0016), il repo `logistico-workflows` deve avere **un solo** Databricks Asset
Bundle. Nel monorepo convivono però **due sistemi di job paralleli**:
- **`workflows/*.yml`** — 7 pipeline **per-area** (carichi, giacenze, prep_sped, trasporti, aggregati,
  dim_refresh, landing_ingestion): complete, allineate ai notebook reali e presidiate dai guardrail
  ([[ADR-0019]], [[ACT_9014]], `tests/test_workflows_alignment.py`), con `dq_gate` ([[ACT_9010]]) e compute
  serverless ([[ADR-0009]]). Sono in formato "job nudo" (top-level `name:`/`tasks:`), non `resources: jobs:`.
- **`infra/databricks_bundle/resources/logistica_wave_a.job.yml`** — scheletro **KIT-06 "a wave"** in formato
  DAB corretto, ma **incompleto** (solo wave A, dimensioni omesse, wrapper `run_acceptance.py` inesistente).

Serve scegliere quale sia l'unità di orchestrazione/deploy.

**Alternative considerate**:
1. **Pipeline per-area** (`workflows/*.yml`): un job per area di business. Reale, mantenuto, testato.
2. **Wave KIT-06** (`resources/*.job.yml`): un job per "wave" di rilascio. Solo wave A esiste, incompleta;
   duplicherebbe le pipeline per-area; andrebbe costruito da zero per tutte le wave.
3. **Coesistenza** (wave come raggruppamento sopra le pipeline): doppio set da mantenere allineato.

**Decisione**:
**Opzione 1 — pipeline per-area.** Le 7 `workflows/*.yml` sono la **SoT dell'orchestrazione**. Lo scheletro
`logistica_wave_a.job.yml` viene **archiviato** (riferimento storico, non deployato).
Il **rilascio a fasi** ([[ADR-0017]]) si realizza **abilitando/deployando una pipeline per-area alla volta**
(es. prima `logistica_carichi`, poi le altre) — non servono job "wave" separati per ottenerlo.

**Conseguenze**:
+ Un solo set di job, già allineato ai notebook e **presidiato da test** (nessuna divergenza da mantenere).
+ Phased release conservato (per-area, un job alla volta).
+ `dq_gate` già integrato nelle pipeline per-area.
− I `workflows/*.yml` vanno **wrappati in `resources: jobs: <key>:`** per essere deployabili da DAB, e
  `tests/test_workflows_alignment.py` va adattato a leggere `resources.jobs` invece del top-level.
− Il wheel `logistica_utils` passa dal **Package Registry** (pinnato, DBR-05), non più da build/path locale.
− Lo scheletro wave e il secondo `databricks.yml` (`infra/databricks_bundle/`) vengono rimossi/archiviati.

Esecuzione del consolidamento in un unico `databricks.yml`: → [[ACT_9018]].

**Riferimenti**:
- [[ACT_9018]] (consolidamento databricks.yml), [[ACT_9014]] (DAG per-area), [[ADR-0019]] (DAG derivato),
  [[ADR-0017]] (rilascio a fasi), [[ADR-0016]] (multi-repo), [[ADR-0009]] (serverless), DBR-05 (wheel).
