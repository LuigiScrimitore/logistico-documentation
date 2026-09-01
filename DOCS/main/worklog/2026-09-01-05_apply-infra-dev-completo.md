---
data: 2026-09-01
titolo: Infra DEV completa: apply v0.1.6 verde (6 grants), ACT_0.1.6 chiuso
autore: Luigi Scrimitore
push_monorepo: 432d32e
push_documentation: "n/d (sync @432d32e)"
push_gitlab: "—"
act: [ACT_0.1.6]
adr: []
lesson: []
op: []
---

## Cosa e' stato fatto
- **ACT_0.1.6 CHIUSO**: `apply` v0.1.6 su GitLab **verde** — `Apply complete! 6 added, 0 changed, 0 destroyed`. Applicati i 6 `databricks_grants` al gruppo **`Group-Engineering-dev`** sui 6 schemi.
- Sommando v0.1.5: in DEV sono provisionati **8 schemi + Volume `landing_dev.logistica.files` + 6 grants**. Fondamenta Unity Catalog complete.

## Novita'
- **Sprint 0.1 ✅ COMPLETO** (DEV): ACT 0.1.1/0.1.2/0.1.3/0.1.6/0.1.7 passati a done. Milestone FASE 0: infra DEV provisionata (0.1/0.2/0.3 tutti ✅).
- Nessun blocco infra residuo. Gate successivo = **ingestion** (accesso container AzCopy, §F.2 in attesa) e **PROD**.

## Doc aggiornati
04, 12, 15, 16, ACT_0.1.6, sprint_0.1, milestones/fase_0.

## Stato dopo il push / prossimi passi
Infra DEV **completa**. Prossimo passo: ricevere l'accesso al **container AzCopy** (§F.2) per validare il `--send` reale e far atterrare i primi file in landing; poi provisioning **PROD**.
