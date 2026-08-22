# ADR-0001 · Catalog di controllo ETL = `config_dev` (non `control_dev`)

**Status**: accepted (retroactive) (2026-07-02)

**Contesto**:
Il framework ETL medallion (bronze→silver→gold) ha bisogno di **tabelle di controllo** trasversali,
non di business: il **watermark incrementale** (OP-35: ultimo `_bronze_load_date` processato per
`(stage, sistema, tabella, sito)`), i **parametri** di run e — dalla riorganizzazione DQ (KIT-03) —
la tabella **`dq_results`** con gli esiti dei controlli qualità. Queste tabelle devono vivere in un
**catalog Unity Catalog dedicato**, separato dai catalog di dato (`bronze/silver/gold`), perché hanno
ciclo di vita, permessi e retention diversi (sono "infrastruttura ETL", non dato analitico).
Il naming iniziale ipotizzava `control_<env>`, ma la piattaforma dati aziendale (DWH) usa già
`config_*` come catalog di configurazione/controllo: introdurre un `control_*` avrebbe creato una
convenzione parallela sulla stessa piattaforma condivisa.

**Alternative considerate**:
1. **`control_dev` / `control_prod`** — nome autoesplicativo ("control" = tabelle di controllo), ma
   **disallineato** dallo standard della piattaforma condivisa → attrito di governance, rischio di
   naming divergente rispetto agli altri team.
2. **`config_dev` / `config_prod`** — riusa la convenzione DWH esistente. Meno esplicito nel nome, ma
   coerente con la piattaforma; nessun nuovo pattern da far approvare.

**Decisione**:
Decisione **D1**: il catalog di controllo è **`config_dev`** (e `config_prod`), allineato al DWH
aziendale. Implementazione: `get_catalog("control", env)` risolve a `config_<env>`; schema `etl`;
tabelle `config_<env>.etl.watermark`, `config_<env>.etl.dq_results`. In esecuzione **locale** il runner
collassa l'FQN a 3 livelli in 2 livelli (`config_dev_etl.watermark`).

**Conseguenze**:
+ Coerenza con la piattaforma condivisa; nessuna convenzione parallela da negoziare con Reply/Data Platform.
+ Un solo punto (`_CATALOG_MAP` in `utils.py`) risolve i nomi per tutti i layer/ambienti.
− Il nome "config" è meno parlante di "control" per un lettore esterno → mitigato dalla doc e dallo
  schema `etl` che chiarisce lo scopo.
− Vincolo: chi crea nuove tabelle di controllo deve usare `get_catalog("control", env)`, non hardcodare.

**Riferimenti**:
- Sezione decisioni catalog: `10_piano_migrazione_databricks.md` (mapping catalog/ambienti) e milestone `milestones/fase_0.md`.
- Codice: `lib/logistica_utils/utils.py` (`_CATALOG_MAP`, `get_catalog`, `get_control_table`).
- OP-35 (watermark) · KIT-03 (`dq_results`, `lib/logistica_utils/dq_monitor.py`) · memory `project-d1-d5-decisions`.
