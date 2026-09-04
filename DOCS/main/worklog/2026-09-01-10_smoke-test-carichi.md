---
data: 2026-09-01
titolo: Smoke test carichi DEV: bronze+silver verdi E2E su dati reali
autore: Luigi Scrimitore
push_monorepo: "n/d (docs)"
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0025]
lesson: [LL-020, LL-021]
op: []
---

## Cosa e' stato fatto
- Primo run reale della pipeline `logistica_carichi` in DEV su **sandbox personale** (deploy DAB dalla home
  dell'utente), seed manuale di una fetta minima (sito **lgcx**, run_date 2026-09-01) sul Volume `landing_dev`.
- **Validato E2E il dato**: seed -> Volume -> deploy -> serverless -> wheel via `%pip` -> notebook ->
  scrittura Delta. **Bronze (4) + Silver dettagli/testate = SUCCESS**; pesate/traccia = NO_DATA (non seedati).

## Novita'
- **ADR-0025** (accepted-interim): provisioning del wheel su serverless via `%pip` in-notebook (env-dependency da
  Volume/registry non funziona) -> **sblocca DBR-05**; canale definitivo (DAB artifacts / path Workspace) da validare.
- **LL-020**: wheel privato su serverless = `%pip`, non env-dependency; niente pyspark/delta-spark in `install_requires`.
- **LL-021**: UC serverless -> `input_file_name()` vietato (usa `_metadata.file_path`); path mancante letto lazy sfugge
  al try/except (forzare `.columns`). Residuo: robustezza NO_DATA da portare anche lato Silver.

## Doc aggiornati
- `adr/0025_provisioning_wheel_serverless.md` (nuovo) · `lessons/LL-020`, `lessons/LL-021` (nuovi) · `lessons/INDEX.md`.
- (codice non ancora pushato: fix `_metadata.file_path`+skip-path nei 4 bronze carichi, `sys.path` via wheel su ~94
  notebook, `%pip` nei 14 notebook DAG carichi, `setup.py` deps->extras — vedi "prossimi passi").

## Stato dopo il push / prossimi passi
- Pipeline provata E2E fino a Silver su dato reale. Confini aperti: (1) Silver su tabella bronze assente ->
  `TABLE_OR_VIEW_NOT_FOUND` (robustezza NO_DATA); (2) Gold richiede le dim/LU (`logistica_dim_refresh`).
- Prossimo: **push pulito del codice** (disintreccio dal lavoro pregresso + scelta provisioning definitivo) e
  **invio snapshot completa** sulla landing (tutti i siti/tabelle) per ottenere dati anche su pesate/traccia/altri siti.
