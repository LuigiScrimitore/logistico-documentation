# ACT_9035 · Recupero del residuo ~2% copertura F_CARICO: riconciliazione (bolla, ordine) pesata↔dettaglio

**Status**: done
**Type**: fix (copertura / correttezza)
**Origin**: follow-up [[ACT_9033]] (residuo ~2% lasciato come open point) — richiesta "va risolto subito"
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-23   **Closed**: 2026-10-23   **Owner**: team
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
- **Release**: monorepo @b329553 → GitHub (workflows @6143c71, documentation) → GitLab workflows
  **v0.1.20** (push solo main, no tag [[LL-031]]); `deploy_dev` (MI) success, notebook v2.2.0 verificato sul job MI.
- **Re-run DEV** `logistica_carichi` (run 533031850033208, 202610) = **SUCCESS** → gold F_CARICO ricostruito.
- **Verifica end-to-end (13–16/10, warehouse)** ✅:
  - Copertura vs CDT_DW: 13/10 **100,0%**, 14/10 **100,0%**, 15/10 **100,0%** (28.191/28.191), 16/10 **100,0%**
    (prima ~98%).
  - Gold 13–16: **113.020 righe = 113.020 etichette distinte** → **0 fan-out**.
  - Misure chiave (QTA/UF/PES/VOL) quadrano sulle comuni; unico scarto = **4 etichette duplicate
    nell'ODI legacy** (`etich_odi_duplicate=4`, gold_duplicate=0) — artefatto sorgente, non errore gold.
- **Quadratura pubblicata rigenerata** (run 323182479522217) per 13–16/10 → tabelle
  `gold_dev.logistica_dm.quadratura_f_carico_*` ora riflettono il ~100%.
- **Backfill storico — 2 fasi** (richiesta "tutto il gold ok"):
  1. Re-process logica su 202610 e 202609 da sorgenti silver esistenti (v2.2.0). Emerse però **buchi in
     settembre**: solo **20/30 giorni**, 94.784 righe (03–08, 23, 25–27 mancanti) → settembre era stato
     **ingerito parzialmente** in ramp-up, non solo mal-processato.
  2. **Ricarico dalla sorgente** (estrazione Oracle per range, backfill reale): `extract_oracle_to_landing.py`
     con **config dedicata** `config_backfill.yaml` (selection disattivata → `--from-date/--to-date` +
     `--ignore-odi-flag` effettivi) su `sto_tes_carichi,sto_righe_carico,pesate`, 3 blocchi da 10 gg
     (~1,23M righe). Copia sul **Volume** `landing_dev` (l'abfss landing non è scrivibile dall'utente, ACT_9034)
     → pipeline mirata ramo F_CARICO (run 552522402835429: bronze con `landing_base_path`=Volume per 09/10-20-30,
     silver `full_refresh`, prep, gold).
  - **Risultato gold F_CARICO 202609: 94.784 → 657.114 righe** (= etichette distinte, **0 fan-out**), **30/30
    giorni** coperti, distribuzione feriale/weekend regolare. 202610 invariato (439.229). Entrambi i mesi su v2.2.0.
- **Quadratura settembre** (estratto ODI CDT_DW 30 gg = 684.717 righe → Volume → notebook, run 389456114113878):
  copertura **96,0%**, misure comuni QTA 85,8% / UF 85,0% / PES 87,2% / VOL 93,5% (ORD_FORN 6,9%, COSTO 15,5%).
  Due effetti (non bug): (a) **copertura bassa a inizio mese** (01/09: 45%, poi ~100% dal ~10) = effetto-bordo
  della finestra pesate (bolle datate agosto fuori range); (b) **drift misure** su etichette comuni = ri-estrazione
  *di oggi* vs snapshot **congelato** del legacy (dati storici corretti dopo il consumo ODI). Ottobre quadra 100%
  perché recente (stessa epoca).
- **Downstream rinfrescati** (run 294584164203101): `gold_late_arriving_handler` + `gold_a_inbound_mensile` 202609 = SUCCESS.
- **Copertura inizio settembre — RISOLTA**: ri-estratte **pesate agosto** (688.221 righe; le bolle di fine
  agosto dei carichi di inizio settembre) → bronze_pesate(08/31) → silver_pesate full_refresh → prep+gold
  (run 468804598453575) → ri-quadratura (run quad_sett_v2). **Copertura settembre 96% → 100,0%** (01/09
  45%→100%; ODI 684.597 / gold 684.598).
- **Misure settembre — chiarimento grana**: il match per `(giorno,sito)` risultava ~85-93%, ma a **livello
  etichetta QTA è identica su 684.439/684.555 = 99,98%** (solo **116** diverse, delta medio ~195 = correzioni
  storiche reali). L'85% era artefatto: una sola etichetta che drifta fa fallire il MATCH dell'intero gruppo
  giorno-sito. Settembre quadra di fatto come ottobre; residuo = dato storico, non errore pipeline.
- **202608** (solo 31/08) non incluso. `config_backfill.yaml` committato tra gli script per i backfill futuri.

## Quadratura completa settembre + ottobre (confronto corretto 1 riga/etichetta)
- **Metodologia**: il confronto va fatto **deduplicato per etichetta su entrambi i lati** (il notebook già lo fa
  con dropDuplicates; una query manuale che somma i duplicati ODI gonfia falsamente il delta). L'ODI legacy ha
  **duplicati** di etichetta (DQ legacy) che il gold non ha.
- **Settembre** (ODI 684.597 etich · copertura 99,99%): QTA −0,005%, UF −0,005%, PES −0,001%, VOL −0,005%.
- **Ottobre 1–21** (ODI 468.423 etich · copertura 99,76% dopo fix 21/10): QTA −0,001%, UF −0,001%, PES −0,000%, VOL −0,001%.
- **Fix 21/10**: il giorno 21 era quasi vuoto in gold (358/29.547) — pipeline normale non lo aveva completato.
  Backfill carichi 15–21/10 (run 722614107552743) → gold ottobre 439k→467k etich, copertura 93,76%→99,76%.
- Estratto ODI ottobre completo 1–21 (468.482 righe) sul Volume; tabelle `quadratura_f_carico_*` rigenerate.

## Conclusione
Gold F_CARICO (set+ott) **completo su v2.2.0**, **misure allineate a ≥99,99%** e **copertura ~99,8–100%** vs CDT_DW.
Il residuo frazionale **non è errore pipeline**: duplicati del legacy (deduplicati nel gold) + correzioni sorgente
post-congelamento legacy (dato storico). Un 100,000% bit-exact su mesi storici non è ottenibile. Punti aperti
indipendenti: OP-CAR-1 (costo), OP-CAR-3 (allocazione ord. forn.), fedeltà date per-ordine ([[ACT_9033]] opz. B),
e lo 0,2% copertura ottobre residuo (singole etichette sparse, basso ROI).
