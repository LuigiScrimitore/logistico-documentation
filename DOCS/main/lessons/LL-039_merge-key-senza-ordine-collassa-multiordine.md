# LL-039 · Merge key senza ordine collassa i carichi multi-ordine → join testata scarta etichette

**Data**: 2026-10-21 · **ACT**: [[ACT_9033]] · **Area**: carichi / landing-bronze

## Sintomo
`gold.f_carico` copre solo ~82% delle etichette di `CDT_DW.F_CARICO` anche su giorni **pieni** (tutti i siti).
Il gap sta **dentro carichi che abbiamo già**, non in siti/giorni mancanti.

## Causa
La landing/bronze di `sto_tes_carichi` usa `merge_keys = [STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO]` — **senza
l'ordine**. I carichi **multi-ordine** (più righe testata, una per ordine) vengono **collassati a una riga per
carico** (bronze: 47.122 righe = 47.122 (carico,mag) = 47.122 (carico,mag,ordine)). Il **dettaglio** resta
multi-ordine, quindi la join `silver_prep_carico` su `(SITO,CARICO,DATA,ORDINE)` **scarta le righe degli ordini
collassati** → ~17% di etichette perse. Le pesate NON mancano (silver pesate = ODI esatto): è solo la join.

## Soluzione
Join testata a livello **CARICO** `(SITO,CARICO)` (il bronze ha 1 riga/carico → 0 fan-out, dedup di sicurezza):
`silver_prep_carico.py` v2.1.0 ([[ACT_9033]]). Test: join su solo (sito,carico) → 27.829 etichette = 0 fan-out
(vs 22.991 con ordine). Fix profonda alternativa: aggiungere `STCAR_NRO_ORDINE` ai merge_keys della landing e
ri-landare (preserva le testate per-ordine).

## Come ritrovarla
Se una fact "a grana figlia" (righe/pesate) perde righe vs il legacy ma le sorgenti ci sono tutte, controlla il
**grain della testata** (`COUNT(*) == COUNT(DISTINCT chiave_merge)`?) e se la **merge key della landing** include
tutte le dimensioni su cui poi si **joina a valle** (qui: l'ordine). Vedi [[logistico-fcarico-dup-pesata-databolla]]
(altro caso di chiave di dedup instabile sui carichi).
