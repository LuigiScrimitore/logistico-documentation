---
data: 2026-09-01
titolo: Catena carichi VERDE end-to-end (bronze->silver->gold) su serverless con dati reali
autore: Luigi Scrimitore
push_monorepo: efa616b
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0025]
lesson: [LL-020, LL-021]
op: []
---

## Cosa e' stato fatto
- Seed **completo** (tutti i siti + cdtdw) sulla landing DEV, poi eseguita la catena
  **`landing_ingestion` -> `dim_refresh` -> `carichi`** su serverless con dati reali.
- **Carichi tutto verde E2E**: bronze (4) + silver (dettagli/testate/pesate/traccia/tracciabilita/prep_carico)
  + **`gold_f_carico`** + `gold_late_arriving_handler` + `gold_f_tracciabilita_lotti` = SUCCESS.
  `dq_gate` blocca su **1 check DQ** (gate funzionante, non un bug — dettaglio in `config_dev.logistica_etl.dq_results`).

## Novita' (bug reali serverless fixati, committati in efa616b)
- 4 silver_dim: `# COMMAND ----------` **indentato** dentro `try` -> cella tronca (`incomplete input`).
- `silver_pesate`: cast `'4.0'`->int via double (Oracle NUMBER con decimale).
- `silver_prep_carico`: `partitionOverwriteMode` come **option del writer Delta** (`spark.conf` vietata su serverless).
- `gold_late_arriving_handler`: `.rdd.isEmpty()` -> `.isEmpty()` (RDD vietati su serverless).

## Doc aggiornati
- Solo codice. (Candidati LESSON per la prossima: gotcha serverless — RDD, partitionOverwriteMode via conf, cella indentata.)

## Stato dopo il push / prossimi passi
- Catena carichi provata E2E su serverless. **Residui** (non bloccano carichi): DQ finding del gate (indagare
  `dq_results`); **`partitionOverwriteMode` via `spark.conf` in ~14 notebook** (giacenze/prep_sped/trasporti) da
  convertire a writer-option; `gold_lu_from_cdtdw` merge non idempotente (dedup); `silver_dim_corriere` serve
  bronze `vettori_track` (job trasporti); 2 bronze da `cdt_estr` (non seedato). `databricks.yml` root_path->home
  resta locale. Provisioning wheel = interim `%pip` ([[ADR-0025]]).
