# ACT_9007 · Allineare workflow e Terraform al compute serverless (ADR-0009)

**Status**: done   **Type**: infra   **Origin**: emerged (cross-check doc-vs-codice, arricchimento ACT 2026-08-01)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (orchestrazione)
**Gg (stima)**: 0.5   **Closed**: 2026-08-04
**Blocco**: 🟢 modifiche locali completate — la **validazione** (`bundle validate`/run) resta ☁️ cloud-gated
**Created**: 2026-08-01
**Dipende da**: —   **Blocca**: coerenza deploy PROD ([[ACT_8.1.2]]), gate cloud ([[ACT_GATE-1]])
**ADR collegate**: ADR-0009 (serverless — **aggiornata** con la correzione implementativa), ADR-0015 (tuning cloud non trasferibile)   **OP collegati**: OP-19, H1 (→ [[ACT_9013]])

## Contesto e motivazione
La decisione ADR-0009 (confermata con Reply) è **compute serverless** per i job. Il cross-check del
2026-08-01 ha rilevato che **tutti i workflow** in `workflows/*.yml` dichiaravano invece un **job cluster
classico** (`Standard_D4s_v3`, `num_workers`, `autotermination`). Approfondendo (doc Databricks ufficiale)
sono emersi **altri 5 difetti collegati**, tutti sullo stesso tema: il modello serverless non era stato
implementato correttamente né nei YML né in Terraform. Andava sanato prima del deploy ([[ACT_8.1.2]]).

## Obiettivo
Workflow, bundle e Terraform coerenti con il modello serverless reale di Databricks; nessuna
configurazione inapplicabile o non valida; dipendenze (wheel) dichiarate nel modo supportato.

## Analisi tecnica — i 6 difetti trovati e come sono stati risolti
| # | Difetto | Correzione |
|---|---------|-----------|
| 1 | 7 YML con **job cluster classico** (contrario ad ADR-0009) | rimossi `job_clusters` e `job_cluster_key`: **i task senza compute girano su serverless** |
| 2 | **`runtime_engine = "SERVERLESS"`** nella cluster policy Terraform | valore **non valido** (ammessi solo `PHOTON`/`STANDARD`) → policy rimossa |
| 3 | **Cluster policy per il serverless**: concettualmente inapplicabile | *"serverless does not support compute policies or init scripts"* → risorsa rimossa da `brownfield/main.tf`, sostituita da nota esplicativa |
| 4 | **`libraries:` a livello job** (campo non valido: nel Jobs API è per-task) + path/nome wheel errati (`../dist/logistica-*.whl`, ma il pacchetto è `logistica_utils` e l'artifact è in `lib/dist/`) | sostituito da blocco **`environments`** job-level + `environment_key: default` sui task; dipendenza corretta `../lib/dist/logistica_utils-*.whl` |
| 5 | **`spark_conf` a livello cluster** (optimizeWrite/autoCompact/shuffle.partitions/photon) | non impostabile su serverless (solo sottoinsieme, a livello **sessione**) → rimosse; Photon/autoscaling sono automatici (ADR-0015: si ritara in cloud) |
| 6 | **`custom_tags`** del cluster per l'attribuzione costi | su serverless non esistono → attribuzione via **serverless usage/budget policy** → nuova [[ACT_9013]] |

**Come si ottiene il serverless (fonte: doc Databricks)**: per un job con notebook task si **omette il
compute**; le dipendenze si dichiarano con un `environments` job-level referenziato da `environment_key`
(per i notebook è l'override del "Notebook Environment"). Per Python script/wheel/dbt `environment_key` è
obbligatorio.

**Blocco applicato ai 7 workflow** (identico):
```yaml
environments:
  - environment_key: default
    spec:
      environment_version: "2"   # allineare alla versione serverless raccomandata al 1o deploy
      dependencies:
        - ../lib/dist/logistica_utils-*.whl
```

**File modificati**
- `workflows/logistica_{carichi,giacenze,prep_sped,trasporti,aggregati,dim_refresh,landing_ingestion}.yml`
  (7 file; `logistica_wave_e.yml` escluso: deprecato/vuoto → [[ACT_9008]]).
- `infra/terraform/brownfield/main.tf` (policy rimossa + nota), `variables.tf` e
  `terraform.tfvars.example` (rimossa variabile dead `spark_version`).
- `databricks.yml` (rimosse variabili dead `spark_version`, `node_type_id`).

## Sviluppo (diario)
- 2026-08-01 · divergenza rilevata durante l'arricchimento delle work-order (fasi 1-7).
- 2026-08-04 · verifica sulla doc Databricks ufficiale → emersi i difetti 2-6; correzione applicata a
  7 YML + Terraform + bundle; ADR-0009 aggiornata; aperta [[ACT_9013]] per il tagging costi.

## Verifica
**Eseguita in locale:**
- `grep` su `workflows/*.yml`: **0** occorrenze di `job_clusters`/`job_cluster_key`/`node_type_id`/
  `num_workers`/`autotermination`/`custom_tags`/`spark_conf`/`libraries:`;
- `environment_key: default` presente su **tutti** i task (6/12/9/3/10/11/6 = 57 task, 1:1 con i `task_key`);
- 1 blocco `environments` per workflow; encoding e line-ending preservati (UTF-8/CRLF, nessun mojibake);
- Terraform: nessun riferimento residuo a `cluster_policy`/`spark_version` nel brownfield; parentesi bilanciate.

**Cloud-gated (non eseguibile ora: nessun CLI Databricks/Terraform in locale, accesso Azure pendente A7)** —
da fare al primo deploy, dentro [[ACT_GATE-1]]:
1. `databricks bundle validate -t dev` verde;
2. il DAB risolve/carica il wheel indicato in `environments.spec.dependencies` (path relativo);
3. `environment_version` accettato e allineato alla versione serverless raccomandata;
4. i job partono effettivamente su serverless e i notebook importano `logistica_utils`;
5. ri-taratura performance (ADR-0015) e assegnazione della usage policy ([[ACT_9013]]).

## Esito
Correzione completata in locale (2026-08-04): **7 workflow** convertiti a serverless con `environments`,
**cluster policy Terraform errata rimossa**, **dead config eliminata** (bundle + tfvars + variables).
ADR-0009 aggiornata con la correzione implementativa e i riferimenti alla doc ufficiale. Aperta [[ACT_9013]]
per l'attribuzione costi (ex `custom_tags`). Restano i 5 punti di validazione cloud sopra.

## Follow-up
- [[ACT_9013]] tagging costi serverless (H1).
- Validazione al gate cloud ([[ACT_GATE-1]], [[ACT_8.1.2]]): `bundle validate`, wheel, `environment_version`.
- `lib/logistica_utils/cost_tags.py` (KIT-05): verificare se assumeva tag su cluster → riallineare (in [[ACT_9013]]).
- Nota operativa (doc Databricks): se cambia l'implementazione del wheel su serverless, **bumpare la versione**
  del pacchetto, altrimenti i job riusano la cache dell'environment.
