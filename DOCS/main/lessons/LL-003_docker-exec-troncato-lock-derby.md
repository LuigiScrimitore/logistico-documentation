---
id: LL-003
titolo: Un docker exec troncato lascia vivo il processo, che tiene il lock del metastore
sintomi:
  - "Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient"
  - "il rilancio di un notebook fallisce subito dopo un tentativo interrotto"
  - "Binary file (standard input) matches su un log di testo"
tag: [docker, spark, derby, metastore, ambiente-locale, logging]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_9015]
---

## Sintomo
Un job lanciato con `docker exec` viene interrotto lato host (timeout del tool, `Ctrl-C`, sessione chiusa). Il
rilancio fallisce immediatamente con:

```
AnalysisException: HiveException: java.lang.RuntimeException:
Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient
```

Nello stesso log compaiono righe con timestamp **successivi** all'errore, e `grep` classifica un file di testo
come binario.

## Strada sbagliata
Assumere che interrompere il comando sull'host abbia ucciso il processo nel container, e interpretare
l'errore del metastore come una corruzione da riparare. Nessuna delle due cose è vera.

## Regola
Prima di rilanciare, **verificare che non ci sia già un processo vivo**:

```bash
MSYS_NO_PATHCONV=1 docker exec logistico-spark ps -eo pid,etime,cmd | grep run_notebook
```

Se c'è e sta avanzando, lasciarlo finire: è lo stesso lavoro. Se va ucciso, `docker exec ... kill <pid>`.

I job lunghi vanno lanciati **in background dall'inizio**, non in foreground sperando che rientrino nel timeout.

E: **un file di log per tentativo.** Mai troncare o riusare il log di un run precedente.

## Perché
`docker exec` interrotto lato host chiude il canale di I/O ma **non propaga il segnale** al processo nel
container, che continua a girare orfano. Il metastore Derby locale è **single-writer**: finché il primo
processo tiene `_metastore_db/db.lck`, qualunque altra sessione Spark fallisce nell'istanziare il client. Non è
corruzione, è mutua esclusione che funziona correttamente.

Il "Binary file matches" ha la stessa radice: troncare un file su cui un altro processo scrive a un offset
elevato lascia un buco di byte NUL fra l'inizio e quell'offset. `grep` vede i NUL e passa in modalità binaria,
rendendo l'output illeggibile — con la conseguenza pratica di **perdere gli esiti di un run andato a buon
fine**.

Corollario utile: quando gli esiti hanno una sede autorevole (per il DQ è `config_dev_etl.dq_results`),
leggerli da lì invece che dal log. Il log è un artefatto di trasporto, non la fonte.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · il primo `dq_gate`, interrotto a 10 minuti, era ancora vivo (PID 11644, 12
  minuti di uptime) e ha completato regolarmente le 9 pipeline: 78/78 PASS letti da `dq_results`.
