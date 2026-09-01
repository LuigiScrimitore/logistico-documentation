---
data: 2026-09-01
titolo: Hook pre-push per gli INDEX generati (worklog, lessons)
autore: luigi.scrimitore
push_monorepo: 6ba1223
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0024]
lesson: []
op: []
---

## Cosa è stato fatto
- `.githooks/pre-push` (versionato): blocca il push se `worklog/INDEX.md` o `lessons/INDEX.md` sono stale (via `--check`). Setup una tantum per clone: `git config core.hooksPath .githooks`.
- Detection python robusta: **esegue** i candidati (su Windows lo stub "App execution alias" risponde a `command -v` ma non è Python vero). `.gitattributes` forza **LF** sugli hook.

## Novità
- L'hook ha **subito trovato** `lessons/INDEX.md` stale (18 → 19, LL-019 non rigenerato) → corretto.

## Doc aggiornati
worklog/README, CLAUDE.md. Nuovi: `.githooks/pre-push`, `.gitattributes`; rigenerato `lessons/INDEX.md`.

## Stato dopo il push / prossimi passi
Guardrail attivo. Da ora il push si blocca se un INDEX generato è stale (rigenera e ricommitta).
