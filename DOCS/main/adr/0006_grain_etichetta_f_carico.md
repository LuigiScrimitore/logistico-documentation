# ADR-0006 · Grain di F_CARICO = etichetta (fedele all'ODI), peso da anagrafica articolo

**Status**: accepted (2026-07-02)

**Contesto**:
La prima versione di `F_CARICO` era modellata come **testata ⋈ dettaglio** (grana "riga di dettaglio
carico"), un'ipotesi di comodo. Certificando la fact contro il legacy reale (PL/SQL ODI in
`DOCS/99. SCRIPT/CDT_SA.sql` / `CDT_ESTR.sql`) è emerso che il grain autentico di `CDT_DW.F_CARICO` è
**per etichetta di pesata** (`NUM_ETICH`), guidato dalle **PESATE**, non da testata⋈dettaglio. Inoltre
`PES_CARICO`/`VOL_CARICO` **non** derivano dalla pesata fisica ma dall'**anagrafica articolo**
(`LU_ART_UNITA_LOGISTICA`: `PESO_LORDO × QTA_UF`). Modellare male il grain significa quadrature sbagliate
e misure non confrontabili con l'as-is → la certificazione è un requisito, non un dettaglio.

**Alternative considerate**:
1. **Mantenere testata⋈dettaglio** — semplice ma **non fedele** all'ODI: numero righe e chiavi diversi
   da CDT_DW, quadratura impossibile, `PES/VOL` errati (presi dalla pesata fisica anziché anagrafica).
2. **Grain etichetta (fedele ODI)** — ricostruire la catena `V_CARICO_ORDINARIO → WL2→WL3→WL4→T_CARICO`
   con chiave `(MAG_SITO_COD, NUM_DOC_CARICO, NUM_ETICH, NUM_BOLLA_FORN)`, peso/volume da
   `LU_ART_UNITA_LOGISTICA`. Più oneroso ma corretto e quadrabile.

**Decisione**:
Grain **etichetta**. `silver_prep_carico` ricostruisce la catena ODI a grana etichetta (join
testata⋈dettaglio⋈**pesata**, driver `NUM_ETICH`); `PES_CARICO/VOL_CARICO` calcolati da
`LU_ART_UNITA_LOGISTICA` (utility `attach_carico_peso_volume`), **non** dalla pesata fisica. `gold_f_carico`
resta 2-notebook (ADR-0007): legge solo `silver.logistica_curated.carico`.

**Conseguenze**:
+ F_CARICO **quadrabile** vs CDT_DW (orphan-rate 0% in locale); misure allineate all'as-is.
+ Sblocca a valle A_INBOUND e i KPI qualità ricevimento con misure coerenti.
− Catena silver più complessa (ricostruzione WL). Dipendenza dall'estrazione di `LU_ART_UNITA_LOGISTICA`
  (2.67M righe) dal CDT_DW.
− `VAL_COSTO_CARICO` resta NULL (sorgente `cndstostock` dismessa 2020, OP-CAR-1) — fuori scope.

**Riferimenti**:
- Sezione carichi/grain: `07_certifica_gold_vs_cdtdw.md` §1.1 (F_CARICO) e `08_playbook_certifica_wave.md`.
- Codice: `notebooks/silver/carichi/silver_prep_carico.py`, `notebooks/gold/carichi/gold_f_carico.py`, `lib/logistica_utils/utils.py` (`attach_carico_peso_volume`).
- Memory `odi-f-carico-grain-peso`. Collegate: ADR-0007 (2-notebook), ADR-0012 (ammanco), OP-CAR-1/3/5.
