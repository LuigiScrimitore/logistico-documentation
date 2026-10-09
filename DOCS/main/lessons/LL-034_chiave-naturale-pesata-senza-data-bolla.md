---
id: LL-034
titolo: La chiave naturale della pesata non include DATA_BOLLA — instabile tra ri-estrazioni, duplica F_CARICO
sintomi:
  - "il job carichi va KO ogni giorno sul dq_gate: unique_keys BLOCKING con N duplicati su gold F_CARICO"
  - "F_CARICO ha righe duplicate sulla grana [SITO_COD, NUM_DOC_CARICO, NUM_ETICH, NUM_BOLLA_FORN] identiche tranne QTA_ORD_FORN (una copia con la qta, l'altra 0.0)"
  - "silver.logistica.pesata ha 2 righe per la stessa etichetta (SITO, ETICHET_NRO) con DATA_BOLLA diverse e BOLLA_NRO placeholder vs reale"
tag: [silver, pesate, carichi, dedup, merge, natural-key, dq, gold, dati]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-09-24
origine: [run-1122-cloud, dq-gate-carichi-ko]
---

## Sintomo
Il job `carichi` fallisce **ogni giorno** sul `dq_gate` (1 check BLOCKING su 2 pipeline). Il check è
`unique_keys` di **F_CARICO** sulla grana `[SITO_COD, NUM_DOC_CARICO, NUM_ETICH, NUM_BOLLA_FORN]`:
poche righe **duplicate** (es. 3 su 45.247 nel mese) fanno scattare il blocco (tolleranza 0). Le 2 copie
sono **identiche tranne `QTA_ORD_FORN`** (una con la quantità, l'altra 0.0). F_CARICO NON è vuota: è
popolata e corretta al 99,99%, ma quelle poche righe di troppo bloccano la certificazione.

## Perche'
La causa è **a monte**, in `silver.logistica.pesata`. `silver_pesate.py` deduplica (Window) e fa MERGE
sulla chiave naturale **`(SITO_COD, ETICHET_NRO, DATA_BOLLA)`**, che **include `DATA_BOLLA`**.
La stessa pesata fisica viene **ri-estratta su più giorni** (finestra lookback dell'estrattore, [[LL-024]])
e ad ogni estrazione cambiano campi *instabili*: `DATA_BOLLA` slitta alla data di estrazione e `BOLLA_NRO`
evolve da placeholder (`'1'`/`'ONE'`) al numero reale. Poiché `DATA_BOLLA` è nella chiave, il MERGE del
giorno successivo **non aggiorna** la riga: ne **inserisce una seconda** → pesata ×2.

La catena carichi joina la pesata su **`BOLLA_NRO`** (non `DATA_BOLLA`) e la **pesata guida il grain**
(1 riga/etichetta). Due pesate con lo stesso `BOLLA_NRO` matchano entrambe il dettaglio → **fan-out**;
poi la window di distribuzione `QTA_ORD_FORN` (OP-CAR-3) assegna la qta a una copia e 0.0 all'altra.
Coerente con l'AS-IS ODI (punto C6 della revisione CDT_ESTR): il match pesate↔righe **esclude la data
bolla** (incongruenza rimossa nel 2008).

Evidenza: `(SITO_COD, ETICHET_NRO)` è **unico** (0 gruppi su 111.781 attraversano più di un carico) →
l'etichetta è l'identità stabile della pesata; nessun duplicato **intra-giorno** in bronze → la
duplicazione è **solo** cross-day da ri-estrazione.

## Regola
La chiave naturale della pesata (dedup Window **e** condizione di MERGE) deve essere basata
sull'**identità stabile** dell'evento di pesata, **senza `DATA_BOLLA`**:

```python
# dedup intra-run
w = Window.partitionBy("SITO_COD", "CARICO_LOG_NRO", "ETICHET_NRO").orderBy(F.col("_bronze_insert_ts").desc())
# merge incrementale
"tgt.SITO_COD = src.SITO_COD AND tgt.CARICO_LOG_NRO = src.CARICO_LOG_NRO AND tgt.ETICHET_NRO = src.ETICHET_NRO"
```

- `DATA_BOLLA` (e `BOLLA_NRO`) sono **attributi**, non identità: variano tra snapshot di estrazione.
  Tenere l'**ultimo** snapshot (`_bronze_insert_ts` DESC → whenMatchedUpdateAll) = numero bolla finale.
- Cleanup one-time dopo il fix: run `silver_pesate` con **`full_refresh=true`** (OVERWRITE) → ricostruisce
  la tabella pulita (1 riga per pesata), poi ri-run catena carichi sui mesi impattati → `dq_gate` verde.
- **Non rilassare il `dq_gate`**: `unique_keys` BLOCKING ha fatto correttamente il suo lavoro.
- Principio generale: se una tabella incrementale è raggiunta a valle su un sottoinsieme della sua chiave
  di MERGE, quel sottoinsieme deve **essere** la chiave (o la chiave deve essere un sovra-insieme stabile),
  altrimenti le ri-scritture accumulano duplicati che esplodono nei join a valle. Vedi anche [[LL-026]]
  (full_refresh deve fare OVERWRITE) e [[LL-022]] (date Logistix JDN, stesso notebook [[silver_pesate]]).

## Conferme e contraddizioni
- 2026-09-24 · run cloud 11→22: `carichi` KO tutti i 12 i giorni, tutti gli altri 6 job verdi. Diagnosi
  su `config_dev.etl.dq_results` + query dirette (warehouse Serverless): F_CARICO 202609 = 3 gruppi dup;
  silver.pesata = 97 righe di troppo su 111.878. Fix applicato: chiave `(SITO,CARICO_LOG_NRO,ETICHET_NRO)`.
