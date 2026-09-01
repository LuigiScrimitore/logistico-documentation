# ADR-0024 · Worklog — diario di sviluppo per push su `main`

**Status**: accepted (2026-09-01)

**Contesto**:
Il progetto ha già gli artefatti di **reference/SSOT**: **ACT** (attività), **ADR** (decisioni), **lessons**
(gotcha indicizzati per sintomo, [[ADR-0020]]), `05_open_points` (registro OP), `sprint_agile/` + `milestones/`
(stato a cadenza), `15_backlog_master` (indice). Tutti si **tirano quando servono**.
Manca invece un artefatto **cronologico, per-push**, che un collega legga **subito dopo un `git pull`** per
capire in 30 secondi *cosa è cambiato* e *dove siamo ora*. Esempio reale: il push del 2026-09-01 ha **chiuso
OP-INF-1**, **aperto OP-INF-2**, fatto un **apply parziale** — oggi lo si ricostruisce solo leggendo 4 doc.
Le **lessons** non coprono questo (sono un KB per-sintomo, non un broadcast di stato); gli **ADR** nemmeno
(decisioni, non cronologia). È un buco di **comunicazione al team**, non di reference.

**Alternative considerate**:
1. **`CHANGELOG.md` unico** — macchina da conflitti git (vincolo *merge* di [[ADR-0020]]) e cresce fino a non
   essere più letto. Scartata.
2. **Affidarsi ai commit message** — troppo granulari, senza narrazione di stato/novità/doc aggiornati.
3. **Estendere lessons o sprint** — snaturerebbe artefatti con scopo diverso.
4. **Worklog dedicato**, one-file-per-voce + indice generato — **scelto**.

**Decisione**:
**Worklog** in `DOCS/main/worklog/`, **una voce per push su `main`**.
- File `YYYY-MM-DD-NN_slug.md` con frontmatter. **Un file per voce = merge-safe** (come le lessons).
- **INDEX generato** (`scripts/worklog/worklog_index.py`), newest-first: la **voce più recente = "stato
  corrente"**. Non si edita a mano (come `lessons/INDEX.md`).
- **Scaffold generato da git** (`scripts/worklog/new_entry.py`): commit range + file toccati + id
  `ACT_/ADR-/LL-/OP-` rilevati dal diff → pre-compilati; l'umano scrive 3 righe di narrazione + lo stato.
- **È un *view*, non una SSOT**: linka gli id, **non duplica** il dettaglio; ogni voce è uno **snapshot
  immutabile** del push (non si riscrive, a differenza degli SSOT vivi).
- **Ancorato alla DoD dell'ACT** (`acts/README.md`, ciclo di vita — **step 6**) così non decade.
- **Solo GitHub/`documentation`**, mai GitLab (dev-facing).

**Conseguenze**:
+ Un puller si orienta in 30s dalla voce più recente; i push diventano leggibili senza aprire 4 doc.
+ Contributi paralleli senza conflitti; nessuna manutenzione manuale dell'indice.
+ Adozione a costo ~zero: i riassunti "cosa ho fatto / cosa è cambiato" di fine task **sono** la voce.
− Una voce in più per push — mitigato dallo **scaffold** e dal cap **8-12 righe**.
− Rischio **decadimento** (il primo passo manuale a saltare, [[ADR-0020]]) → agganciato alla **DoD ACT**.
− Non sostituisce le SSOT: se ci si mette del dettaglio, degrada in un doppione.

**Riferimenti**: [[ADR-0020]] (lessons: pattern one-file + INDEX generato) · `acts/README.md` (ciclo di
vita/DoD, step 6) · `DOCS/main/worklog/README.md` (convenzioni + template) · `CLAUDE.md` (aggancio sessioni
assistite: carica `worklog/INDEX` + `lessons/INDEX`).
