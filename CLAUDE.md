# CLAUDE.md — Logistico 2.0

DWH logistico su **Azure Databricks** (Unity Catalog, architettura medallion) — pipeline **PySpark/Delta**,
CI **GitLab**, **Terraform** brownfield. Multi-repo ([[ADR-0016]]): **GitHub = SoT sviluppo** (4 repo),
**GitLab cliente = release** (3 repo, mai `documentation`). Auth CI = **Managed Identity**, nessun secret
([[ADR-0022]]).

## Da leggere per orientarsi (in quest'ordine)

- **Stato corrente** → [`DOCS/main/worklog/INDEX.md`](DOCS/main/worklog/INDEX.md): la voce **in alto** è
  l'ultimo push (cosa è cambiato, dove siamo). Decisione: [[ADR-0024]].
- **Gotcha per sintomo** → [`DOCS/main/lessons/INDEX.md`](DOCS/main/lessons/INDEX.md): se sbatti contro un
  errore, cerca il **sintomo**. Decisione: [[ADR-0020]].
- **Indice unico** (attività + decisioni) → [`DOCS/main/15_backlog_master.md`](DOCS/main/15_backlog_master.md).
- **Aperti / blocchi** → [`DOCS/main/05_open_points.md`](DOCS/main/05_open_points.md).

## Mappa artefatti (chi risponde a cosa)

| Artefatto | Domanda |
|---|---|
| `acts/` | come si fa/si è fatta *questa attività* (SSOT) |
| `adr/` | perché abbiamo deciso *X* |
| `lessons/` | ho *questo sintomo*, come lo risolvo |
| `sprint_agile/` + `milestones/` | a che punto è *la fase* |
| `05_open_points` | cosa è ancora *aperto* |
| `worklog/` | *cosa è cambiato con questo push, dove siamo* |

## Regole di lavoro

- **Al completamento di una ACT** aggiorna nell'ordine (vedi `DOCS/main/acts/README.md`, ciclo di vita):
  ACT → `15_backlog_master` → sprint → doc globali impattati → eventuali ADR/ACT-9000 → **voce worklog del
  push** (`scripts/worklog/new_entry.py` + `worklog_index.py`).
- **Indici generati** (`lessons/INDEX.md`, `worklog/INDEX.md`): non editare a mano, **rigenerare** con i
  rispettivi script.
- **Segreti**: mai `.env` / `terraform.tfvars` / token nei repo. Auth via Managed Identity.
- **Push**: sviluppo su GitHub (branch → PR → `main`); `documentation` **solo GitHub**, mai GitLab.
