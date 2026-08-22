---
id: LL-007
titolo: Un DAG mantenuto a mano divergerà dal codice — derivarlo e presidiarlo con un test
sintomi:
  - "notebook_path in un workflow punta a un notebook inesistente"
  - "notebook presenti nel repo ma non orchestrati da alcun job"
  - "il DAG del workflow non riflette le dipendenze reali di lettura/scrittura"
tag: [orchestrazione, workflow, databricks, guardrail, manutenibilita]
stadio: guardrail-automatico
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_9014, ADR-0019]
---

## Sintomo
Audit dei 7 workflow YML: **6 `notebook_path` puntavano a notebook inesistenti** e **52 notebook su 104 non
erano orchestrati da nessun job**. Un workflow aveva `tasks: []`, che l'API Jobs rifiuta — quindi non era mai
stato validato.

## Strada sbagliata
Correggere i singoli riferimenti rotti. È una toppa: il DAG scritto a mano divergerà di nuovo al prossimo
notebook aggiunto o rinominato, e la divergenza è invisibile finché non si tenta un deploy.

## Regola
**Il DAG si deriva dal codice, il YML resta l'artefatto.** Le dipendenze si ricavano dal grafo reale di
letture/scritture dei notebook, non dalla memoria di chi scrive il YML.

E il presidio è un test, non una convenzione: `tests/test_workflows_alignment.py` — 30 test che verificano che i
path esistano, che le dipendenze siano valide, che non ci siano cicli né orfani inattesi, che il compute sia
serverless e che i `base_parameters` corrispondano ai widget dei notebook.

## Perché
Questa lezione è il **precedente della scala di maturità** di [ADR-0020](../adr/0020_lezioni_operative.md): non
è rimasta una raccomandazione da ricordare, è diventata un controllo che gira da sé. Nessuno deve sapere che
esiste per esserne protetto — ed è la differenza fra conoscenza documentata e conoscenza applicata.

La stessa logica ("genera, non mantenere") è applicata a `lessons/INDEX.md`, rigenerato dal frontmatter invece
che scritto a mano.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · il guardrail ha già pagato: la diagnostica di ACT_9015 ha trovato l'unico
  `full_refresh` del repo dentro un worktree abbandonato, e ha potuto escluderlo dal perimetro con certezza
  perché il codice vivo è quello presidiato dai test.
