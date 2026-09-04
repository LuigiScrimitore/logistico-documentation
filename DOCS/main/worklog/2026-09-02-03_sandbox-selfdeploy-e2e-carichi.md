---
data: 2026-09-02
titolo: Sandbox self-deploy (root_path home) + fix JDN + extractor ignore-odi-flag; carichi E2E verde
autore: Francesco Foconi
push_monorepo: 27590e7
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9020]
adr: []
lesson: []
op: []
---

## Cosa e' stato fatto
- **PR #1** `fix(dab)`: `root_path` del target `dev` spostato nella **home utente** (`/Workspace/Users/<me>/.bundle/...`)
  → sblocca il **self-deploy delle sandbox** senza grant sulla cartella condivisa (403 su `mkdirs`). Opzione B
  concordata col team; cartella condivisa riservata a CI/MI.
- **PR #2** `fix(silver)`: `silver_pesate.DATA_SCADENZA` e' un **JDN** → `julian_to_date` (era `.cast("date")`,
  crashava il LAD con "year out of range"). Distinto dai cast int gia' su `main`.
- **PR #3** `feat(landing)` [[ACT_9020]]: extractor `--ignore-odi-flag` (opt-in, default OFF) per il **seed storico**
  delle transazionali; wrapper `seed_landing_dev.ps1` esteso (`-IgnoreOdiFlag` + auto-detect `py -3.12`); runbook 17
  (install CLI). `config.yaml` invariato.

## Novita'
- Emersa la dipendenza fra ignore-odi-flag e fix JDN: seedando lo storico (piu' pesate con `DATA_SCADENZA` JDN)
  il bug JDN si attiva → i due fix vanno insieme. Watermark carichi non bloccante (era 2026-09-01, letto read-only).
- Da valutare col team: ADR **dev/qa/prod** (dev=sandbox in home, qa=condiviso via CI/MI, prod) — la PR #1 la anticipa.

## Doc aggiornati
- `databricks.yml`, `notebooks/silver/carichi/silver_pesate.py`, `scripts/landing_simulator/extract_oracle_to_landing.py`,
  `scripts/landing_simulator/seed_landing_dev.ps1`, `DOCS/main/17_runbook_seed_landing_manuale.md`,
  `DOCS/main/acts/ACT_9020_...md`, `DOCS/main/15_backlog_master.md`.

## Stato dopo il push / prossimi passi
- **Carichi E2E verde in DEV dalla sandbox** (`[dev flabffoconi]`): `dim_refresh` 17/17, `logistica_carichi` SUCCESS,
  `gold_f_carico` 11.022 righe, LAD `NO_LATE_ARRIVING`, `dq_gate` OK (failed=1 non-bloccante). Seed DEV
  logistix+stat+cdtdw sul Volume (partizione 09/02, 3,65M righe con flag ODI ignorato).
- **Cleanup dovuto**: `silver_dev.logistica.pesata` ha 93 righe pre-fix (run 09:25) da ripulire con `full_refresh`.
- **Prossimo**: `ACT_CND-01` (repoint bronze `cnd` dismessa) per giacenze/trasporti; poi altri fact.
