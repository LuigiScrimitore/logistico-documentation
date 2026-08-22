---
id: LL-002
titolo: VACUUM del warehouse per-database e con output unbuffered
sintomi:
  - "il vacuum gira da 20+ minuti senza variazione dello spazio libero"
  - "nel log si vedono solo messaggi JVM di Delta, nessun avanzamento Python"
  - "il processo sembra bloccato ma non lo è"
tag: [delta, vacuum, spark, ambiente-locale, docker]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_MNT-01, ACT_9005]
---

## Sintomo
`vacuum_warehouse.py` lanciato su tutto il warehouse con output rediretto su file: dopo 20+ minuti nessuna
variazione dello spazio libero e nel log solo messaggi JVM. Sembra un processo impiantato.

## Strada sbagliata
Concludere che sia bloccato e ucciderlo. Non lo era: stava lavorando, ma su tabelle sbagliate e senza darne
conto.

Due cause sovrapposte:

1. **Ordine alfabetico.** `find_delta_tables` restituisce le tabelle ordinate, quindi processa prima ~69 tabelle
   bronze **senza tombstone** e arriva alle gold — dove sta lo spazio — dopo decine di minuti. Su 94 tabelle
   totali solo 25 erano state rigenerate e avevano qualcosa da liberare.
2. **Buffering.** Le `print()` Python sono bufferate quando l'output è rediretto su file: si vedono solo i
   messaggi della JVM, che scrive su un altro stream. L'avanzamento reale è invisibile.

## Regola
Un'invocazione **per database**, limitata a quelli effettivamente rigenerati, con `PYTHONUNBUFFERED=1`:

```bash
for db in gold_dev_logistica.db gold_dev_logistica_dm.db silver_dev_logistica_curated.db; do
  MSYS_NO_PATHCONV=1 docker exec -e PYTHONUNBUFFERED=1 logistico-spark \
    python -u /workspace/code/tests/local_bronze/vacuum_warehouse.py \
    --warehouse "/workspace/data/warehouse/$db"
done
```

Minuti invece di ore, con avanzamento visibile tabella per tabella. `python -u` e `PYTHONUNBUFFERED=1` sono
ridondanti fra loro: metterne almeno uno.

## Perché
Su bind mount Windows lo `stat` di ogni file passa dal layer di traduzione POSIX e paga un pedaggio enorme: il
listing di una tabella con centinaia di parquet può richiedere 30–90 s. Scandire tabelle che non hanno
tombstone è quindi costoso **e** inutile. Restringere il perimetro non è un'ottimizzazione marginale, cambia
l'ordine di grandezza.

Lo stesso pedaggio spiega perché `du` di MSYS si impianta su directory con molti file piccoli: per misurare le
dimensioni su Windows conviene l'enumerazione nativa .NET, non gli strumenti POSIX.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · confermata: VACUUM su 3 database mirati completato in pochi minuti, mentre il
  run precedente su tutto il warehouse era ancora sulle bronze dopo mezz'ora.
