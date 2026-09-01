# worklog/ · Diario di sviluppo (per push su `main`)

**Cos'è:** una voce per ogni push su `main`, che racconta in 8-12 righe *cosa è cambiato* e *dove siamo ora*.
Serve a chi fa `git pull` per orientarsi in 30 secondi. Decisione: [ADR-0024](../adr/0024_worklog_diario_push.md).

**Cosa NON è:** non è una SSOT. Non duplica il dettaglio: **linka** gli id (`ACT_`, `ADR-`, `LL-`, `OP-`);
la verità sta in `acts/`, `adr/`, `lessons/`, `05_open_points`. Ogni voce è uno **snapshot immutabile** del
push: una volta scritta **non si riscrive** (se lo stato cambia, lo racconta la voce del push successivo).

> Per lo **stato corrente** apri l'[INDEX](INDEX.md): la **prima voce** (in alto) è l'ultimo push.

## Come si scrive una voce

Al momento del push su `main`, dopo aver aggiornato ACT/backlog/sprint/doc (vedi
[`../acts/README.md`](../acts/README.md), ciclo di vita, **step 6**):

```bash
# scaffold pre-compilato dal diff (commit range, file toccati, id ACT/ADR/LL/OP rilevati)
python scripts/worklog/new_entry.py --slug backend-azcopy --title "Backend AzCopy per il send"
# ...si apre/crea DOCS/main/worklog/YYYY-MM-DD-NN_backend-azcopy.md → completa narrazione + stato
python scripts/worklog/worklog_index.py        # rigenera INDEX.md
```

`new_entry.py` di default usa il range `<ultima-voce>..HEAD`; con `--range a..b` lo forzi.
`worklog_index.py --check` fallisce (exit 1) se l'INDEX non è allineato — utile in CI/pre-commit.

## Formato di una voce

```markdown
---
data: 2026-08-31
titolo: Backend AzCopy per il send verso landing
autore: luigi.scrimitore
push_monorepo: 9fac961
push_documentation: 3afa581
push_gitlab: "—"
act: [ACT_9012]
adr: [ADR-0023]
lesson: []
op: []
---

## Cosa è stato fatto
- (quali ACT toccate e in che stato: es. ACT_9012 → resolved)

## Novità
- ADR nate/cambiate · lessons nuove · OP aperti/chiusi · info emerse

## Doc aggiornati
- (elenco file)

## Stato dopo il push / prossimi passi
- (1-3 righe: dove siamo, blocchi, prossimo passo)
```

**Regole:**
- **Nome file** `YYYY-MM-DD-NN_slug.md`: `NN` = progressivo del giorno (01, 02…) → l'ordinamento per nome è
  cronologico. Lo assegna `new_entry.py`.
- **8-12 righe** di corpo: se diventa un report, muore. Il dettaglio sta negli id linkati.
- **Append-only**: una voce non si cancella né si riscrive; un codice/nome non si riusa.
- Campi lista vuoti = `[]`.
