# ADR-0010 · Strategia incrementale a tre pilastri (watermark + pattern #2 + pruning `_row_hash`)

**Status**: accepted (2026-06)

**Contesto**:
La pipeline gira ogni giorno su volumi grandi (storico bolle ~9.8M, liste ~7.3M righe). Ri-processare
tutto lo storico ogni giorno è insostenibile per tempo e costo. Serve una strategia **incrementale** che
sia (a) corretta (risultato incrementale == full), (b) idempotente (ri-run dello stesso giorno non
duplica), (c) efficiente sui volumi reali. Il problema si presenta a più livelli: quali righe *bronze*
sono davvero nuove, quali *gruppi* ricalcolare nelle aggregazioni silver, come non ri-datare righe
identiche.

**Alternative considerate**:
1. **Full recompute giornaliero** — semplice ma non scala (tempi/costi proibitivi sullo storico).
2. **Solo watermark sul clean** — processa il delta del giorno, ma le aggregazioni "uniche" (GROUP BY
   sullo storico per chiave) dipendono da *tutte* le righe di quelle chiavi, non solo dalle nuove.
3. **Tre pilastri combinati** (scelta): watermark + ricalcolo per chiavi-impattate + pruning a monte.

**Decisione**:
Strategia incrementale a **tre pilastri**:
1. **Watermark** (OP-35): tabella `config_<env>.etl.watermark` per `(stage, sistema, tabella, sito)`;
   i clean processano solo `_bronze_load_date > ultimo_processato`.
2. **Pattern #2 (chiavi-impattate)**: le aggregazioni "uniche"/prep ricalcolano **solo i gruppi toccati**
   dal batch (join null-safe sulle chiavi impattate + MERGE), non l'intero storico. Con **guard
   anti-degenerazione** (ADR incrementale correlata): se il batch tocca ~tutte le chiavi (full rebuild),
   si passa al path full senza cache per evitare spill catastrofici.
3. **Bronze pruning `_row_hash`** (OP-30): firma di contenuto per riga; righe identiche non vengono
   ri-datate → a valle arriva solo il **delta reale** (~22% misurato).

**Conseguenze**:
+ Clean 2–2.6× più veloci in locale; a valle solo delta reale; idempotenza garantita (MERGE null-safe).
+ Scala su cluster reale (impacted << totale sullo storico grande).
− Complessità maggiore (3 meccanismi da capire/mantenere). Bronze MERGE è più lento del CTAS (prezzo del
  pruning a monte, guadagno a valle).
− **Trappola** documentata: in un **full-rebuild** (tutta la clean con stesso `_silver_load_date`) il
  pattern #2 degenera; senza guard la `.cache()` esplode (~57GB spill). Fix = guard impacted>50%→full path.

**Riferimenti**:
- Sezione incrementale: `02_pipeline_mapping.md` e `03_linee_guida.md` (design incrementale OP-30/35).
- Codice: `lib/logistica_utils/utils.py` (`add_row_hash`, `bronze_merge_upsert`, watermark), `notebooks/silver/prep_spedizioni/silver_storico_*_uniche.py` (guard).
- OP-30, OP-35. Memory `big-rerun-pending`, `bronze-csv-schema-by-name`.
