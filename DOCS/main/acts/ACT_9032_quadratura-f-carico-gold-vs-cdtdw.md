# ACT_9032 · Sistema di quadratura F_CARICO: gold vs CDT_DW (ODI) per il SAL

**Status**: in-progress
**Type**: tooling / quadratura
**Origin**: richiesta SAL — quadratura giornaliera misure gold vs vecchia F_CARICO (CDT_DW)
**Sprint**: trasversale quadratura / FASE 2 Wave A Carichi
**Created**: 2026-10-21   **Closed**: —   **Owner**: team
**ADR collegate**: —   **OP collegati**: Q-01 (quadratura F_CARICO), OP-QDR-1 (copertura vs finestra)
**Dipende da**: accesso Oracle CDT_DW (estrazione), gold F_CARICO cloud

## Contesto / obiettivo
Per il SAL serve un sistema **snello** che confronti ogni giorno le **misure** del gold `f_carico` con la
vecchia `CDT_DW.F_CARICO`, con possibilità di **drill per radice + variante logistica** oltre che per giorno/sito.
Idea: caricare file giornalieri dell'ODI e confrontarli in Databricks con il gold.

## Scelte di design (validate con proof 22-23/09)
- Confronto sulle **ETICHETTE COMUNI** (SITO+NUM_DOC+NUM_ETICH); la **copertura** (il gold dev ha un
  sottoinsieme, es. 7% delle etichette ODI) è **metrica a parte**, non un errore (OP-QDR-1).
- Grain configurabile: `giorno_sito` (default) · `articolo` (drill `ART_RADICE_COD`+`ART_VAR_LOGIS_COD`).
- Allineamento articolo lato ODI: **decodifica `ART_VAR_LOGIS_ID` via `L_ART_VAR_LOGIS`** → porta
  `ART_RADICE_COD`+`ART_VAR_LOGIS_COD` (ART_COD su F_CARICO è `'0'`). Verificato **100% = gold**.
- Tolleranza: 0 per conteggi/qta, `1e-3` per pesi/volumi (float).
- Esito proof 22-23: QTA_CARICO/QTA_UF/PES = **delta 0**; VOL ok a meno di arrotondamenti; QTA_ORD_FORN e
  VAL_COSTO divergono per i **punti aperti noti** (OP-CAR-3 allocazione, OP-CAR-1 costo non calcolato).

## Artefatti
- `scripts/quadratura/extract_f_carico.py` — esteso: join `L_ART_VAR_LOGIS` → `ART_RADICE_COD`/`ART_VAR_LOGIS_COD`
  nel file ODI (per il drill). Riuso dei tool esistenti (`compare_f_carico.py` per la logica di normalizzazione).
- `notebooks/gold/quadratura/quadratura_f_carico_misure.py` v1.0.0 — confronto su etichette comuni, grain
  configurabile, scrive `gold.logistica_dm.quadratura_f_carico_misure` (grain×misura → odi/gold/delta/match) +
  `quadratura_f_carico_copertura` (giorno×sito → n_odi/n_gold/n_comuni/%). Serverless, append per giorno.

## Flusso (snello)
1. Estrai CDT_DW.F_CARICO per giorno (`extract_f_carico.py`) → parquet (chiavi+6 misure+radice/variante).
2. Carica i file su Volume `/Volumes/landing_dev/logistica/files/quadratura/f_carico/cdtdw/AAAA/MM/GG/`.
3. Run notebook `quadratura_f_carico_misure` (dopo `gold_f_carico`) → tabelle risultati.
4. SAL: query/dashboard su `quadratura_f_carico_misure` (match% per giorno/misura) + copertura.

## Esito Fase 1 — MVP operativo (VALIDATO 2026-10-21) ✅
Estratti ODI 13-16/10 (radice/variante) → Volume `.../quadratura/f_carico/cdtdw/` → run notebook (serverless) =
SUCCESS → tabelle `gold_dev.logistica_dm.quadratura_f_carico_misure` (432 righe) + `..._copertura`.
**Risultati (13-16, etichette comuni)**:
- QTA_CARICO / QTA_UF_CARICO / PES_CARICO / VOL_CARICO = **100% match** (delta 0; VOL a meno di arrotondamento float).
- QTA_ORD_FORN 56,9% (OP-CAR-3 allocazione), VAL_COSTO_CARICO 44,4% (OP-CAR-1, gold=0) — scostamenti **noti**.
- **Copertura 97,5–98,7%** per giorno (dopo fix [[ACT_9033]]).
Fix notebook durante la validazione: `norm_sito`/`norm_num` con `.cast()` corretto; tolleranza MATCH **relativa**
(EPS_ABS 0,5 + EPS_REL 1e-5) per i volumi.

## Da fare (Fase 2 — sistema schedulato)
- Schedulare l'estrazione ODI giornaliera (relay/odi3, dove Oracle è raggiungibile) → Volume.
- Aggiungere il notebook come **task nel job** (dopo `gold_f_carico`) → tabelle aggiornate ogni giorno.
- (SAL) vista/dashboard sulla tabella risultati (match% per giorno/misura + copertura).
