---
id: LL-025
titolo: La alias-map sito va castata con double (non int) ed essere completa — sorgente S_LOGISTIX+WL1, non solo TABGEN
sintomi:
  - "orphan sito residuo sulle transazionali dopo aver completato la dimensione (codici alfabetici LGAX/LONX non agganciano)"
  - "get_sito_alias_map restituisce una mappa vuota o parziale"
  - "normalize_sito lascia il codice alfabetico invariato invece di mapparlo al numerico"
tag: [logistica, sito, mapping, normalize, wheel, bronze]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-03
origine: [ACT_9026]
---

## Sintomo
Le transazionali trasporti (`ordine`, `spedizioni_clean`) hanno il codice sito in encoding **misto**: alcune righe
numeriche (`20`, `35`), altre alfabetiche (`LGAX`, `LONX`). Dopo aver reso completa la dimensione `dim_sito`, gli
orphan **numerici** spariscono ma restano gli **alfabetici** — perché `normalize_sito` non li rimappa a numerico.

## Strada sbagliata
1. **Cast `int` sul codice numerico sorgente**: `F.col("TGEN_CAMPO1_TAB").cast("int")`. Dal bronze i numeri
   arrivano come `"20.0"` (string/parquet): `cast("int")` su `"20.0"` → **null** → la mappa esce **vuota** →
   `normalize_sito` fa solo `lpad` e lascia `LGAX` invariato → orphan.
2. **Alias-map solo da TABGEN** (tab 7): copre **5 siti**. Le transazionali ne referenziano di più → gli alias
   fuori-tabgen restano non risolti.

## Regola
In `get_sito_alias_map` (`lib/logistica_utils/utils.py`):
- cast **`double`→`long`** prima di stringere le cifre: `regexp_replace(col.cast("double").cast("long").cast("string"), "[^0-9]", "")` — robusto a `"20"`/`"20.0"`/numerico.
- costruire la mappa **completa** da `S_LOGISTIX` (anagrafica 22 siti: alias 4-char `LGAX` da `DBLINK_NAME`, 5-char
  `0020A` da `MAG_SITO_COD`) ⋈ `WL1_MAG_SITO_STORICO` (codice numerico `MAG_SITO_COD_ORIG`, correnti+attivi
  `DATFIN_VALID=99999999 AND MAG_SITO_ORIG_ATTIVO=1`). TABGEN resta solo **fallback** (non sovrascrive).

La numerica finale (lpad 2) la applica `normalize_sito`. Le chiavi mappa sono UPPERCASE (lookup case-insensitive).

## Perché
`normalize_sito` mappa alias→numerico **solo** se la alias-map è popolata: una mappa vuota (per il cast) o parziale
(solo TABGEN) degrada silenziosamente a `lpad`, lasciando gli alfabetici come orphan a valle. La fonte autoritativa
e completa dei siti è `S_LOGISTIX`, non `TABGEN`. Vedi [[LL-026]] (per propagare il remap serve full_refresh=overwrite).

## Conferme e contraddizioni
- 2026-09-03 · Francesco Foconi · DEV run_date 2026-09-02: con la mappa completa+cast double, `ordine` e
  `spedizioni_clean` → **orphan sito 0** (prima: 5 codici alfabetici orphan su ordine, idem spedizioni).
