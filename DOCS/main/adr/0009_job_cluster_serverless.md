# ADR-0009 · Compute = job cluster **serverless** (no VM/node_type dedicati)

**Status**: accepted (2026-07-03)

**Contesto**:
I workflow Databricks (bronze/silver/gold, schedulati) hanno bisogno di compute. Le opzioni sono cluster
"classici" (con `node_type_id`, autoscaling di VM, `autotermination_minutes`) oppure **compute
serverless** per i job. La scelta impatta la configurazione (Terraform/DAB), i tempi di avvio, il modello
di costo e la manutenzione. Sulla piattaforma condivisa la separazione dei costi tra aree si fa via
**tag/budget policy**, non via cluster dedicati.

**Alternative considerate**:
1. **Job cluster classici** con `node_type_id`/VM — controllo fine su macchina e autoscaling, ma
   configurazione più pesante (dimensionamento VM, warm-up, autotermination) e manutenzione continua del
   sizing; costi meno trasparenti da attribuire.
2. **Serverless job compute** — niente `node_type_id`/VM da gestire, avvio rapido, sizing gestito da
   Databricks; costo attribuibile via **budget policy con tag** (ADR-0004 / KIT-05).

**Decisione**:
Compute **serverless** per i job (confermato con Reply/Ippazio 2026-07-03). Rimossi
`node_type_id_*`/`autotermination_minutes` dalle variabili Terraform; i job DAB (KIT-06) non dichiarano
`job_clusters`.

**Aggiornamento 2026-08-04 — correzione implementativa (ACT_9007)**
La *decisione* (serverless) resta valida; la sua **implementazione era errata** su due punti, corretti ora:

1. **Non esiste una "cluster policy serverless"**. La risorsa
   `databricks_cluster_policy "logistico-serverless-job-policy"` con `runtime_engine = "SERVERLESS"` è stata
   **rimossa** da `brownfield/main.tf`: (a) i valori ammessi per `runtime_engine` sono solo
   `PHOTON | STANDARD` → `SERVERLESS` non è valido; (b) **le compute policy non si applicano al serverless**
   (come init scripts e `spark_conf` a livello cluster) — valgono solo per il compute classico.
   Rif. doc Databricks: *"Because serverless does not support compute policies or init scripts, you must
   install custom dependencies using the Environment pane"*.
2. **Come si ottiene il serverless nei job**: **non dichiarando alcun compute** nel task. I 7
   `workflows/*.yml` dichiaravano invece un job cluster classico (`Standard_D4s_v3`, `num_workers`,
   `autotermination`) → rimossi. Le **dipendenze** (wheel `logistica_utils`) si dichiarano con un
   **`environments` job-level** + `environment_key` sui task (per i notebook task è l'override del
   "Notebook Environment"). Il precedente `libraries:` a livello job non era nemmeno un campo valido
   (nel Jobs API `libraries` è per-task).

Conseguenze operative della correzione:
- **`spark_conf` a livello cluster non è disponibile** su serverless (solo un sottoinsieme, a livello di
  **sessione**): `optimizeWrite`/`autoCompact`/`shuffle.partitions`/`photon.enabled` sono stati rimossi dai
  YML — Photon e autoscaling sono automatici; se una conf servisse davvero va impostata **in notebook**
  (vedi ADR-0015: si ritara in cloud).
- **`custom_tags` del cluster non esistono** su serverless → l'attribuzione costi passa dalle
  **serverless usage/budget policy** di account (tracciato in [[ACT_9013]], collegato a H1 della checklist).
- Rimosse le variabili dead `spark_version` (Terraform brownfield) e `spark_version`/`node_type_id`
  (`databricks.yml`).
- **Da validare al primo deploy** (cloud-gated, [[ACT_GATE-1]]): valore di `environment_version` e
  risoluzione del path del wheel da parte del DAB.

**Conseguenze**:
+ Meno configurazione e manutenzione (nessun sizing VM); avvio rapido; costi attribuibili via tag.
+ Chiude OP-19.
− **Il tuning di memoria/shuffle NON si trasferisce dal locale** (il `SPARK_DRIVER_MEMORY=12g` locale è
  un artefatto single-machine): su serverless il sizing è gestito e va **osservato/ritarato** a fresco
  (vedi ADR-0015). La *logica* (guard uniche, full_refresh) resta valida.
− Alcune configurazioni Spark low-level non sono disponibili/uguali su serverless → verificare in cloud.

**Riferimenti**:
- Sezione compute/infra: `10_piano_migrazione_databricks.md` e `11_devops_handoff_databricks.md`.
- Terraform: `infra/terraform/brownfield/main.tf` (nota "Compute: SERVERLESS — nessuna cluster policy"),
  `variables.tf`. Workflow: `workflows/*.yml` (blocco `environments`). Bundle: `databricks.yml`.
- Doc Databricks: [Run jobs with serverless compute](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-serverless-jobs) ·
  [Configure the serverless environment](https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/dependencies) ·
  [Bundle configuration examples](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/examples).
- OP-19. Backlog I-05. Esecuzione correzione: [[ACT_9007]]; tagging costi: [[ACT_9013]].
- Collegate: ADR-0004 (naming/costi), ADR-0015 (tuning cloud), ADR-0017 (rilascio a fasi).
