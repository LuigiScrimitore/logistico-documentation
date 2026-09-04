---
id: LL-026
titolo: full_refresh deve fare OVERWRITE, non MERGE — se cambia la derivazione di una chiave restano righe stale duplicate
sintomi:
  - "dopo un full_refresh la tabella ha righe duplicate: stessa entità con la vecchia e la nuova chiave"
  - "stessi conteggi su due valori diversi della colonna chiave (es. SITO_COD '18'=559 e 'LCAX'=559)"
  - "un remap di una colonna-chiave non elimina gli orphan nonostante il full_refresh"
tag: [silver, delta, merge, full-refresh, idempotenza, sito]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-03
origine: [ACT_9026]
---

## Sintomo
Ri-processo un silver in `full_refresh=true` per applicare un nuovo mapping su una colonna che fa parte della
**chiave di merge** (es. `SITO_COD` rimappato da `LGAX` a `20`). Dopo il run la tabella contiene sia le righe
**vecchie** (chiave `LGAX`) sia le **nuove** (chiave `20`): stessi conteggi, righe duplicate, orphan non risolti.

## Strada sbagliata
Trattare `full_refresh` come "rileggi tutto il sorgente" ma tenere il **write in MERGE** anche in quel ramo:
```python
if not spark.catalog.tableExists(TARGET):     # <-- solo prima esecuzione fa overwrite
    df.write.mode("overwrite")...
else:
    DeltaTable...merge("tgt.SITO_COD = src.SITO_COD AND ...").whenMatchedUpdateAll().whenNotMatchedInsertAll()
```
Se la derivazione di `SITO_COD` cambia, le vecchie righe hanno una chiave che il `src` non contiene più →
`whenMatched` non scatta, `whenNotMatched` **inserisce** le nuove → le vecchie sopravvivono. `full_refresh` non
pulisce nulla.

## Regola
`full_refresh` (e la prima esecuzione) devono **OVERWRITE**, mai merge:
```python
if full_refresh or not spark.catalog.tableExists(TARGET):
    df.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable(TARGET)
else:
    DeltaTable...merge(...)   # solo l'incrementale usa il merge
```
Il merge è corretto **solo** per l'incrementale (chiave stabile). Nota: un merge su chiave **stabile** (es.
`SP_ID` in `spedizioni_clean`) aggiorna in-place anche con full_refresh e non duplica — ma la semantica corretta
di "clean slate" resta l'overwrite (rimuove anche righe la cui chiave è sparita dal sorgente).

## Perché
`full_refresh` significa "ricostruisci lo stato da zero": l'unica scrittura idempotente rispetto a un cambio di
derivazione di chiave è la sostituzione completa. Il merge presume che le chiavi target siano un sottoinsieme
stabile del sorgente — assunzione falsa quando è proprio la chiave a cambiare. Vedi [[LL-025]] (il remap sito che
ha reso visibile il bug).

## Conferme e contraddizioni
- 2026-09-03 · Francesco Foconi · `silver_ordini` DEV: full_refresh in MERGE → `ordine` con righe doppie
  (`18`/`LCAX`, `20`/`LGAX`, stessi conteggi). Con overwrite → orphan 0, nessun duplicato. Fix esteso a
  `silver_ordini`, `silver_trasporti` (aggiunto widget full_refresh), `silver_spedizioni_clean`.
