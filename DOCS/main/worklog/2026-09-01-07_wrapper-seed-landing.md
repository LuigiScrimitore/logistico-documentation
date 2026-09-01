---
data: 2026-09-01
titolo: Wrapper PowerShell seed_landing_dev (estrai->copia->archivia)
autore: Luigi Scrimitore
push_monorepo: 3cbac76
push_documentation: "n/d (sync @3cbac76)"
push_gitlab: "—"
act: []
adr: []
lesson: []
op: []
---

## Cosa e' stato fatto
- Nuovo `scripts/landing_simulator/seed_landing_dev.ps1`: wrapper del **ciclo giornaliero** estrai→copia→archivia in un comando (estrazione operativi + lookup CDT_DW bridge → `databricks fs cp` ricorsiva sul Volume DEV → zip snapshot → stage svuotato). Modalità `-ReseedZip` per ricaricare Azure da archivio; `-DryRun`, `-Sites`, `-Tables`, `-Systems`.
- Runbook 17 aggiornato con la sezione "Automazione".

## Novita'
- **Retention decisa**: snapshot giornaliero **zippato** in `landing_archive\snap_YYYYMMDD.zip` (ricaricabile se si ripulisce Azure) + stage locale svuotato → disco minimo. Volume DEV accumula la storia.

## Doc aggiornati
`17_runbook_seed_landing_manuale.md` + nuovo script.

## Stato dopo il push / prossimi passi
Kit di seed manuale pronto (runbook + wrapper). **Prossimo passo utente:** install/config Databricks CLI, run `seed_landing_dev.ps1` sulla fetta del 01/09, poi lanciare i job DEV (dim_refresh→carichi) e validare.
