---
data: 2026-10-21
titolo: "Gap copertura F_CARICO (82%) chiuso: la join testata scartava ~17% etichette dei carichi multi-ordine (merge key senza ordine)"
autore: Francesco Foconi
push_monorepo: "diretto su main (fix silver + doc)"
push_documentation: "split dopo"
push_gitlab: "workflows: al prossimo giro CI (poi re-run per materializzare)"
act: [ACT_9033, ACT_9032]
adr: []
lesson: [LL-039]
op: [Q-01]
---

## Contesto
Mettendo su la quadratura F_CARICO ([[ACT_9032]]) è emerso che il gold copre solo ~82% delle etichette di
CDT_DW anche su giorni pieni (18/18 siti). Indagine richiesta: "chiudi il gap pesate".

## Diagnosi (misurata, 10-15)
Le pesate ci sono tutte (silver = 28.191 = ODI). Il calo è **nella join con la testata**: `p⋈r`=27.829 →
`⋈t`=22.991. Root cause: **bronze `sto_tes_carichi` ha 1 riga/carico** (merge key `carico+magazzino` senza
ordine → multi-ordine collassati); il dettaglio è multi-ordine → la join su `(SITO,CARICO,DATA,ORDINE)` scarta
le righe degli ordini collassati. Test: join su solo `(SITO,CARICO)` → 27.829 etichette, 0 fan-out.

## Fix
`silver_prep_carico.py` v2.1.0 ([[ACT_9033]], [[LL-039]]): join testata a livello **CARICO** `(SITO,CARICO)`
con dedup di sicurezza. Copertura attesa 82%→~99%. Provato a livello SQL (27.829 vs 22.991).

## Prossimo passo
Deploy + re-run `silver_prep_carico`+`gold_f_carico` su un giorno pieno per materializzare e verificare la
copertura ~99% e le misure quadrate → esito in worklog.

## Nota
Fix profonda alternativa (opzione B): `STCAR_NRO_ORDINE` nei merge_keys della landing + re-land, per preservare
le testate per-ordine (date emissione/conferma per-ordine). Da valutare come follow-up.
