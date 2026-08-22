# ACT_DBR-01 · Databricks-readiness (interventi retro-compatibili DBR-01..07)

**Status**: in-progress   **Type**: infra   **Origin**: backlog DBR-01..DBR-07
**Sprint**: fuori-sprint (sviluppo tecnico offline)   **Fase / Wave**: trasversale (migrazione)
**Gg (stima)**: —   **Blocco**: parziale — DBR-04..07 dipendono da scelte deploy/infra
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: —   **Blocca**: deploy job/lib su cluster (DBR-05/06)
**ADR collegate**: ADR-0001 (config_dev D1), ADR-0002 (bronze.condiviso D2)   **OP collegati**: D1-D5

## Contesto e motivazione
Rendere il codice pronto per Databricks **senza** dipendere dalle decisioni D1-D5 e senza rompere il flusso
locale. Piano completo in `10_piano_migrazione_databricks.md`. Il codice è già UC-native (nomi a 3 livelli
via `get_catalog()`); questi interventi chiudono i gap residui di parametrizzazione e packaging.

## Obiettivo
Codebase deployabile su Databricks (catalog/schema parametrici, wheel + Asset Bundle, workflows) mantenendo
il runner locale invariato.

## Analisi tecnica
- **DBR-01** ✅ modulo `storage.py` (`is_databricks()`, `get_landing_root`/`get_warehouse_root` per-ambiente).
- **DBR-02** ✅ `get_condiviso_schema(env)` in `utils.py` (D2 = `bronze_dev.condiviso`), 7 notebook aggiornati.
- **DBR-03** ✅ `_CATALOG_MAP["dev"]["control"] = "config_dev"` (D1), shim `run_notebook.py` aggiornato.
- **DBR-04** ⬜ backend Spark per `quadratura_fact.py` (auto su Databricks: `spark.table`; pyarrow locale invariato).
- **DBR-05** ⬜ build wheel `logistica_utils` + `databricks.yml` (Asset Bundle) skeleton.
- **DBR-06** ⬜ definire Databricks Workflows (bronze→silver→gold→quadratura) da `run_all_*`.
- **DBR-07** ⬜ strategia repo (superata da ADR-0016 multi-repo: DBR-07 mono-repo **non** applicabile).

## Sviluppo (diario)
- 2026-07-02 · DBR-01/02/03 chiusi (zero-risk, retro-compatibili).

## Verifica
Runner locale invariato dopo ogni intervento; su Databricks: wheel installabile, DAB deployabile, workflow
eseguibili.

## Esito
DBR-01/02/03 consegnati (2026-07-02). DBR-04..06 pendenti; DBR-07 superato da ADR-0016.

## Follow-up
DBR-05/06 abilitano il deploy (collegati a FASE 0 e sprint 0.2 DAB).
