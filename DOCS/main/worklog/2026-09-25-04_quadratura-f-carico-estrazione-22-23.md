---
data: 2026-09-25
titolo: "Quadratura F_CARICO: estrattore validato + estrazione CDT_DW 22-23 Sett + confronto fase 1 (chiavi/colonne)"
autore: Francesco Foconi
push_monorepo: "PR #14 (feat/act-9029) allineata a main + esito"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: [ACT_9029]
adr: []
lesson: []
op: [Q-01]
---

## Contesto
F_CARICO ora è sul **gold cloud** (11→22 verde, dup risolto [[LL-034]]). Si avvia la quadratura Q-01
**a gradi**: prima struttura (chiavi + numero colonne), poi bontà del dato. Usato il nuovo
`scripts/quadratura/extract_f_carico.py` ([[ACT_9029]]).

## Cosa fatto (VPN attiva, `py -3.12`)
1. Dipendenze: installate `pandas`/`pyarrow` in `py -3.12` (aveva già `oracledb`/`dotenv`).
2. **`--discover`**: `CDT_DW.F_CARICO` = **63 colonne**, nessuna PK; grain = `MAG_SITO_COD` + `NUM_DOC_CARICO`
   + `NUM_ETICH`. Tool validato a runtime.
3. **Estrazione 22-23 Sett 2026** (READ-ONLY): 22 → 25.556 righe, 23 → 28.993 righe (tot **54.549**) →
   parquet per-giorno in `LOGISTICO_DATA/quadratura/f_carico/cdtdw/2026/09/{22,23}/`.
4. **`--gold-schema`** (parquet locale snapshot 202608): **48 colonne** (+ ANNO_MESE).

## Confronto fase 1 (struttura)
- **Chiavi/grain corrispondono**: SITO + NUM_DOC + NUM_ETICH su entrambi (ODI `MAG_SITO_COD/NUM_DOC_CARICO/
  NUM_ETICH` ↔ gold `SITO_COD/NUM_DOC_CARICO/NUM_ETICH`).
- **Numero colonne**: 63 (ODI) vs 48 (gold). ODI ha surrogate ID extra; gold ha colonne tecniche/`*_NAT`.
- Caveat: gold locale stantìo (202608) → schema/valori "veri" dal gold **cloud** per la fase 2.

## Fase 3 — confronto misure (fatto, giorno 22)
Tool `scripts/quadratura/compare_f_carico.py` (ODI parquet vs gold cloud via SQL warehouse Engineering /
databricks-sdk), grain etichetta (SITO+NUM_DOC+NUM_ETICH), nessuna soglia.
- **Copertura**: gold DEV = solo **5 siti** (09,11,18,20,57) su 22; chiavi gold ⊂ ODI (0 "solo gold");
  su ODI 25.553 chiavi vs gold 3.669 (landing dev parziale). Il 23 **assente** dal gold.
- **Misure sulle 3.669 chiavi comuni**:
  - `QTA_CARICO`, `QTA_UF_CARICO`, `PES_CARICO` → **0 differenze, quadrano al 100%**.
  - `VOL_CARICO` → delta totale 2,8 su 1,1 mld (arrotondamenti) → ok.
  - `QTA_ORD_FORN` → 1.732 chiavi diverse (allocazione per-etichetta) → **OP-CAR-3** noto.
  - `VAL_COSTO_CARICO` → gold = 0 ovunque → **OP-CAR-1** (sorgente costo dismessa).
- Dipendenze: aggiunto `databricks-sdk` a `py -3.12`.

## Prossimi passi
1. Se serve quadrare anche il **23/24**: caricarli sul gold cloud (23 assente) ed estrarre l'ODI del 24.
2. Approfondire **QTA_ORD_FORN** (OP-CAR-3) con confronto allocazione-aware, e confermare **VAL_COSTO** OP-CAR-1.
3. Mergiare PR #14 (estrattore + compare + ACT_9029 + mappa colonne + worklog) — allineata a main.
