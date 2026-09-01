---
data: 2026-09-01
titolo: Fix nome gruppo engineer (Group-Engineering-dev) -> OP-INF-2 chiuso, v0.1.6
autore: Luigi Scrimitore
push_monorepo: c8afe89
push_documentation: "n/d (sync @c8afe89)"
push_gitlab: "logistico-infrastructure v0.1.6"
act: [ACT_0.1.6]
adr: []
lesson: []
op: [OP-INF-2]
---

## Cosa e' stato fatto
- ACT_0.1.6: diagnosticato il fallimento dei `grants` dell'`apply` v0.1.5 (schemi+Volume gia' creati). Non era piattaforma ne' permessi MI: solo il **nome del gruppo** errato.
- Fix `infra/terraform/brownfield/variables.tf`: `group_engineers` default `Engineering-dev` -> **`Group-Engineering-dev`** (nome reale verificato nel workspace).

## Novita'
- **OP-INF-2 CHIUSO**: il gruppo reale e' `Group-Engineering-dev` (prefisso `Group-`), gia' assegnato al workspace con `ALL PRIVILEGES`/`MANAGE` su `bronze_dev`. `Group-Data-Science-dev` esiste ma ha meno permessi (non usarlo). Gruppo reader analisti ancora assente (`enable_reader_grants=false`).
- Release **v0.1.6** di `logistico-infrastructure` promossa su GitLab: applica i 6 grants (idempotente, 0 destroy, schemi/Volume intatti).

## Doc aggiornati
04, 05 (OP-INF-2 -> risolto), 12 (A4/B7/B8, sequenza, tabella), 16, ACT_0.1.6, milestones/fase_0.

## Stato dopo il push / prossimi passi
Schemi + Volume creati in DEV; nome gruppo corretto. **Prossimo passo:** ri-lanciare la pipeline `infrastructure` (v0.1.6) + clic `apply` -> completa i 6 grants e chiude l'infra DEV. Poi ingestion (container AzCopy, §F.2).
