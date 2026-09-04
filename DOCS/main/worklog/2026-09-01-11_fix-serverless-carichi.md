---
data: 2026-09-01
titolo: Fix serverless carichi committati + base catena gold (landing_ingestion/dim_refresh preparati)
autore: Luigi Scrimitore
push_monorepo: 0794b57
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0025]
lesson: [LL-020, LL-021]
op: []
---

## Cosa e' stato fatto
- Committati i **fix reali** emersi al 1o run serverless: **35 bronze** `input_file_name`->`_metadata.file_path`
  (UC) + skip path mancante; **~94 notebook** `sys.path` risolto dal wheel (find_spec, fallback locale);
  **`%pip`** del wheel-on-Volume in prima cella su carichi + landing_ingestion + dim_refresh, `dependencies: []`;
  **`setup.py`** pyspark/delta-spark -> extras. **Bronze+Silver carichi validati E2E** su dati reali (lgcx).

## Novita'
- **Base della catena gold preparata**: `logistica_landing_ingestion` (bronze anagrafiche) e
  `logistica_dim_refresh` (silver/gold dim + `gold_lu_from_cdtdw`) hanno ora `%pip` + `deps: []` e sono rideployati.
- `databricks.yml` **root_path->home** (sandbox personale) **NON committato**: resta locale per i redeploy.

## Doc aggiornati
- Solo codice qui. ADR-0025 / LL-020 / LL-021 / worklog-10 erano nel push precedente (`4395c29`).

## Stato dopo il push / prossimi passi
- Provisioning wheel = **interim `%pip`** ([[ADR-0025]], target env-level da validare). In corso: **seed completo
  con cdtdw** (lato utente). A seed finito: run **landing_ingestion -> dim_refresh -> carichi (gold)** + fix dei bug
  che emergeranno (come per carichi). Poi: propagazione **single-repo GitHub** (rimandata a milestone stabile) e
  **GitLab** (hold). root_path condiviso da ripristinare / gestire con target dev/qa (ADR futuro).
