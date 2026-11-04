---
id: LL-041
titolo: Un giorno di landing riscritto dopo l'elaborazione viene saltato dal silver incrementale (watermark con ">")
sintomi:
  - "F_CARICO gold ha un giorno con poche righe (es. 3.774 invece di ~30.000) mentre landing e bronze sono completi"
  - "silver carico_dettaglio ha molte meno righe del bronze per una DATA_CARICO"
  - "testata presente in bronze ma assente in silver carico_testata"
tag: [silver, incrementale, watermark, landing, bronze, carichi, recupero]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-10-30
origine: [ACT_9038]
---

# LL-041 · Giorno di landing riscritto = righe saltate dal silver incrementale

## Sintomo
Gold F_CARICO del 28/10/2026: 3.774 righe contro ~30.000 del legacy. Landing e bronze completi (21.777 righe di dettaglio),
silver `carico_dettaglio` solo 2.660; 39 testate in bronze ma non in silver.

## Causa
`silver_carichi_dettagli` / `silver_carichi_testate` in incrementale leggono `_bronze_load_date > watermark` (maggiore stretto).
La run del mattino del 28 ha portato il watermark al 28; alle 20:35 il cutover DataRelay ha **riscritto** il file del 28;
il bronze l'ha ricaricato con `_bronze_load_date = 28` → mai più letto. Le righe poi modificate (es. timbro ODI sulle
testate) sono "risalite" con una data nuova; quelle invariate (dettaglio) sono rimaste perse. `silver_pesate` legge solo
`= run_date`: stesso rischio.

## Soluzione
Recupero col parametro esistente `process_from` (giorno prima di quello riscritto) su `silver_carichi_dettagli` e
`silver_carichi_testate`, `silver_pesate` con `run_date` del giorno riscritto, poi `silver_prep_carico` + `gold_f_carico`
(eseguito 2026-10-30 con i notebook deployati; bookmark versioni in `LOGISTICO_DATA/legacy9038/bookmark_recupero_28.json`).

## Regola
Ogni volta che si **riscrive** un giorno di landing già elaborato, va rilanciato il silver con `process_from` (o
`run_date`) su quel giorno. Guardrail da automatizzare: controllo bronze vs silver per `DATA_CARICO` dopo ogni run.
