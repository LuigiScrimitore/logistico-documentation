---
id: LL-008
titolo: Sui CSV di landing lo schema si applica per nome, mai per posizione
sintomi:
  - "colonne bronze popolate con i valori di un'altra colonna"
  - "valori numerici finiti in una colonna di testo (o viceversa) senza errore"
  - "conteggi corretti ma contenuti spostati di una posizione"
tag: [bronze, csv, landing, schema, dati]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-21
origine: [memoria di progetto bronze-csv-schema-by-name]
---

## Sintomo
Tabella bronze che si carica **senza errori** ma con i contenuti sfasati: valori nella colonna sbagliata,
conversioni assurde, conteggi corretti. Il difetto non fa rumore.

## Strada sbagliata
Applicare `.schema(...)` a un CSV assumendo che l'ordine delle colonne nel file coincida con quello dello schema
dichiarato. Spark **non verifica**: associa per posizione e va avanti. Se la sorgente cambia l'ordine delle
colonne — o ne aggiunge una in mezzo — l'intera tabella si sposta silenziosamente.

## Regola
1. Leggere il CSV **per header** (`header=True`, `inferSchema` o cast espliciti *dopo* la lettura), mai con uno
   schema posizionale.
2. Applicare i tipi selezionando le colonne **per nome**.
3. `MERGE` null-safe sulla chiave e dedup sulla chiave naturale prima della scrittura.

**Debito di automazione**: un check che confronti l'header effettivo del file con l'elenco di colonne atteso e
fallisca sulla differenza. È il controllo che trasformerebbe questa lezione in guardrail — oggi la protezione
dipende da chi scrive il notebook.

## Perché
`.schema()` su un `read.csv` è un'istruzione posizionale: dice a Spark *"i campi sono in questo ordine"*, non
*"cerca questi nomi"*. È l'errore più insidioso della fase Bronze perché non produce eccezioni — solo dati
plausibili e sbagliati, che si scoprono a valle in Gold quando i numeri non tornano (vedi
[LL-005](LL-005_delta-costante-accusa-colonna.md): un contenuto spostato produce delta variabili, non costanti,
quindi si confonde col rumore da copertura).

## Conferme e contraddizioni
- (nessuna ancora — regola derivata da un caso già risolto in fase Bronze, migrata qui dalle memorie personali
  perché è conoscenza condivisa, non individuale)
