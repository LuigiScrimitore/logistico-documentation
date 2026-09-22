---
id: LL-029
titolo: Serverless — .cache()/.persist() su DataFrame non supportati (PERSIST TABLE), rimuovere l'hint
sintomi:
  - "[NOT_SUPPORTED_WITH_SERVERLESS] PERSIST TABLE is not supported on serverless compute. SQLSTATE: 0A000"
tag: [serverless, cache, persist, performance, incrementale]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-09-10
origine: [run-09-settembre, ACT_9027]
---

## Sintomo
Un task silver fallisce in serverless con
`[NOT_SUPPORTED_WITH_SERVERLESS] PERSIST TABLE is not supported on serverless compute`.
Nel nostro caso `silver_storico_liste_uniche` (e gemello `silver_storico_bolle_uniche`),
task del job `prep_sped`.

## Perche' non si vedeva prima (insidia)
La chiamata `.cache()` stava **solo nel ramo incrementale** (`incremental = not full_refresh AND
la tabella target esiste`), sotto-ramo "batch parziale" (righe del giorno <= 50% del clean).
- Il **primo run** / full-refresh (es. run_date 2026-09-02) va nel ramo `agg_src = src`: nessun
  cache -> passava.
- Il **primo run davvero incrementale** (target gia' costruito + batch del giorno piccolo, es.
  run_date 2026-09-09) entra nel ramo con `.cache()` -> il serverless lo blocca.
Classico bug latente serverless che emerge solo quando la pipeline gira in modalita' incrementale reale.

## Strada sbagliata
```python
# agg_src riusato da DQ + groupBy + MERGE -> "cache per non ricalcolare il join"
agg_src = s.join(imp, joincond, "inner").select("s.*").cache()
```
`.cache()` = `.persist(MEMORY_AND_DISK)`: sul serverless la persistenza esplicita
(RDD/DataFrame cache, `CACHE TABLE`, `PERSIST TABLE`) non e' disponibile.

## Regola
Rimuovere l'hint di cache: e' solo performance, non correttezza. Il serverless (Photon +
disk cache automatica) rimaterializza il join a costo accettabile.
```python
agg_src = s.join(imp, joincond, "inner").select("s.*")   # niente .cache() su serverless
```
Se in futuro servisse davvero materializzare per riuso pesante, scrivere una tabella/temp view
Delta intermedia (checkpoint esplicito), non `.cache()`. Vale insieme a [[LL-027]] (ANSI try_cast)
e [[LL-028]] (schema-evolution per-merge): sul serverless le ottimizzazioni vanno espresse
nell'API del comando, non come stato di sessione.

## Conferme e contraddizioni
- 2026-09-10 · Francesco Foconi · `silver_storico_liste_uniche` + `silver_storico_bolle_uniche`
  DEV: rimosso `.cache()`, deploy `bundle -t dev`, ri-run `prep_sped` run_date=2026-09-09 →
  task e job verdi (09 chiuso 7/7).
