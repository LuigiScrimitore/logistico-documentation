---
id: LL-010
titolo: Uno split/proiezione parte dai file tracciati e segnala i non mappati — mai drop silenziosi
sintomi:
  - "un file del monorepo non compare in nessun repo derivato dopo lo split"
  - "un .env o un dato reale è finito in un repo condiviso/consegnato"
  - "lo split copre solo alcune cartelle e il resto sparisce senza avviso"
  - "la copia manuale dei repo si porta dietro __pycache__/artefatti di build"
tag: [git, multi-repo, migrazione, tooling, sicurezza]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9017, ADR-0016]
---

## Sintomo
Si spezza un monorepo in più repo (o si copiano cartelle "a mano"). Poi: un file non si ritrova da nessuna
parte, oppure — peggio — un `.env`/dato reale finisce in un repo condiviso, o la copia trascina
`__pycache__`/`dist/`. Il difetto è invisibile finché qualcuno non lo cerca.

## Strada sbagliata
Proiettare i repo **copiando cartelle** (`cp -r`, robocopy) o iterando sul filesystem. Si porta dietro tutto
ciò che è su disco (segreti esclusi dal `.gitignore` ma **presenti** localmente, artefatti, junk) e, se la
mappatura è per-cartella, i file che non rientrano in nessuna regola **spariscono in silenzio**.

## Regola
**Iterare sui file _tracciati_ (`git ls-files`), instradare tutto, segnalare i non mappati.**
- `git ls-files` come sorgente ⇒ `.env`, `warehouse/`, dati reali e `__pycache__` sono esclusi *gratis* perché
  già nel `.gitignore`. Non serve una blacklist da mantenere.
- Ogni file tracciato deve avere una destinazione; i **non mappati vengono elencati** (errore/warning), mai
  ignorati. "Zero non mappati" è la prova che la copertura è completa.
- La proiezione **svuota** l'albero di destinazione prima di ripopolarlo, così le rimozioni si propagano (lo
  stato riflette la sorgente, non si accumulano file fantasma).
Realizzata in `scripts/split_to_multirepo.py` (dry-run che stampa i conteggi e i non mappati).

## Perché
Il `.gitignore` è già la lista, curata e versionata, di "cosa non deve stare nel repo": riusarla via
`git ls-files` invece di reinventare un filtro elimina un'intera classe di errori (segreti/dati che sfuggono).
E il **fail-loud sui non mappati** trasforma un difetto invisibile ("dov'è finito quel file?") in un avviso
esplicito al momento dello split — stesso spirito di [[LL-005]]: un problema che nessun controllo copre è
indistinguibile da "tutto ok".

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · dry-run split @96b115e: 584 file instradati, **0 non mappati** su 4 repo;
  la verifica "0 non mappati" ha dato la certezza che nessun file del monorepo restasse orfano.
