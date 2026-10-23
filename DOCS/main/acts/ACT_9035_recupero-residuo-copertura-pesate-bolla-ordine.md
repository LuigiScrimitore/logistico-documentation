# ACT_9035 · Recupero del residuo ~2% copertura F_CARICO: riconciliazione (bolla, ordine) pesata↔dettaglio

**Status**: in-progress (validato sul dato, in deploy)
**Type**: fix (copertura / correttezza)
**Origin**: follow-up [[ACT_9033]] (residuo ~2% lasciato come open point) — richiesta "va risolto subito"
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-23   **Closed**: —   **Owner**: team
**OP collegati**: Q-01   **Dipende da**: silver pesata/carico_dettaglio

## Contesto / sintomo
Dopo [[ACT_9033]] la copertura F_CARICO vs CDT_DW è ~98%: il residuo ~2% sono **pesate scartate**
dalla join `p⋈r` su `(SITO, CARICO, BOLLA_NRO, COMMESSA_NRO=ordine, ART_EAN13=MSI)` perché la loro
`(bolla, ordine)` non combacia col dettaglio, **pur avendo l'MSI nello stesso carico** (derivazione
bolla/ordine a monte diversa tra pesata e dettaglio). Parcheggiato in ACT_9033 perché allargare la join
sembrava rischioso (fan-out → articolo errato).

## Diagnosi sul dato (13–16/10, warehouse) ✅
- Totale pesate = **113.020** (= ODI). Non agganciate = **2.229** (~1,97%).
- Dei 2.229: **782** hanno `(sito,carico,ordine,msi)` con **una sola** bolla nel dettaglio →
  recuperabili fissando la bolla; **1.447** hanno `(sito,carico,msi)` con **una sola** `(bolla,ordine)`
  → recuperabili fissando bolla+ordine.
- **Ambigui = 0, orfani (MSI assente nel carico) = 0.** → il 2% è **interamente e univocamente
  recuperabile**, senza fan-out e con l'articolo corretto.

## Obiettivo ("fatto" =)
Copertura F_CARICO vs CDT_DW → **~100%** sulle etichette, **mantenendo** 1 riga per etichetta
(0 fan-out) e le misure chiave al 100%.

## Soluzione (design)
`silver_prep_carico.py` v2.2.0: **riconciliazione di `(BOLLA_NRO, COMMESSA_NRO)` della pesata PRIMA
della join**. Per le pesate non in match esatto, si adottano i valori del dettaglio **solo se la chiave
rilassata è univoca**: 1° `(sito,carico,ordine,msi)` → fissa la bolla (ordine invariato); 2° `(sito,carico,msi)`
→ fissa bolla+ordine. Le pesate ambigue restano invariate (cadono come oggi). La join e tutto il codice a
valle restano **invariati** (cambia solo l'input `df_p` riconciliato). Nessun fan-out: ogni tabella di
lookup è ≤1 riga per chiave (filtri di unicità).

## Come verificarla
- Simulazione SQL: match esatto ∪ recupero-univoco = 113.020 (0 non agganciate), 0 righe duplicate.
- Run DEV silver_prep_carico + gold_f_carico (periodo) → quadratura: copertura ~100%, misure chiave 100%, 0 fan-out.

## Esito (in corso — 2026-10-23)
- **Codice**: `silver_prep_carico.py` v2.2.0 (riconciliazione pre-join). `py_compile` OK.
- **Validazione simulazione SQL (13–16/10, warehouse)** ✅: su 113.020 pesate, dopo riconciliazione
  **agganciate 113.020 / non agganciate 0**; righe in output = 113.020 (**0 fan-out**); max righe
  dettaglio per 5-chiave = 1. Recupero del residuo 2.229 completo, senza duplicati.
- **Da fare**: deploy dev (solo notebook, no wheel) + re-run `logistica_carichi` (202610) + quadratura
  → conferma copertura ~100% end-to-end; worklog + chiusura.
