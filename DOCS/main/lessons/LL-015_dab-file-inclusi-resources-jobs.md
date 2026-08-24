---
id: LL-015
titolo: I file inclusi da un Databricks Asset Bundle devono essere `resources:`, non un job "nudo"
sintomi:
  - "il job YAML ha name:/schedule:/tasks: a livello top-level (nessun resources:)"
  - "databricks bundle validate non vede il job / dopo il deploy il job non c'è"
  - "un file in include: non produce alcuna risorsa nel bundle"
tag: [databricks, dab, ci-cd, orchestrazione]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9018, ADR-0021]
---

## Sintomo
Un file YAML di job referenziato da `include:` nel `databricks.yml` ha il job **a livello top-level**
(`name:`, `schedule:`, `tasks:` …). Il bundle non lo raccoglie: `databricks bundle validate` non mostra il job
e dopo il deploy la risorsa non esiste.

## Strada sbagliata
Assumere che "un file YAML con `tasks:` sia un job deployabile". Un test custom sul formato (es. che i
`notebook_path` esistano) può passare lo stesso, dando falsa sicurezza: valida il *contenuto*, non che DAB lo
*riconosca* come risorsa.

## Regola
I file inclusi in un DAB devono usare le **chiavi di primo livello del bundle** (`resources`, `targets`,
`variables`, `bundle`, `artifacts`). Un job va sotto `resources: jobs:`:
```yaml
resources:
  jobs:
    logistica_carichi:        # chiave della risorsa
      name: logistica_carichi # display name
      tasks: [...]
```
Se hai job in formato "nudo", vanno **wrappati** in `resources: jobs: <key>:`. Adegua anche i test che leggono
il YAML (devono navigare `resources.jobs.<key>` invece del top-level).

## Perché
`databricks bundle validate` **non** segnala "questo file non è una config valida": semplicemente non produce
risorse — un fallimento silenzioso (stessa famiglia di [[LL-007]]/[[LL-010]]: ciò che nessun controllo copre è
indistinguibile dal corretto). Il presidio vero è provare `bundle validate` in CI, non solo i test di formato.

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · consolidamento DAB ([[ACT_9018]]/[[ADR-0021]]): i 7 `workflows/*.yml` erano
  in formato "job nudo"; wrappati in `resources: jobs:` e adeguato `tests/test_workflows_alignment.py` a
  leggere `resources.jobs.<key>` (30/30 verdi). Validazione DAB completa demandata alla CI cloud (DBR-05).
