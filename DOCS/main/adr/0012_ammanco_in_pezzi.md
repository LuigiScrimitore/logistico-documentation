# ADR-0012 · Ammanco (ordinato−ricevuto) calcolato in **pezzi**, unità omogenea

**Status**: accepted (2026-07-05)

**Contesto**:
L'aggregato `A_INBOUND_MENSILE` espone l'**ammanco** = quantità ordinata − ricevuta (misura di business,
NON scarto-di-record). La prima versione calcolava `AMMANCO = SUM(QTA_ORD_FORN) − SUM(QTA_CARICO)`
ottenendo un valore **negativo ed enorme** (−14.6M), non interpretabile. Indagando sui dati è emerso che
le due misure sono in **unità diverse**: `QTA_ORD_FORN` è in **colli/imballi**, `QTA_CARICO` è in
**pezzi** (`nrcolli × pzxcart`, dalle pesate). Sottrarle direttamente è un errore semantico (colli − pezzi).
Verifica al pezzo: `QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN == QTA_CARICO` sul campione (3×4=12, 19×10=190…);
a totale `SUM(ord×pzimb)=16.79M ≈ SUM(QTA_CARICO)=16.54M`.

**Alternative considerate**:
1. **Ammanco in colli** — riconvertire QTA_CARICO in colli (`/NUM_PZ_IMB`) — meno naturale: QTA_CARICO
   nasce in pezzi dalle pesate, la divisione introdurrebbe non interi/arrotondamenti.
2. **Ammanco in pezzi** — convertire l'ordinato in pezzi: `QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN`, omogeneo
   con `QTA_CARICO` (misura primaria del ricevuto).

**Decisione**:
`A_INBOUND_MENSILE.QTA_ORDINATA_TOT = SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN)` **in pezzi**; ammanco =
`QTA_ORDINATA_TOT − QTA_CARICO_TOT`. Risultato validato: **+253.243 pz = 1.51%** (sotto-consegnato
realistico). Rimossa la colonna morta `AMMANCO_QTA` da `silver.carico_dettaglio` (unità mista e per-riga:
l'ammanco è concetto di ordine/gruppo, vive solo in gold aggregato).

**Conseguenze**:
+ Ammanco interpretabile e coerente; `kpi_qualita_ricevimento` eredita la correzione.
+ Fissato il principio: **misure sottratte/confrontate devono essere nella stessa unità**.
− I nomi ODI `QTA_ORD_FORN` (colli) / `QTA_CARICO` (pezzi) restano per fedeltà/quadratura CDT_DW →
  l'unità è documentata nei **commenti colonna**; un eventuale rename fisico è rimandato (vedi OP-NAMING).

**Riferimenti**:
- Sezione ammanco/carichi: `07_certifica_gold_vs_cdtdw.md` §1.1, `13_registro_rename_gold_microstrategy.md` §D, `05_open_points.md` (OP-CAR-3).
- Codice: `notebooks/gold/aggregati/gold_a_inbound_mensile.py`, `notebooks/silver/carichi/silver_prep_carico.py` (commenti unità).
- Memory `odi-f-carico-grain-peso`. Collegate: ADR-0006 (grain/peso).
