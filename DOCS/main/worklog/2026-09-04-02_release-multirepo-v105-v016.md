---
data: 2026-09-04
titolo: "Release multi-repo: GitHub (4) + GitLab (lib v1.0.5, workflows v0.1.6) + doc pass (ADR-0026)"
autore: Francesco Foconi
push_monorepo: "(main @6420869 → doc pass su branch docs/release-7su7-multirepo)"
push_documentation: "GitHub logistico-documentation aggiornato"
push_gitlab: "lib v1.0.5, workflows v0.1.6 (CI verdi)"
act: [ACT_9026, ACT_9027, ACT_CND-01]
adr: [ADR-0026]
lesson: [LL-013, LL-025, LL-026, LL-027, LL-028]
op: [OP-TRA-1, OP-CND-1]
---

## Cosa e' stato fatto
Rilascio del giro 7/7 lungo tutta la catena **monorepo → GitHub → GitLab cliente**, poi doc pass complessivo.

### Pubblicazione
- **Monorepo**: PR #7 mergiato in `main` (`6420869`).
- **GitHub** (SoT, `split_to_multirepo.py --all`, commit "import da monorepo @6420869"):
  `logistico-lib` (main + tag `v1.0.5`), `logistico-workflows` (main + tag `v0.1.6`),
  `logistico-documentation` (main). `logistico-infrastructure` **invariato** (0 file diff) → non toccato.
- **GitLab cliente** (`promote_to_gitlab.py`, snapshot su clone, push **ff** — history preservata):
  `logistico-lib v1.0.5` + `logistico-workflows v0.1.6`; **CI cliente verdi** (wheel publish / bundle validate).
  Infra non ripubblicata.

### Doc pass
- **[[ADR-0026]]** (nuovo): canonico sito numerico unico + attributi alfabetici sul gold.
- **16_runbook_multirepo**: tabella "Stato pubblicazione" aggiornata (v1.0.5/v0.1.6, release 2026-09-04).
- **05_open_points**: **[[OP-CND-1]] chiuso** (CND rimosso) — [[OP-TRA-1]] gia' chiuso.
- **SAL_2026-09-04** (nuovo): delta esecutivo 7/7 + release + prossimi passi (backfill/quadratura).
- ACT/lesson gia' capitalizzati nel giro precedente (ACT_9026/9027, LL-025/026/027/028).

## Note operative (per il team)
- **Accessi**: GitHub push via `gh` (account `ffoconi`; `documentation` ha richiesto grant separato).
  GitLab: **solo HTTPS+PAT** (SSH bloccato — banner timeout su porta 22); host `cp1lgitlab.conaddeltirreno.it`,
  gruppo `cno/cno-data-platform/Logistico`.
- **Versioning** ([[LL-013]]): i tag GitLab (`v1.0.5`) sono **disallineati** dalla versione pacchetto wheel
  (resta `1.0.0`, caricata a runtime via `%pip` dal Volume). Da riconciliare quando si automatizza il publish.
- Le working copy `../logistico-repos` (GitHub) e `../logistico-repos-gitlab` sono state **rigenerate da zero**
  (non persistevano in locale).

## Stato dopo il push / prossimi passi
- Release completata; CI cliente verdi. Il **re-push del monorepo per il doc pass** (branch
  `docs/release-7su7-multirepo`) va **mergiato in main** (azione utente: il classifier blocca il merge a me),
  poi si **rigenera/ripubblica `logistico-documentation`** su GitHub.
- Prossimo lavoro tecnico: **backfill 7 giorni + run incrementale**, poi **quadratura** ([[OP-QDR-1]]).
