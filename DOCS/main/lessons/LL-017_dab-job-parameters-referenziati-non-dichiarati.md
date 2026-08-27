---
id: LL-017
titolo: I riferimenti `{{job.parameters.X}}` vanno dichiarati nel job — validate non lo verifica, jobs/create sì
sintomi:
  - "INVALID_PARAMETER_VALUE: refers to an undefined job parameter 'X'"
  - "bundle validate passa ma bundle deploy fallisce alla creazione dei job (400)"
  - "un task usa {{job.parameters.X}} ma il job non dichiara X in parameters"
tag: [databricks, dab, ci-cd, orchestrazione]
stadio: guardrail-automatico
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-27
origine: [ACT_9018]
---

## Sintomo
`databricks bundle validate` è verde, ma `bundle deploy` fallisce alla creazione del job:
`Reference 'job.parameters.siti' in task '…' refers to an undefined job parameter 'siti' (400 INVALID_PARAMETER_VALUE)`.

## Strada sbagliata
Fidarsi del `validate` verde come prova che il bundle sia deployabile. `validate` **non** controlla che i
`{{job.parameters.X}}` usati dai task siano dichiarati nei `parameters` del job: quel controllo lo fa solo
l'API `jobs/create`, cioè in fase di **deploy** (spesso solo in cloud).

## Regola
Ogni `{{job.parameters.X}}` referenziato da un task **deve** essere dichiarato nel blocco `parameters:` del
job:
```yaml
resources:
  jobs:
    logistica_giacenze:
      parameters:
        - name: siti          # dichiarato...
          default: "..."
      tasks:
        - task_key: bronze_catena
          notebook_task:
            base_parameters: { siti: "{{job.parameters.siti}}" }   # ...poi usato
```
Presidiato in locale da `tests/test_workflows_alignment.py::test_job_parameters_referenziati_sono_dichiarati`
(un test per workflow): converte un fallimento cloud-only in un test locale.

## Perché
È la stessa famiglia di [[LL-015]]: `bundle validate` è **permissivo** e non equivale al deploy reale. I
controlli forti stanno sull'API (`jobs/create`). La difesa è un guardrail locale che imita il vincolo dell'API,
così l'errore emerge prima del cloud — coerente con [[LL-007]] (presidiare col test, non con la convenzione).

## Conferme e contraddizioni
- 2026-08-27 · luigi.scrimitore · deploy_dev di `logistico-workflows`: `validate` verde, ma `jobs/create`
  ha rifiutato 6 job su 7 (siti/file_format/landing_base_path/retail_master_schema non dichiarati). Aggiunti i
  parametri mancanti + guardrail → 37/37 verdi.
