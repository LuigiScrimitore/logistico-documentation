# ACT_5.3.4 · Quadratura vs Oracle (QTA_CONSEGNATA, COSTO_EUR)

**Status**: in-progress
**Type**: dq
**Origin**: sprint 5.3
**Sprint**: 5.3 — Gold F_ORDINI & F_TRASPORTO
**Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD + accesso Oracle (sorgente di confronto)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_5.3.1, ACT_5.3.2   **Blocca**: certificazione Gold trasporti
**ADR collegate**: ADR-0013 (F_TRASPORTO grana MTV), ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto e motivazione
I fact F_ORDINI/F_TRASPORTO sono pronti (23k F_TRASPORTO nel big re-run) ma vanno quadrati contro Oracle prima di poter essere certificati. Senza cloud + accesso Oracle la quadratura dati non è eseguibile. Vedi [`../sprint_agile/sprint_5.3.md`](../sprint_agile/sprint_5.3.md) (5.3.4: "richiede cloud+Oracle").

**Stato certificazione strutturale (già fatto, offline, 2026-07-05)** — vedi [`../07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md) §1.3/§1.5:
- **F_TRASPORTO**: certificato a grana **MTV** ([[adr/0013_scope_trasporti_mtv]]). In CDT_DW i trasporti sono una gerarchia a 3 grane (`F_TRASP_MTV` + `F_TRASP_TRATTA` + `F_TRASP_TRATTA_BOLLA`); il nostro `gold_f_trasporto` modella solo `F_TRASP_MTV` (scelta deliberata: TRATTA/BOLLA non sono in landing e il loro valore = costo tratta, fuori scope).
- **F_ORDINI**: scope **fornitore** (`F_ORD_FORN`, non `F_ORD_SOCI`); nessuna controparte diretta piena → certifica **indiretta** via F_CARICO (`SUM(QTA_ORD_FORN)`).

Resta quindi la **quadratura dati vs Oracle** (cloud-gated).

## Obiettivo
Quadratura Gold vs Oracle entro tolleranza concordata, con delta documentato e motivato. Fatto = report per misura sotto soglia (o scostamenti spiegati).

⚠️ **Nota misure**: **COSTO_EUR non è valorizzato realmente** — i listini corrieri sono assenti (fase_5 §Punti aperti); `COSTO_STIMATO_EUR` è un placeholder (`peso*0.15`, vedi `sql/kpi/gold_kpi_costo_trasporto.sql`) → la quadratura del costo è **non applicabile** finché non arrivano i listini. Analogamente **QTA** su trasporti/ordini è disponibile solo come **PROXY** (OP-27: F_ORDINI non porta qta ordinate/consegnate, sono nel dettaglio carico). Rivedere con il BA la lista misure effettivamente quadrabili.

## Analisi tecnica
- **Script**: `scripts/quadratura/quadratura_fact.py` (parametrico `--fact`), che legge Oracle READ-ONLY e il Gold via **pandas/pyarrow** (no Spark; legge solo i file Delta *live* add−remove dal `_delta_log`, cfr. memoria `delta-tombstone-pyarrow-read`). ⚠️ Oggi il dict `FACTS` copre **solo `CARICO` e `PREP_SPED`**: per questa ACT va **esteso** con le entry `TRASPORTO` (→ `CDT_DW.F_TRASP_MTV`) ed eventualmente l'indiretta ordini.
- **Grain di confronto F_TRASPORTO** ([[adr/0013_scope_trasporti_mtv]]): `(SITO, GIORNO_BOLLA_SPED)` con COUNT + SUM KM (vedi 07 §1.3 "Quadratura MTV"). Partizione Gold `GIORNO_BOLLA_SPED_ID`.
- **Mapping SITO** (P-01, risolto): `MAG_SITO_COD` CDT_DW (es. `0005C`) → codice canonico Gold (`05`) via `CDT_ESTR.S_LOGISTIX` (FLAG_ATTIVO=1), `int(cifre)` + zero-pad 2 → `build_sito_map()`. Cfr. memoria `sito-mapping-slogistix`.
- **Mapping date** (P-02): le fact CDT_DW usano FK surrogate `GIORNO_*_ID` → JOIN `CDT_DW.L_GIORNO`; oppure colonne YYYYMMDD dirette. Gestito nello script.
- **Finestra dati** (P-03): landing dal **2026-06-09**; usare `--da/--a` nella finestra coperta. **Soglia** (P-04) default 1%, 5% per il primo run.
- **F_ORDINI indiretta**: quadratura via F_CARICO (`SUM(QTA_ORD_FORN)`) — vedi 07 §1.5.
- Connessione Oracle: `.env` in `scripts/landing_simulator/` (stesse credenziali del cdtdw extractor).

## Sviluppo (diario)
- 2026-07-03 · PARZIALE ~20%; bloccato su cloud + accesso Oracle.

## Verifica
- `python scripts/quadratura/quadratura_fact.py --fact TRASPORTO --discover` per validare le colonne di `F_TRASP_MTV`.
- `python scripts/quadratura/quadratura_fact.py --fact TRASPORTO --da 2026-06-09 --a 2026-06-21 --soglia 5.0` → report `(SITO, GIORNO_BOLLA_SPED)` con delta COUNT/misure; exit 0 = OK.
- Report con delta per misura sotto soglia; scostamenti (COSTO/QTA proxy) documentati come attesi.

## Esito
— (in attesa di cloud/PROD e accesso Oracle)

## Follow-up
- Estensione del dict `FACTS` in `quadratura_fact.py` con `TRASPORTO` (e indiretta ordini) → eventuale ACT emergente 9000+.
- Sblocco quadratura COSTO trasporto vincolato all'arrivo dei **listini corrieri** (dipendenza esterna cliente).
