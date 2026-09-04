---
data: 2026-09-02
titolo: "Formalizza follow-up: ACT_9023 cleanup pesata + OP-INF-3 modello dev/qa/prod"
autore: Francesco Foconi
push_monorepo: eef96a9
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9023]
adr: []
lesson: []
op: [OP-INF-3]
---

## Cosa e' stato fatto
- Formalizzati come item azionabili i due follow-up che erano solo prosa nelle voci 03/04:
  - **[[ACT_9023]]** (proposed) — cleanup delle 93 righe `silver.pesata` con `DATA_SCADENZA` pre-fix (`_silver_ts`
    09:25, vecchio cast): riprocesso via `full_refresh` di `silver_pesate`. Verifica: `YEAR(DATA_SCADENZA) > 3000` = 0.
  - **OP-INF-3** — modello ambienti **dev/qa/prod** (dev=sandbox in home, qa=condiviso via CI/MI, prod): da
    formalizzare in un ADR dedicato (anticipato da [[ACT_9022]]).

## Novita'
- Riga backlog per ACT_9023; OP-INF-3 aggiunto in `05_open_points` §C (Infra/CI-CD).

## Doc aggiornati
- `acts/ACT_9023_cleanup-pesata-data-scadenza-pre-fix.md`, `15_backlog_master.md`, `05_open_points.md`.

## Stato dopo il push / prossimi passi
- Follow-up ora tracciati (nessun "da fare" solo nel worklog).
- **Prossimo**: si parte con **ACT_CND-01** (repoint bronze `cnd` dismessa) — nodo 1 (vettori→track) a basso rischio,
  nodi 2/3 (rebuild MTV trasporti, stock da catena) con decisione di dominio.
