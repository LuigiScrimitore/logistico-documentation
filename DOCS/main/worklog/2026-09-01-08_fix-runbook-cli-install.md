---
data: 2026-09-01
titolo: Runbook 17: chiarita install CLI (winget ok, pip legacy deprecato)
autore: Luigi Scrimitore
push_monorepo: 8541a4e
push_documentation: "n/d (sync @8541a4e)"
push_gitlab: "—"
act: []
adr: []
lesson: []
op: []
---

## Cosa e' stato fatto
- Runbook 17 §2 corretto: la CLI **nuova** (winget raccomandato / download / choco-experimental / WSL) è quella giusta; il **deprecato** è `pip install databricks-cli` (legacy v0.17), rimosso come fallback.

## Novita'
- Verificato sui doc Databricks (set. 2026): **winget NON è deprecato**, è il metodo Windows raccomandato per la CLI unificata.

## Doc aggiornati
`17_runbook_seed_landing_manuale.md` (§2).

## Stato dopo il push / prossimi passi
Solo chiarimento doc. Nessun cambio di stato: il kit seed (runbook + wrapper) resta pronto per il primo run.
