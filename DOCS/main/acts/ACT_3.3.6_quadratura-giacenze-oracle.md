# ACT_3.3.6 · Quadratura vs Oracle (QTA_DISPONIBILE)

**Status**: in-progress
**Type**: dq
**Origin**: sprint 3.3
**Sprint**: 3.3 — Gold F_GIACENZE
**Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (richiede cloud + Oracle sorgente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_3.3.2   **Blocca**: certificazione F_GIACENZE
**ADR collegate**: ADR-0014 (DQ interni)   **OP collegati**: —

## Contesto e motivazione
Il Gold `F_GIACENZE_DAILY` (prodotto da `gold_f_giacenze_daily.py`, ACT_3.3.2) va certificato
confrontando le quantità di stock con la sorgente legacy Oracle, per garantire che la nuova pipeline
Spark riproduca i valori del vecchio DWH. Controparte legacy: **`CDT_DW.F_STOCK`** (procedura
`SP_LOAD_F_STOCK`) — vedi [[../07_certifica_gold_vs_cdtdw.md]] §1.6, che marca F_GIACENZE_DAILY come
🟢 "Decode A0-A2 fatto — ALLINEATO con gap misura VAL_STOCK". Metodologia: playbook di certificazione
wave (memoria progetto "Playbook certifica wave").

> **Nota misura (anti-invenzione)**: il titolo storico dell'ACT cita `QTA_DISPONIBILE`, ma il Gold
> reale NON espone quella colonna (era inventata e rimossa, vedi header `silver_prep_giacenze.py` e
> `gold_f_giacenze_daily.py`). Le misure di quantità effettivamente prodotte sono **`QTA_PEZZI`**
> (da `STKQTAPZ`/`PZ_STOCK`) e **`QTA_UF`** (da `STKQTAUF`/`QTA_UF_STOCK`). Il campo da quadrare va
> concordato: `QTA_DISPONIBILE` come label logica → mappare sulla misura Gold reale (da verificare
> quale delle due, o loro derivata, corrisponde alla "disponibile" del legacy `F_STOCK`).
> I `VAL_STOCK_*` sono a 0 (gap noto OP ST-01/ST-02, sorgente valorizzata assente) → esclusi dalla quadratura.

## Obiettivo
Quadratura Gold `F_GIACENZE_DAILY` vs `CDT_DW.F_STOCK` entro tolleranza concordata, sul grain di
confronto (SITO, DATA_FOTO, ART_RADICE — aggregato SUM quantità + COUNT righe). Fatto = delta nullo o
entro soglia, documentato con report per chiave.

## Analisi tecnica
- **Grain Gold**: `F_GIACENZE_DAILY` ha grain `(DATA_FOTO, ART_COD_INTERNO, MAG_COD)`. Per il confronto
  col legacy si aggrega su `(SITO, DATA, ART_RADICE)` con SUM delle quantità (07 §1.6 "Procedura").
- **Strumento**: lo script parametrico `scripts/quadratura/quadratura_fact.py` (CDT_DW/ODI vs Gold Delta).
  **Attenzione**: attualmente il dict `FACTS` supporta SOLO `CARICO` e `PREP_SPED` → per giacenze va
  **aggiunta una nuova entry `GIACENZE`** con: `oracle_schema=CDT_DW`, `oracle_table=F_STOCK`,
  `oracle_sito` (colonna sito su F_STOCK, da verificare via `--discover`), `oracle_date` (semantica
  DATA_FOTO/stock: FK `L_GIORNO` oppure YYYYMMDD, da verificare), `oracle_measures` (misure stock),
  e il lato Gold `gold_path` → `f_giacenze_daily`, `gold_sito`, `gold_date=DATA_FOTO`, `gold_measures`.
  Lo script legge il Gold via `live_delta_files()` (add−remove sul `_delta_log`, no Spark) per non
  contare i tombstone (pattern `delta-tombstone-pyarrow-read` in memoria).
- **Mapping sito**: `MAG_SITO_COD` (CDT_DW, es. `0005C`) → codice canonico Gold (`05`) via
  `CDT_ESTR.S_LOGISTIX` (`FLAG_ATTIVO=1`), normalizzazione `int(cifre)` + zero-pad 2. Da verificare se
  il lato Gold giacenze espone `SITO_COD` o solo `MAG_COD` (il Gold F_GIACENZE ha `MAG_COD`, non `SITO`).
- **Discovery preliminare**: `python quadratura_fact.py --fact GIACENZE --discover` (dopo aver aggiunto
  la config) per leggere colonne reali di `CDT_DW.F_STOCK` e confermare sito/date/misure.
- **Connessione Oracle**: `.env` in `scripts/landing_simulator/` (`ORACLE_HOST/PORT/SERVICE/USER/PASSWORD`),
  deps `oracledb python-dotenv pandas pyarrow`. Richiede accesso simultaneo a cloud (Gold Delta) e Oracle
  → non eseguibile offline.
- **Criticità ordering (OP-29)**: prima di certificare, assicurarsi che il Gold locale/cloud sia
  effettivamente popolato: `silver_giacenze_aggregata`/`silver_t_stock` dipendono da
  `silver_catena_unificata` che in locale può risultare vuota (07 §1.6 criticità; pipeline_mapping
  §"Dipendenze di ordinamento Silver"). In cloud il DAG del workflow [[ACT_3.4.1_workflow-giacenze]]
  garantisce l'ordine. Rischio di quadrare su Gold parziale se non verificato.
- **Nota semantica legacy**: in CDT_DW le giacenze potrebbero essere aggregate per articolo commerciale,
  non per radice (07 §1.6) → verificare la chiave articolo prima di dichiarare uno scostamento.

## Sviluppo (diario)
- 2026-07-03 · avanzamento ~20%; impostazione query di confronto, esecuzione bloccata su cloud+Oracle.

## Verifica
- Report di `quadratura_fact.py --fact GIACENZE --da ... --a ... [--per-mese] --soglia X`: delta% per
  `(SITO, PERIODO)` su CNT + misure quantità; flag `!` se delta > soglia o chiave mancante; exit 0/1.
- Chiavi "solo in ODI" / "solo in Gold" a zero (o giustificate).
- Delta entro tolleranza concordata (default script 1.0%).

## Esito
— (in attesa di accesso cloud + Oracle)

## Follow-up
- Aggiunta della config `GIACENZE` in `scripts/quadratura/quadratura_fact.py` (se non tracciata altrove)
  → ACT emergente 9000+.
- Eventuali scostamenti non spiegabili (grain/articolo commerciale vs radice) → ACT emergente 9000+.
- Gap `VAL_STOCK_*` (ST-01/ST-02): resta fuori scope finché non si identifica la sorgente valorizzata.
