---
data: 2026-09-02
titolo: "Capitalizzazione: LL-022/023/024 + ACT_9019/9021/9022 (doc-sync dei fix mergiati)"
autore: Francesco Foconi
push_monorepo: 2d28898
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9019, ACT_9020, ACT_9021, ACT_9022]
adr: []
lesson: [LL-022, LL-023, LL-024]
op: [OP-08]
---

## Cosa e' stato fatto
- **Doc-sync** dei fix mergiati oggi (PR #1/#2/#3, voce 2026-09-02-03): mancavano ACT dedicati e lessons.
- Nuovi **ACT record**: [[ACT_9021]] (fix JDN `silver_pesate`, PR #2), [[ACT_9022]] (DAB dev root_path in home,
  PR #1). [[ACT_9020]] già presente (extractor `--ignore-odi-flag`); aggiornata la sua sezione Lezioni.
- **ACT_9019** (quadrature offline agosto) committato come record (era orfano, mai versionato) + riga backlog.

## Novita'
- Nuove **lessons**: [[LL-022]] date Logistix = JDN (mai `.cast("date")`, usa `julian_to_date`; automatizzabile →
  check DQ anno fuori range), [[LL-023]] DAB mode:development → root_path in home per le sandbox, [[LL-024]] il
  filtro CDC ODI non è adatto al seed storico (opt-in, non cablato nel config).
- **OP-08**: annotato il workaround seed storico (`--ignore-odi-flag`).
- Il modello **dev/qa/prod** resta da formalizzare in un ADR dedicato (team) — [[LL-023]]/[[ACT_9022]] lo anticipano.

## Doc aggiornati
- `lessons/LL-022|LL-023|LL-024.md` + `lessons/INDEX.md`; `acts/ACT_9019|9021|9022.md` + `acts/ACT_9020.md`;
  `15_backlog_master.md`; `05_open_points.md`.

## Stato dopo il push / prossimi passi
- Documentazione allineata allo standard (ACT + LESSON + backlog + open_points + worklog) per il lavoro di oggi.
- **Prossimo**: `ACT_CND-01` (repoint bronze `cnd`) per giacenze/trasporti; cleanup 93 righe pesata pre-fix
  (full_refresh); il team formalizza l'ADR dev/qa/prod.
