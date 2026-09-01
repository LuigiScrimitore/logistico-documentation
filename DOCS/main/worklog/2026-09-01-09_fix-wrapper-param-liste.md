---
data: 2026-09-01
titolo: Fix wrapper seed: parametri lista (string[]) + nota versione CLI runbook
autore: Luigi Scrimitore
push_monorepo: 1b685f6
push_documentation: "n/d (sync @1b685f6)"
push_gitlab: "—"
act: []
adr: []
lesson: []
op: []
---

## Cosa e' stato fatto
- `seed_landing_dev.ps1`: `-Systems/-Sites/-Tables` ora `[string[]]` (join con virgola) → `-Tables a,b,c` funziona senza virgolette (PowerShell li passa come array).
- Incluso il fix runbook 17 §2 (nota versione CLI agnostica) rimasto in sospeso dal push precedente.

## Novita'
- Bring-up CLI utente completato: Databricks CLI v1.14.1 autenticata (PAT via `.databrickscfg` scritto da clipboard `-Raw`; OAuth su Windows fallisce lo store CredMan). Utente in `Group-Engineering-dev`. `fs ls` sul Volume DEV OK (vuoto).

## Doc aggiornati
`seed_landing_dev.ps1`, `17_runbook_seed_landing_manuale.md`.

## Stato dopo il push / prossimi passi
CLI pronta e Volume raggiungibile. **Prossimo passo:** `-DryRun` del wrapper, poi run reale (estrai fetta 01/09 + copia sul Volume) e lancio job DEV.
