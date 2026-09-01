---
data: 2026-09-01
titolo: Runbook 17: seed manuale landing DEV (workaround pre-AzCopy)
autore: Luigi Scrimitore
push_monorepo: 8ea19bf
push_documentation: "n/d (sync @8ea19bf)"
push_gitlab: "—"
act: []
adr: []
lesson: []
op: [OP-GIA-1, OP-QDR-1]
---

## Cosa e' stato fatto
- Nuovo doc **`17_runbook_seed_landing_manuale.md`**: procedura interim per alimentare la landing DEV **a mano** (fotografie giornaliere estratte in locale), in attesa di AzCopy. Baseline 2026-09-01.
- Include: install/config **Databricks CLI** (Windows, PAT), `databricks fs cp --recursive` sul Volume, ordine DAG dim→fact, run via job (valida DBR-05).

## Novita'
- Emersa la possibilità di **copiare a mano** i file nel Volume managed (da dentro UC, no vincolo C6 esterno) → sblocca un **primo run reale in DEV con dati veri** senza aspettare AzCopy.
- Caveat documentati: **quadratura giorno-1 non significativa** ([[OP-QDR-1]], copertura vs storia legacy); **snapshot giacenze non backfillabile** ([[OP-GIA-1]]). CDT_DW resta solo bridge/DQ ([[cdtdw-non-e-sorgente]]).

## Doc aggiornati
Nuovo `17_runbook_seed_landing_manuale.md`.

## Stato dopo il push / prossimi passi
Infra DEV completa; pronto il runbook per seedare la landing a mano. **Prossimo passo:** l'utente installa/config la CLI, estrae la fotografia del 01/09 (fetta minima: dims TABGEN + carichi), copia sul Volume, lancia i job DEV e valida (funzione/orphan, non quadratura).
