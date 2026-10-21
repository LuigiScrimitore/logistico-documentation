# ACT_9033 · Fix join testata F_CARICO: ~17% etichette perse sui carichi multi-ordine

**Status**: in-progress
**Type**: fix (bug pipeline)
**Origin**: quadratura F_CARICO ([[ACT_9032]]) — copertura gold ~82% vs CDT_DW anche su giorni pieni (18/18 siti)
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-21   **Closed**: —   **Owner**: team
**OP collegati**: Q-01   **Lesson**: [[LL-039]]

## Sintomo
Su giorni recenti **pieni** (tutti i 18 siti), il gold `f_carico` ha solo **~82%** delle etichette di
`CDT_DW.F_CARICO` (es. 10-15: gold 22.991 vs ODI 28.191). Non è copertura siti né flag: è un gap **dentro i
carichi che abbiamo già** (95% delle etichette mancanti sta in carichi presenti nel gold).

## Diagnosi (misurata sul dato, 10-15)
- Pesate nel silver = **28.191 = esattamente l'ODI** → le pesate ci sono tutte (estrazione ok).
- Catena join: `p⋈r` = 27.829 → `⋈t (testata)` = **22.991** → il calo è **tutto nella join con la testata**.
- Testata vs dettaglio a livello (sito,carico,**ordine**): dettaglio 2.338, testata **1.830** → **515 ordini**
  sono nel dettaglio ma non nella testata. A livello (sito,carico): **0 mancanti** (i carichi ci sono tutti).
- **Bronze `sto_tes_carichi`: 47.122 righe = 47.122 (carico,mag) = 47.122 (carico,mag,ordine)** → **1 riga per
  carico**. La MERGE della landing usa `merge_keys=[STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO]` **senza ordine** →
  i carichi **multi-ordine** vengono collassati a una riga.
- Il dettaglio è multi-ordine → la join testata su `(SITO,CARICO,DATA,ORDINE)` scarta le righe degli ordini
  collassati. **Test**: join su solo `(SITO,CARICO)` → **27.829 etichette, 0 fan-out** (righe = etichette distinte).

## Fix applicata
`notebooks/silver/carichi/silver_prep_carico.py` v2.1.0: join testata a livello **CARICO** `(SITO,CARICO)`
(con dedup di sicurezza su df_t), invece di `(SITO,CARICO,DATA,ORDINE)`. Copertura F_CARICO attesa **82%→~99%**.
Le misure (QTA/UF/PES/VOL dalla pesata/dettaglio) quadrano quindi su ~tutte le etichette.

## Trade-off / nota
Il bronze ha **già** collassato i multi-ordine → la testata è per-carico: gli attributi d'ordine
(`DATA_EMISSIONE_ORD`, `DATA_PREV_CONS_FORN`) sono quelli dell'**unico ordine superstite** per i carichi
multi-ordine. Per fedeltà **per-ordine** servirebbe la fix profonda (**opzione B**): aggiungere
`STCAR_NRO_ORDINE` ai `merge_keys` della landing e ri-landare → testate multi-ordine preservate. Da valutare
se i GG_*/date per-ordine lo richiedono (follow-up).

## Come verificarla
- Run DEV `silver_prep_carico` + `gold_f_carico` per un giorno pieno → copertura vs CDT_DW ~99% (etichette),
  misure QTA/UF/PES quadrano sulle comuni.

## Esito (VALIDATO 2026-10-21) ✅
Re-run DEV (sandbox, poi distrutta) `silver_prep_carico`+`gold_f_carico` per 202610 = SUCCESS. Copertura
F_CARICO vs CDT_DW **da ~80% a ~98%**: 10-13 25.901/26.415, 10-14 27.825/28.439, 10-15 **27.829/28.191 (98,7%)**,
10-16 29.236/29.975. Residuo ~2% = join MSI (≈362 su 10-15), minore. Le misure (dalla pesata/dettaglio) quadrano
sulle etichette comuni (calcolo già validato, [[ACT_9029]]). Status: **gap chiuso**; da propagare al re-run
completo dei giorni di quadratura.
