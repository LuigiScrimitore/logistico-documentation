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
- `scripts/sftp/send_to_landing.py`: trasporto pluggable `--transport azcopy|sftp` (riusa `build_upload_plan`).
- Backend AzCopy: `azcopy copy --overwrite=ifSourceNewer`, auth SAS/AAD(MSI/SPN) da env, **dry-run** con SAS mascherato (nessun tool/credenziale richiesti).
- ACT_9012 → follow-up #1 ✅; `send_to_sftp.py` resta come backend legacy.

## Novità
- Nessun ADR/OP nuovo. Bug corretto: output reso **ASCII-safe** (crash del carattere `->` su console cp1252).

## Doc aggiornati
ACT_9012 (follow-up), 14_release_kit (KIT-01). Nuovo test `tests/test_send_to_landing.py` (15 pass).

## Stato dopo il push / prossimi passi
Backend pronto e validato in **dry-run**. Blocco: la validazione reale (`--send`) attende il **container** (§F.2).
