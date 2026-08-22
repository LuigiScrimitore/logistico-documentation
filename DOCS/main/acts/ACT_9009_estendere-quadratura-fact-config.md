# ACT_9009 · Estendere `quadratura_fact.py` ai fact mancanti (GIACENZE/TRASPORTO/TURNO/TRACC)

**Status**: done   **Type**: feature   **Origin**: emerged (cross-check doc-vs-codice 2026-08-01)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (tooling quadratura)
**Gg (stima)**: 1   **Closed**: 2026-08-04   **Blocco**: 🟢 codice locale (esecuzione vs Oracle resta cloud-gated)
**Created**: 2026-08-01
**Dipende da**: decode A0-A2 ([[ACT_9000]])   **Blocca**: quadrature dati dei fact non-carico
**ADR collegate**: ADR-0013 (F_TRASPORTO MTV), ADR-0008 (chiavi naturali)   **OP collegati**: OP-CAR-4 (tombstone), ST-01 (VAL_STOCK), OP-27 (misure proxy)

## Contesto e motivazione
`scripts/quadratura/quadratura_fact.py` copriva nel dict `FACTS` **solo** `CARICO` e `PREP_SPED`: per gli
altri fact la quadratura non era nemmeno lanciabile. Il decode strutturale era già in
[`07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md) ([[ACT_9000]]) → mancava la config.

## Obiettivo
`FACTS` esteso a GIACENZE, TRASPORTO, TURNO_PREP_SITO, TRACCIABILITA, pronti per `--discover` e per la
quadratura dati appena si ha l'accesso Oracle, **senza** che una config incompleta produca errori oscuri.

## Analisi tecnica — 4 finding emersi verificando il codice reale
La stesura della config ha richiesto di leggere i notebook Gold: le ipotesi dell'ACT originale erano in
parte **sbagliate**. Finding (tutti verificati sul codice/dati, non su doc):

1. **`F_GIACENZE_DAILY` non ha dimensione sito.** Grain reale `(DATA_FOTO, ART_COD_INTERNO, MAG_COD)`; il
   notebook dichiara esplicitamente "le giacenze sono per MAG_COD (non per SITO)". Il grain di confronto
   `(SITO, PERIODO)` era quindi inapplicabile → introdotto il supporto ai **fact senza sito** (grain = solo
   PERIODO, etichetta `(tutti)`). Serve, in futuro, la mappatura `MAG_COD ↔ MAG_SITO_COD` per scendere di grana.
2. **`F_TRASPORTO` non espone `KM` né `COSTO_EUR`.** L'ACT prevedeva "SUM KM": il Silver
   `silver_prep_trasporto` produce nodi/vettore/bolla/`LEAD_TIME_GG`, **nessuna** quantità o costo (listini
   corrieri assenti, ADR-0013). → quadratura TRASPORTO sul **solo COUNT** dei movimenti; `LEAD_TIME_GG` è
   nostro-only, non confrontabile.
3. **`QTA_DISPONIBILE` (giacenze) non esiste** — confermato il refuso già corretto in `02_pipeline_mapping`
   ([[ACT_9008]] wave): le misure reali sono `QTA_PEZZI`/`QTA_UF`/`PREZZO_MEDIO_PONDERATO`; `VAL_STOCK` non è
   alimentato (ST-01/OP-CAR-1).
4. **Bug nel reader Gold (trovato dal test funzionale).** `query_gold_kpi` legge i parquet con
   `pq.ParquetFile`, che **non** ricava le colonne di partizione dal path. Per `f_giacenze_daily`
   (`partitionBy DATA_FOTO`) e `f_turno_prep_sito` (`partitionBy DATA_PREPARAZ`) la colonna data risultava
   **tutta NULL** → il filtro per data scartava **ogni riga** (quadratura silenziosamente vuota). Non
   emergeva su CARICO/PREP_SPED/TRASPORTO/TRACC perché lì la data è colonna fisica (partizione su
   `ANNO_MESE`/`GIORNO_BOLLA_SPED_ID`).

### Modifiche allo script
- **4 nuove entry** in `FACTS` (`GIACENZE`, `TRASPORTO`, `TURNO_PREP_SITO`, `TRACCIABILITA`): lato **Gold
  verificato** sul codice dei notebook; lato **CDT_DW ipotetico** e marcato `oracle_confirmed: False`.
- **Fact senza dimensione sito**: `oracle_sito`/`gold_sito` = `None` → grain solo PERIODO.
- **Fact senza misure comuni**: `measures` vuote ammesse → si quadra il solo COUNT (il COUNT non dipende più
  dalla prima misura, che prima causava `IndexError` con dict vuoto).
- **`hive_partition_values()` + `read_gold_frame()`**: reidratano le colonne di partizione dal path e
  **deduplicano** il reader Gold prima copiato in due funzioni (fix del finding 4).
- **Confronto date robusto**: `.dt.normalize()` su entrambi i lati invece di `.dt.date` (il comportamento di
  `.dt.date` cambia tra pandas 2.x e 3.x e rompeva il confronto: verificato con pandas 3.0.5).
- **`validate_config()`**: verifica le colonne configurate contro `ALL_TAB_COLUMNS` e si ferma con un
  messaggio chiaro (+ suggerimento `--discover`) invece di lasciar emergere un `ORA-00904`.
- **`exempt_measures`**: misure mostrate nel report ma **non** conteggiate come anomalia (divergenze
  deliberate/note, marcate `~`).
- `--discover` ora segnala se la config del fact è un'ipotesi e stampa la `note` del fact.

## Verifica
- `python -m py_compile` OK.
- **Test funzionale offline** sui parquet reali del warehouse locale (`scripts`+`LOGISTICO_DATA` in Docker):
  per ogni fact si verificano le colonne Gold configurate e si esegue `query_gold_kpi` su giugno 2026.
  Esito: 6/6 fact leggono le colonne configurate; conteggi non vuoti anche per i due fact partizionati sulla
  data (che prima restituivano 0 chiavi).
- Quadratura **dati vs Oracle**: resta **cloud-gated** (serve `--discover` per confermare i nomi CDT_DW).

## Esito
Script esteso da 2 a **6 fact** e reso robusto: config validata a runtime, fact senza sito/misure supportati,
bug delle colonne di partizione risolto, reader Gold deduplicato. I nomi colonna CDT_DW dei 4 fact nuovi sono
**ipotesi dichiarate** (`oracle_confirmed: False`) da confermare con `--discover` al primo accesso Oracle;
finché non lo sono, la quadratura si ferma prima di produrre numeri sbagliati.

## Follow-up
1. Al primo accesso Oracle: `--discover` sui 4 fact → confermare date-FK e popolare `*_measures` (le misure
   Gold candidate sono elencate nella `note` di ogni entry).
2. Definire la mappatura `MAG_COD ↔ MAG_SITO_COD` per portare GIACENZE a grana sito (oggi solo per data).
3. Confluisce nelle quadrature di [[ACT_9000]] e nei gate [[ACT_GATE-3]]/[[ACT_GATE-4]]/[[ACT_GATE-5]]/[[ACT_GATE-6]].
