# ACT_2.1.6 · Backfill storico Carichi (22 db-link LOGISTIX)

**Status**: in-progress
**Type**: feature
**Origin**: sprint 2.1
**Sprint**: 2.1
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD — richiede ambiente cloud + ADLS + db-link Oracle LOGISTIX
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.1.2, ACT_2.1.3, ACT_2.1.4, ACT_2.1.5   **Blocca**: quadratura Gold (ACT_2.3.4), validazione BA (ACT_2.4.3)
**ADR collegate**: ADR-0010 (incrementale watermark/pattern#2/pruning)   **OP collegati**: —

## Contesto e motivazione
I notebook Bronze Carichi (`notebooks/bronze/carichi/`) caricano l'**incrementale** giornaliero con pattern DELTA_MERGE (vedi [[ADR-0010]] — watermark/pattern#2/pruning). Per quadrare vs Oracle ([[ACT_2.3.4]]) e validare con i BA ([[ACT_2.4.3]]) serve però popolare le Bronze con lo **storico pregresso** letto dai 22 db-link LOGISTIX. Senza storico:
- la quadratura `quadratura_fact.py --fact CARICO` copre solo le date presenti in landing (es. dal 2026-06-09 in poi) — vedi `DOCS/main/07_certifica_gold_vs_cdtdw.md` §1.1 (nota "completare la landing locale sugli altri giorni per una quadratura piena");
- la validazione funzionale 3 mesi ([[ACT_2.4.3]]) non ha profondità storica.

Le 4 sorgenti transazionali multi-sito coinvolte (pipeline `logistica_carichi`):
`sto_tes_carichi`, `sto_righe_carico`, `pesate`, `tracciace178` — landing `logistix-landing/{sito}/…` (vedi `02_pipeline_mapping.md`, righe 192-195). CE178 ha **retention obbligatoria 5 anni, NO delete**.

## Obiettivo
Backfill storico completato sui 22 siti: le Bronze Carichi (`bronze_dev.logistica.sto_tes_carichi`, `sto_righe_carico`, `pesate`, `tracciace178`) contengono lo storico pregresso oltre all'incrementale. Fatto = conteggi Bronze per sito/periodo allineati alle sorgenti Oracle sul range storico.

## Analisi tecnica
- **Meccanismo di caricamento**: i notebook Bronze usano pattern DELTA_MERGE con MERGE null-safe e dedup per chiave naturale (vedi memory `bronze-csv-schema-by-name`). Chiavi di merge per tabella (`02_pipeline_mapping.md`):
  - `sto_tes_carichi`: `MAG_SITO_COD, STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO`
  - `sto_righe_carico`: `MAG_SITO_COD, SRCAR_NRO_CARICO, SRCAR_COD_MSI, SRCAR_COD_MAGAZZINO`
  - `tracciace178`: `MAG_SITO_COD, CE178_NRO_ETICHETTA, CE178_NRO_CARICO`
- **Estrazione Oracle→landing**: in locale il popolamento avviene via `scripts/landing_simulator/extract_oracle_to_landing.py` (config in `scripts/landing_simulator/config.yaml`, credenziali `.env` gitignored) + orchestrazione `scripts/rerun_22siti.ps1` / `rerun_1_bronze.ps1`. Lo script di backfill storico cloud che itera i 22 db-link — **da verificare** se sarà lo stesso extractor esteso al range storico o un job DAB dedicato.
- **Siti**: default runner = 22 siti (vedi memory `runner-siti-default-22`; il param `siti` del workflow elenca il sottoinsieme dev). Il backfill deve girare su tutti e 22 per evitare orphan SITO/AREA.
- **Mapping sito**: `MAG_SITO_COD` (CDT_DW, es. `0005C`) → `SITO_COD` canonico (`05`) via `int(cifre)+pad2` (memory `sito-mapping-slogistix`).
- Richiede connettività cloud verso Oracle LOGISTIX e landing/warehouse su ADLS/UC Volume (`/Volumes/landing_dev/logistica/files`, cfr. `databricks.yml`) — **non eseguibile offline**.

## Sviluppo (diario)
- 2026-07-03 · script pronto; avanzamento ~20%; esecuzione bloccata su accesso cloud+ADLS.

## Verifica
- Conteggi Bronze per `(SITO_COD, periodo)` confrontati con `SELECT COUNT(*)` sulle sorgenti Oracle LOGISTIX per lo stesso range; nessun gap sul range storico.
- A valle: `quadratura_fact.py --fact CARICO --da <inizio-storico> --a <fine-storico>` deve coprire l'intero range senza chiavi "solo in ODI" dovute a landing mancante (vedi `07_certifica_gold_vs_cdtdw.md`).
- Attenzione tombstone: la quadratura conta solo i file live via `live_delta_files` (`_delta_log`), non i parquet orfani da full_refresh (OP-CAR-4).

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
Nessuna al momento.
