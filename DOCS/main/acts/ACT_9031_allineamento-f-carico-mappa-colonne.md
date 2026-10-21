# ACT_9031 · Allineamento F_CARICO alla mappa colonne (GG_, rinomina vettore, flag/scad stock)

**Status**: in-progress
**Type**: fix / sviluppo
**Origin**: revisione mappa colonne F_CARICO (foglio `Quadratura_F_CARICO` 05/10, considerazioni utente) vs codice live
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-21   **Closed**: —   **Owner**: team
**Dipende da**: sorgente stock CND (az.4), meccanismo DQ/scarti (az.3)
**ADR collegate**: —   **OP collegati**: Q-01 (quadratura F_CARICO)   **Doc**: [[quadratura_f_carico_mappa_colonne]]

## Contesto
Revisione della mappa colonne: le 49 colonne gold erano verificate contro il legacy ([[ACT_9029]]).
Dalle considerazioni sul foglio emergono **4 azioni** (le altre voci sono già live o già correttamente
escluse — surrogate `*_ID`, storicizzate `ART_ST_*`, `GG_DIFF_*`, `AFFID_*`, `FASCIA_LAV_SITO_ID`,
`GIORNO_SCAD_CARICO_PREC_ID`, `DATI_STO_CARICO_FLAG`=costante 0, `ART_ID` dismesso).

## Le 4 azioni (obiettivo = allineare il gold alla mappa)
1. **GG_\* (4 diagnostici)** — aggiungere al gold `GG_VITA_RESID_ART_CARICO`, `GG_PREV_CONS`,
   `GG_EFF_CONS`, `GG_RITARDO_CONS`. Sono differenze di **date già presenti** nel fact (formule
   confermate 100% sui dati gg22, [[ACT_9029]]):
   - `GG_VITA_RESID = datediff(DATA_SCAD_CARICO, DATA_CARICO)`
   - `GG_PREV_CONS  = datediff(DATA_PREV_CONS_FORN, DATA_EMISSIONE_ORD)`
   - `GG_EFF_CONS   = datediff(DATA_CARICO, DATA_EMISSIONE_ORD)`
   - `GG_RITARDO_CONS = datediff(DATA_CARICO, DATA_PREV_CONS_FORN)`
2. **Rinomina `CORRIERE_COD` → `VETTORE_COD`** (nota utente "correggere con VETTORE_COD"). Il dato è
   corretto (è il vettore del carico); è solo il **nome** gold.
3. **CARICO_INCOMPLETO_FLAG** — nel legacy =1 se la chiave è negli scarti `E_CARICO` (CDT_DW post-load),
   NULL/0 altrimenti. Non è un dato del carico → va ricostruito dal **nostro DQ/quarantena**, non importato
   da F_CARICO.
4. **GIORNO_SCAD_STOCK_ID** — scadenza dallo **stock (CND/CNDSTOSTOCK)**, con fallback a `DATA_SCAD_CARICO`.
   Serve agganciare la sorgente stock (giacenze) alla pipeline carichi (join sito+radice+variante).

## Esito / stato per azione
- **Az.1 GG_\* — FATTA e VALIDATA** ✅: `notebooks/gold/carichi/gold_f_carico.py` v4.1.0, FASE 3c
  (4 `withColumn` `datediff`). Additiva (mergeSchema), nessun impatto sui gate.
  **Smoke test 2026-10-21** (sandbox personale, poi distrutta): run `gold_f_carico` su serverless = **SUCCESS**;
  i 4 GG_ popolati 100% su `gold_dev.logistica.f_carico`; **confronto per chiave vs CDT_DW (22/09) = 100% match
  su tutte e 4 le colonne** (3.669 chiavi comuni). → pronta per il dev condiviso al prossimo giro CI.
- **Az.2 rinomina `CORRIERE_COD`→`VETTORE_COD` — FATTA nel codice** (requisito cliente non derogabile,
  scope **colonna + tabella**, [[ADR-0028]]): rinomina su **18 file** — `VETTORE_COD`/`VETTORE_COD_NAT` in
  tutti i fatti (carichi/trasporti/prep_sped/aggregati), dimensione **`LU_VETTORE`** / silver **`dim_vettore`**
  (file notebook rinominati `*_dim_vettore.py`), `gold_lad_resolver`, 4 KPI SQL, `lib/logistica_utils`,
  workflow `logistica_dim_refresh`. Sorgenti (`STCAR_COD_CORRIERE`, `VETTORE_SPED_COD`, `VET_CODICE`) intatte.
  Verificato: 0 residui, sintassi OK, nessun test impattato.
  **RESA DEFINITIVA su dev (2026-10-21)** ✅: wheel ricompilato+ricaricato sul Volume; schema migrato in RENAME
  (columnMapping + RENAME COLUMN/TABLE su 9 tabelle, **dati preservati**, 0 residui `CORRIERE_COD`); deploy via
  GitLab `workflows v0.1.17` (push solo main, [[LL-031]]) → CI 6417 `deploy_dev` = success. Estrattore non
  impattato. Dettaglio: [[2026-10-21-04_vettore-migrazione-e-deploy]]. Da fare a go-live: stessa sequenza su **prod**.
- **Az.3 CARICO_INCOMPLETO_FLAG — NON fatta (proposed)**: dipende dal meccanismo scarti/quarantena gold
  (equivalente di `E_CARICO`). Da disegnare.
- **Az.4 GIORNO_SCAD_STOCK_ID — NON fatta (proposed)**: dipende dalla disponibilità dello stock scadenza
  nel flusso carichi. Da disegnare (join + fallback).

## Come verificarla
- Az.1: run DEV `logistica_carichi`; `SELECT` dei 4 GG_ su `gold_dev.logistica.f_carico` e confronto con
  `CDT_DW.F_CARICO` (gg già estratti 22-23) — devono coincidere.
- Az.2/3/4: aperte, da pianificare.

## Punti aperti
- Az.2 rinomina vettore: **go/no-go di team** (impatto 17 file + LAD + KPI).
- Az.3/4: sorgenti e disegno (scarti / stock scadenza).
