---
id: LL-038
titolo: "Un task incrementale senza depends_on sui suoi input va verde ogni giorno senza caricare niente"
sintomi:
  - "una tabella Gold resta ferma a una data vecchia ma il job finisce sempre in SUCCESS"
  - "lo strato silver/curated ha un solo _silver_load_date anche se le sorgenti crescono ogni giorno"
  - "il log del notebook incrementale riporta 0 chiavi impattate"
  - "un task parte allo stesso secondo dei bronze pur leggendo tabelle silver dello stesso job"
  - "una dipendenza dichiarata nello YAML del job non compare nel DAG del job deployato"
tag: [databricks, dab, workflow, dag, incrementale, dq]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-10-15
origine: [prep-sped-vuota]
---

## Sintomo
`F_PREP_SPED` ferma ai dati del 02/09 per sei settimane, con il job `logistica_prep_sped` verde tutti i giorni.
`silver_prep_prep_sped` (incrementale: prende le chiavi con `_silver_load_date = run_date`) non aveva `depends_on` e
partiva insieme ai bronze, prima che `storico_liste_uniche` / `storico_bolle_uniche` del giorno fossero scritte: 0 chiavi,
MERGE vuoto, SUCCESS. Il giorno dopo filtrava solo la nuova data, quindi il carico precedente non veniva mai ripreso.

## Strada sbagliata
- Fidarsi dello stato del run: SUCCESS dice solo che il notebook non ha sollevato eccezioni.
- Fidarsi di `bundle validate`: non conosce le tabelle lette dai notebook, e con una chiave YAML duplicata (es. due
  `depends_on` nello stesso task) tiene l'ultima senza avvisare.

## Regola
- In un job, **ogni task che legge una tabella scritta da un altro task dello stesso job deve averlo tra gli antenati**
  (`depends_on` diretto o indiretto). Vale doppio per i notebook incrementali per `run_date`: se partono prima, perdono il
  giorno per sempre.
- Niente chiavi duplicate negli YAML dei job.
- Entrambe le regole sono verificate da `tests/test_workflows_alignment.py` (tabelle lette/scritte ricavate dalle costanti
  `TARGET_TABLE` / `FULL_TARGET` / `SRC_*` dei notebook).
- Per ripartire dopo un buco: run del job con `full_refresh=true` sul notebook incrementale.

## Perché
Il DAG era stato rigenerato dal codice ([[ACT_9014]]) e il riconoscimento degli input di quel notebook era fallito. Un
task senza dipendenze, in Databricks Jobs, parte subito: nessun errore, solo dati mancanti.

## Conferme e contraddizioni
- 2026-10-15 · run del 15/10: `silver_prep_prep_sped` 08:15:00→08:16:41, `storico_liste_uniche` 08:18:25→08:23:32;
  `logistica_curated.prep_sped` con un solo `_silver_load_date` (2026-09-02). Stesso controllo su tutti i job: un
  `depends_on` duplicato in `gold_a_stock_mensile` (datamart). Worklog 2026-10-15-02.
