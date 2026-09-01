---
data: 2026-09-01
titolo: Introdotto il worklog (ADR-0024)
autore: luigi.scrimitore
push_monorepo: 435b27d
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0024]
lesson: []
op: []
---

## Cosa è stato fatto
- Introdotto il **worklog** (`DOCS/main/worklog/`): una voce per push su `main`, layer di comunicazione al team distinto da lessons (gotcha per sintomo) e ADR (decisioni).
- `scripts/worklog/`: `worklog_index.py` (INDEX generato, `--check`) + `new_entry.py` (scaffold da diff git). Prime **6 voci retroattive** dai push recenti.

## Novità
- **ADR-0024 nato**. Chiarita la distinzione lessons vs ADR vs worklog.
- `acts/README` — **step 6** del ciclo di vita (voce worklog al push). Nuovo **`CLAUDE.md`** di repo (aggancio sessioni assistite: `worklog/INDEX` + `lessons/INDEX`).

## Doc aggiornati
adr/README_adr, 15_backlog_master, acts/README. Nuovi: adr/0024, worklog/ (README+INDEX+6 voci), scripts/worklog/, CLAUDE.md.

## Stato dopo il push / prossimi passi
Worklog operativo. Da ora: ad ogni push su `main`, `new_entry.py` → completa → `worklog_index.py`. Prossimo tema aperto invariato: **OP-INF-2** (gruppo UC) e accesso container AzCopy (§F.2).
