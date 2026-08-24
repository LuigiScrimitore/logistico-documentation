---
id: LL-014
titolo: Immagine CI con ENTRYPOINT non-shell (terraform, kaniko…) → resettare entrypoint in GitLab
sintomi:
  - "Terraform has no command named \"sh\". Did you mean \"push\"?"
  - "il job GitLab non esegue lo script: parte l'entrypoint dell'immagine"
  - "errori tipo '<tool> has no command named sh/-c' all'avvio del job"
tag: [gitlab, ci-cd, docker, terraform]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_0.1.6, ACT_9017]
---

## Sintomo
Un job GitLab con `image: hashicorp/terraform` (o simili) fallisce subito con
`Terraform has no command named "sh"`. Lo `script:` non viene eseguito.

## Strada sbagliata
Pensare che sia un errore di sintassi nello script o un comando terraform sbagliato. Non lo è: lo script non
parte proprio.

## Regola
GitLab lancia lo `script:` **dentro una shell** (`sh -c "…"`). Se l'immagine ha un **ENTRYPOINT non-shell**
(quella terraform ha `ENTRYPOINT ["terraform"]`), GitLab finisce per eseguire `terraform sh -c "…"` → errore.
**Resettare l'entrypoint** nel job:
```yaml
image:
  name: hashicorp/terraform:latest
  entrypoint: [""]
```
Vale per ogni immagine con entrypoint applicativo (terraform, kaniko, alcuni tool CLI). Le immagini "shell-friendly"
(es. `python`, `alpine`) non ne hanno bisogno.

## Perché
`entrypoint: [""]` azzera l'ENTRYPOINT dell'immagine così il container parte con una shell, e i comandi dello
`script:` (incluso `terraform ...`) vengono eseguiti come comandi normali. È la stessa classe di [[LL-011]]/[[LL-012]]:
l'ambiente del runner (entrypoint, tag, CA) va reso esplicito nel `.gitlab-ci.yml`, non dato per scontato.

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · pipeline `logistico-infrastructure`: `validate`/`plan` fallivano con
  "no command named sh"; aggiunto `entrypoint: [""]` nel `default.image` → i job partono. Fix nel generatore
  `split_to_multirepo.py` (vale per tutti i repo).
