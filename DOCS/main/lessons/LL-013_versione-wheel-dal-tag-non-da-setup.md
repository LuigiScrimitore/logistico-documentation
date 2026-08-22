---
id: LL-013
titolo: La versione del pacchetto viene da setup.py, non dal tag git — vanno sincronizzati
sintomi:
  - "nel Package Registry il pacchetto ha una versione diversa dal tag che l'ha pubblicato"
  - "la pipeline gira sul tag v1.0.2 ma il wheel pubblicato è 1.0.0"
  - "la seconda release fallisce il publish per versione duplicata (409)"
  - "il build fallisce con 'unexpected EOF while looking for matching quote' nel sed della versione"
tag: [ci-cd, packaging, python, wheel, release]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9017]
---

## Sintomo
Il tag di release fa partire la pipeline (es. `v1.0.2`), il `publish` va a buon fine, ma nel Package Registry
il pacchetto compare con una versione **diversa** (es. `1.0.0`). Alla release successiva il `publish`
fallisce/duplica perché ricostruisce sempre lo stesso numero.

## Strada sbagliata
Assumere che "taggo `v1.0.2` → il pacchetto è 1.0.2". Il tag git e la versione del pacchetto sono **due cose
diverse**: `python -m build` legge la versione da `setup.py`/`pyproject.toml`, e se lì è hardcoded resta quella
a ogni build, qualunque sia il tag.

## Regola
**La versione del pacchetto deve derivare dal tag di release.** Nel build in CI, su tag, allinea la versione:
```yaml
# NB quoting: il pattern sed contiene doppie apici (version="..."), quindi le parti letterali
# vanno in APICI SINGOLE e solo $V in doppie — 's/.../'"$V"'/' — altrimenti la shell dà
# "unexpected EOF while looking for matching quote".
- if [ -n "$CI_COMMIT_TAG" ]; then V="${CI_COMMIT_TAG#v}"; sed -i 's/version="[^"]*"/version="'"$V"'"/' setup.py; fi
- python -m build --wheel
```
(In alternativa `setuptools_scm`, che deriva la versione dal tag git automaticamente ed evita del tutto il
problema del quoting.) La versione in `setup.py` resta come default per i build locali; in CI vince il tag.

## Perché
Un artefatto pubblicato è **immutabile e identificato dalla versione**: se la versione non segue il rilascio,
due release diverse collidono (stesso numero) e i consumatori non possono pinnare in modo affidabile. Legare la
versione al tag rende il tag l'unica fonte di verità del rilascio — coerente con "release per snapshot taggato"
di [[LL-009]].

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · pilot `logistico-lib`: tag `v1.0.2` ma wheel pubblicato `1.0.0` (versione
  hardcoded in `setup.py`). Il giro CI era corretto; mancava solo l'allineamento versione↔tag.
- 2026-08-22 · luigi.scrimitore · primo fix col `sed` in doppie apici → build KO (`unexpected EOF`); risolto
  col quoting apici-singole `'...'"$V"'...'`. Con `v1.0.4` il registry ha pubblicato **`1.0.4`** (versione = tag).
