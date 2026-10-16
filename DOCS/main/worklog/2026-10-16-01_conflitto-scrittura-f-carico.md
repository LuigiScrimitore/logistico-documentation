---
data: 2026-10-16
titolo: "F_CARICO: gold_late_arriving_handler e gold_f_carico scrivevano in parallelo (ConcurrentAppendException) — ordine nel DAG + guardrail scrittura-scrittura"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "split dopo merge"
push_gitlab: "workflows: rilascio solo main, nessun tag (LL-031)"
act: [ACT_9014]
adr: [ADR-0019]
lesson: [LL-038]
op: []
---

## Contesto
Durante il recupero di ottobre (worklog 2026-10-15-03) ogni run di `logistica_carichi` ha avuto
`gold_late_arriving_handler` in errore al primo tentativo:
`ConcurrentAppendException [DELTA_CONCURRENT_APPEND.WITH_PARTITION_HINT] ... gold_dev.logistica.F_CARICO`, riuscito al
secondo (retry). Esempio: run 480919269590604, `gold_f_carico` e `gold_late_arriving_handler` entrambi 15:07:27→15:07:59,
retry del secondo 15:08:00→15:08:28.

## Diagnosi
Entrambi dipendono solo da `silver_prep_carico` e scrivono `F_CARICO`: `gold_f_carico` in `partitionOverwriteMode=dynamic`,
`gold_late_arriving_handler` con `replaceWhere ANNO_MESE` sulle partizioni dei mesi passati. Partono insieme e Delta
rifiuta il secondo commit. Oggi il retry salva il risultato, ma: un tentativo sprecato a ogni run, rischio di fallimento se i
tentativi finiscono, e l'ordine delle due scritture non è garantito.
Il guardrail di [[LL-038]] controllava solo "leggo una tabella scritta da un altro task", non "due task scrivono la stessa
tabella".

## Decisioni
1. `gold_late_arriving_handler` dipende da `gold_f_carico` (scrive dopo, sulle partizioni passate).
2. Guardrail in `tests/test_workflows_alignment.py`: due task dello stesso job che scrivono la stessa tabella devono essere
   ordinati (uno antenato dell'altro). [[LL-038]] esteso al caso scrittura-scrittura.

## Esito
- PR [#38](https://github.com/LuigiScrimitore/Logistico2.0/pull/38) mergiata (`9e894fa`); `pytest
  tests/test_workflows_alignment.py` 58 passed (senza la correzione il nuovo test fallisce solo su `logistica_carichi`).
- `workflows` **v0.1.15** su GitLab (solo main, `8b51ff7`), deploy CI verificato; sul job della MI
  `gold_late_arriving_handler` depends_on = `silver_prep_carico`, `gold_f_carico`.
- Run di prova 986357837999257 (`run_date` 2026-10-16): SUCCESS, **nessun retry**: `gold_f_carico` 09:50:20→09:50:49,
  poi `gold_late_arriving_handler` 09:50:49→09:51:18 (primo tentativo), `dq_gate` 09:51:18→09:51:46.
