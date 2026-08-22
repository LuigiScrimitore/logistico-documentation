---
id: LL-011
titolo: Pipeline "stuck" con un runner attivo presente → è il tag, non il runner
sintomi:
  - "la pipeline resta Pending con l'etichetta 'stuck'"
  - "Settings > CI/CD > Runners mostra un runner attivo (pallino verde) ma i job non partono"
  - "il runner ha un tag (es. azure-runner) e i job del .gitlab-ci.yml non ne hanno"
tag: [gitlab, ci-cd, runner, ambiente-cliente]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9017]
---

## Sintomo
Push su GitLab, pipeline creata ma **Pending/`stuck`**, e i job non partono mai. In
`Settings → CI/CD → Runners` risulta però un runner **attivo** (verde) assegnato al progetto/gruppo.

## Strada sbagliata
Concludere "manca il runner" e chiedere al team piattaforma di registrarne uno. Il runner c'è: il tempo si
perde a cercare un problema di infrastruttura che non esiste.

## Regola
Se un runner attivo è presente ma la pipeline è `stuck`, **guarda il _tag_ del runner**. In GitLab un runner
**taggato** esegue **solo** i job che portano lo stesso tag; i job senza tag non gli matchano. Allinea i job:
```yaml
default:
  tags: [azure-runner]   # lo stesso tag del runner (vedi card del runner in Settings > CI/CD > Runners)
```
In alternativa (se hai i permessi sul runner) abilitare "Run untagged jobs", ma taggare i job è più esplicito e
non dipende dalla config del runner.

## Perché
Il tag del runner è un **filtro di instradamento**, non un'etichetta decorativa: serve a mandare i job solo ai
runner attrezzati per eseguirli. "stuck" significa proprio "nessun runner _idoneo_ (per tag) disponibile", che
è diverso da "nessun runner". Su GitLab aziendali i runner sono quasi sempre taggati (es. per pool/VM): i job
vanno taggati di conseguenza.

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · pilot `logistico-lib`: 2 pipeline `stuck` con group runner #263
  `azure-runner` attivo. Aggiunto `tags: [azure-runner]` nel `default:` → i job sono partiti subito.
