# ADR-0004 · Naming ambienti = suffisso di ambiente sul catalog di layer (`_dev`/`_prod`/`_stage`)

**Status**: accepted (2026-07-03)

**Contesto**:
Su una **piattaforma Unity Catalog condivisa** (retail + logistica + altri team) servono nomi catalog
coerenti e non conflittuali per gli ambienti della logistica. La domanda architetturale: la separazione
logistica/retail e dev/prod la si fa a livello di **catalog dedicati per area** (es.
`bronze_logistica_dev`) o **suffisso di ambiente** su catalog di layer condivisi (`bronze_dev`,
`silver_dev`, `gold_dev`), con lo **schema** `logistica` a isolare l'area? La scelta impatta numero di
catalog/grant da gestire, allineamento allo standard di piattaforma e come si attribuiscono i costi.

**Alternative considerate**:
1. **Catalog dedicati per area** (`bronze_logistica_dev`, `gold_logistica_prod`…) — isolamento forte a
   livello catalog, ma **raddoppia ambienti e grant**, devia dallo standard di piattaforma e non porta
   benefici reali di compute (che si separa via tag/policy, non via catalog). **Scartata.**
2. **Suffisso ambiente su catalog di layer** (`bronze_dev`/`bronze_prod`, `silver_*`, `gold_*`,
   `config_*`) + schema `logistica` per l'area + **tag costo** per l'attribuzione (vedi ADR-0014-costi).
   Allineato allo standard piattaforma.

**Decisione**:
Decisione **D4** (confermata 2026-07-03): naming **`<layer>_dev`** / **`<layer>_prod`**; `_stage`
previsto ma non ancora configurato. L'area logistica è isolata dallo **schema** (`.logistica`,
`.logistica_curated`, `.logistica_dm`, `.condiviso`). `get_catalog(layer, env)` è l'unico risolutore.

**Conseguenze**:
+ Allineamento allo standard di piattaforma; meno catalog/grant; compute separato via **tag** (ADR costi)
  e budget policy serverless (ADR-0009), non via proliferazione di catalog.
+ Migrazione dev→prod = cambio del solo suffisso (un punto, `_CATALOG_MAP`).
− Nessun isolamento *fisico* per-area a livello catalog → l'isolamento è logico (schema) + governance
  (grant per gruppo). Mitigato: writer `Engineering-dev`, reader condizionale.
− `_stage` da definire se/quando servirà un ambiente intermedio.

**Riferimenti**:
- Sezione ambienti/catalog: `10_piano_migrazione_databricks.md` e `milestones/fase_0.md` §Decisioni out-of-scope (catalog dedicati scartati).
- Codice: `lib/logistica_utils/utils.py` (`_CATALOG_MAP`). Memory `project-d1-d5-decisions`.
- Collegate: ADR-0009 (serverless), ADR-tag-costi (KIT-05, `lib/logistica_utils/cost_tags.py`).
