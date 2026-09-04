---
id: LL-022
titolo: Le date Logistix sono Julian Day Number — mai .cast("date") diretto, usa julian_to_date
sintomi:
  - "ValueError: year 2461373 is out of range"
  - "gold_late_arriving_handler crasha alla deserializzazione di una DateType"
  - "una colonna data ha anno assurdo (~8710 col cast diretto, o = valore JDN)"
  - "MAX(DATA_*) restituisce una data tipo +2461321-01-01"
tag: [silver, date, julian, logistix, gold, dati]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-09-02
origine: [ACT_9021]
---

## Sintomo
Un `.cast("date")` su una colonna data Logistix produce date con anno assurdo. A valle,
`gold_late_arriving_handler` (o qualunque step che deserializza la `DateType` in Python) esplode con
`ValueError: year 2461373 is out of range`. Oppure un `MAX(DATA_SCADENZA)` in silver restituisce
`+2461321-01-01`.

## Strada sbagliata
Trattare la colonna come una data/epoch normale: `F.col("DATA_X").cast("date")`. Sembra giusto perché il
Bronze è tutto stringa e il cast "converte". Ma nei sorgenti Logistix le date sono **Julian Day Number**
(numero di giorni dall'inizio dell'era giuliana, es. `2461373`). Il cast le interpreta come giorni dal
1970-01-01 → anni a 4-5 cifre. Il bug **non emerge** finché non arrivano record con quella colonna valorizzata
dentro la finestra processata (es. seed storico via `--ignore-odi-flag` [[LL-024]] che porta molte pesate con
`DATA_SCADENZA` futura).

## Regola
Per **ogni** colonna data proveniente da Logistix usare `julian_to_date(F.col(...))` (da `logistica_utils`),
mai `.cast("date")`. Esempio (`silver_pesate`):
```python
.withColumn("DATA_SCADENZA", julian_to_date(F.col("DATA_SCADENZA")))   # NON .cast("date")
```
`DATA_BOLLA`/`PSP_DATABOLLA` sono l'eccezione nota (sono già `DATE` nel sorgente): verificare il tipo reale
prima di scegliere.

## Perché
Un JDN è un intero grande (~2.4M). `cast("date")` su un intero = giorni dal 1970 → 2.4M giorni ≈ anno 8710.
`julian_to_date` applica invece l'offset dell'era giuliana (`TO_DATE(n,'J')` in Oracle legacy) restituendo la
data reale. La `DateType` con anno fuori range rompe la conversione Arrow/Python a valle (non in Spark puro).

## Conferme e contraddizioni
- 2026-09-02 · Francesco Foconi · `silver_pesate.DATA_SCADENZA`: col cast, 93+ righe con anno ~2461321 e crash
  LAD; con `julian_to_date`, 17.102/17.102 corrette (min 2026, max 2031), LAD `NO_LATE_ARRIVING`.
- Automazione candidata: check DQ "nessuna data business con anno fuori [1990, 2100]" sui silver Logistix.
