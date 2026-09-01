---
data: 2026-09-01
titolo: Apply infra DEV parziale — grant MI ottenuto, gruppo Engineering-dev non risolto
autore: luigi.scrimitore
push_monorepo: 4d75de3
push_documentation: "n/d"
push_gitlab: "logistico-infrastructure v0.1.5"
act: [ACT_0.1.6]
adr: []
lesson: [LL-019]
op: [OP-INF-1, OP-INF-2]
---

## Cosa è stato fatto
- ACT_0.1.6: `apply` infra DEV eseguito (in CI, via MSI) → **8 schemi + Volume di landing creati**.
- Fix CI dell'apply: il job `apply` eredita lock+provider dal `plan` (`needs`+`init -lockfile=readonly`; il lock veicolato senza `.terraform/` per non superare il limite artifact).

## Novità
- **OP-INF-1 CHIUSO**: grant `USE CATALOG` + `CREATE SCHEMA` alla MI ottenuti dal team infrastructure.
- **OP-INF-2 APERTO**: i `grants` Terraform falliscono perché il gruppo `Engineering-dev` non è risolvibile nel workspace (→ piattaforma).
- Lesson **LL-019** (apply di un tfplan salvato in CI: lock+provider e stato coerenti col plan).
- `logistico-infrastructure` promosso a **v0.1.5** su GitLab.

## Doc aggiornati
04, 05, 12, 14, 15, 16, ACT_0.1.6, ACT_9012, milestones/fase_0, sprint_0.1/0.2, lessons (LL-019).

## Stato dopo il push / prossimi passi
Schemi + Volume creati in DEV. Blocco residuo: **OP-INF-2** (risoluzione gruppo `Engineering-dev`) per completare i grants; poi ingestion (container AzCopy, §F.2).
