---
id: LL-004
titolo: Il dynamic partition overwrite non tocca le partizioni che il flusso non produce più
sintomi:
  - "una misura aggregata è inspiegabilmente gonfiata rispetto alla sorgente"
  - "partizione con colonna di partizione NULL e DWH_UPDATED_AT vecchio"
  - "nessun duplicato sulla chiave ma i totali non tornano"
tag: [delta, partizionamento, idempotenza, gold, dati]
stadio: lezione
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_9005, ACT_9015]
---

## Sintomo
`F_PREP_SPED` conteneva **6.712.256 righe** con `DATA_PREL = NULL` e `DWH_UPDATED_AT = 2026-07-02`, residuo di
un run precedente a un fix. Effetto: `SUM(QTA_PREP)` = 231.729.072 invece di 120.846.960, un **+92% di
inflazione silenziosa**. Nessun duplicato sulla chiave, `max_righe_per_chiave = 1`: tutti i controlli di grain
passavano.

## Strada sbagliata
Cercare un bug di idempotenza nella scrittura. Non c'era: il write era corretto. E prima ancora, usare
`COUNT(DISTINCT col_a, col_b, ...)` per contare le chiavi — **`COUNT(DISTINCT` ignora le righe con NULL**, il
che maschera esattamente il caso da diagnosticare e produce falsi allarmi di duplicati. Per contare chiavi con
NULL usare `GROUP BY`.

## Regola
Dopo un fix che cambia la logica di partizionamento o la derivazione della colonna di partizione, **verificare
esplicitamente le partizioni orfane**:

```sql
SELECT <part_col>, COUNT(*), MAX(DWH_UPDATED_AT)
FROM <fact> GROUP BY <part_col> ORDER BY 1;
```

Leggere le colonne di partizione da `DESCRIBE TABLE`, non assumerle. Due segnali: valori NULL nella colonna di
partizione, e `DWH_UPDATED_AT` molto più vecchio dell'ultimo run.

**Debito di automazione**: serve un check DQ che rilevi partizioni con timestamp di scrittura anomalo rispetto
alla mediana della tabella. Finché non c'è, la verifica è manuale e quindi salterà.

## Perché
`spark.sql.sources.partitionOverwriteMode = dynamic` riscrive **solo le partizioni presenti nel dataframe in
input**. Se il flusso, dopo il fix, non produce più righe con quel valore di partizione, quella partizione non
viene né riscritta né cancellata: **resta lì per sempre**, invisibile a ogni controllo di duplicati perché è
internamente coerente.

È il tipo di difetto peggiore: non rompe niente, non fa fallire nulla, cambia solo i numeri. È stato trovato per
caso durante una verifica su altro.

Nota di perimetro: la diagnostica successiva su tutti gli 8 fact e 6 aggregati ha trovato **zero** altre
partizioni NULL — il caso era isolato. Ma la classe di problema resta aperta per ogni fix futuro sul
partizionamento.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · variante trovata su `F_MOVIMENTAZIONE_CARRELLISTI`: partizioni non NULL ma
  **incomplete**, scritte da logica pre-fix (mancavano 2 date intere; il 17/06 aveva 179 righe invece di 193).
  Il segnale utile lì non era il NULL ma lo **spread di `DWH_UPDATED_AT`**: 15 giorni di scrittura distinti su
  una tabella che il codice attuale genera in un colpo solo.
