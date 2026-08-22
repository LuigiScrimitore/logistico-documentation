# ACT_6.3.2 · Validazione funzionale CE178 e carrellisti

**Status**: proposed
**Type**: analysis
**Origin**: sprint 6.3
**Sprint**: 6.3
**Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD (richiede dati reali) · compliance CE178
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_6.3.1 (workflow deployato)   **Blocca**: chiusura FASE 6
**ADR collegate**: ADR-0014 (DQ interni)   **OP collegati**: —

## Contesto e motivazione
I fact e le viste di Wave E (tracciabilità CE178 e carrellisti) vanno validati funzionalmente su
dati reali prima della chiusura di fase, con particolare attenzione alla **conformità CE178**
(requisito legale food-safety: catena lotto ricevimento→spedizione ricostruibile). Dipende da
[[ACT_6.3.1_workflow-logistica-wave-e]] (pipeline orchestrate e Gold prodotti). La validazione
richiede PROD e non è eseguibile sul locale. Dettaglio in
[`../sprint_agile/sprint_6.3.md`](../sprint_agile/sprint_6.3.md); punto aperto **V-06** in
[`../milestones/fase_6.md`](../milestones/fase_6.md) §7.

## Obiettivo
Validazione funzionale di CE178 (conformità) e carrellisti (KPI produttività) su dati reali.
Fatto = quadrature/controlli documentati e **conformità CE178 (V-06) confermata** su PROD.

## Analisi tecnica
**CE178 — compliance (V-06):**
- Fact reale: **`gold_f_tracciabilita_lotti`** (grana etichetta CE178: `SITO_COD, CARICO_NRO, MSI_COD, DATA_CARICO`; controparte CDT_DW `F_TRACC`, cfr. [`../07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md) §1.8).
- Verificare la **completezza campi CE178** e la ricostruibilità della catena lotto ricevimento→spedizione (requisito legale). Attese di business: lotti scaduti con residuo. Riferimento analisi: `DOCS/Archive/mapping_ce178.md`.
- Il decode A0-A2 (2026-07-05) ha confermato grana etichetta coerente; la verifica compliance su dati reali è **cloud/BA-gated**.

**Carrellisti — KPI produttività:**
- Fact reale: **`gold_f_movimentazione_carrellisti`** (v3.1) — ⚠️ non `gold_f_turno`. Grana `CARRELLISTA_COD × DATA_PRESENZA × SITO_COD`.
- Misure reali (OP-27): `NUM_MISSIONI`, `NUM_CARICHI`, `NUM_RIEPILOGHI`, `ORE_PRESENZA`, `ORA_LOGIN/LOGOUT`, `DURATA_TOT_MIN`, **`NUM_PLT_MOVIMENTATI`** (pallet movimentati/giorno, `2 se DOPPIO_MOVIM='SI'`, allineata a `F_MOV_CARR.NUM_PLT_MOV_CARR`, 07 §1.7). ⚠️ **Il Silver sessione NON ha `ORE_PRODUTTIVE`** (il cartellino non ha pause/riunioni) e non esiste `TIPO_MISSIONE`: validare la produttività su `NUM_MISSIONI`/`NUM_PLT_MOVIMENTATI` vs `ORE_PRESENZA`, non su `ORE_PRODUTTIVE`. Riferimento analisi: `DOCS/Archive/mapping_carrellisti.md`.
- Missioni/ora come rapporto `NUM_MISSIONI / ORE_PRESENZA` (proxy produttività).

- Appoggio ai **DQ interni** ([[adr/0014_dq_alerting_interni]]) per i controlli automatici.
- ⏳ Richiede PROD + dati reali: attività pendente.

## Sviluppo (diario)
- 2026-07-03 · pendente: richiede PROD e compliance su dati reali.

## Verifica
- **CE178 (V-06)**: catena lotto ricostruibile end-to-end su dati reali; campi CE178 completi; lotti scaduti con residuo intercettati. Sign-off compliance.
- **Carrellisti**: KPI (`NUM_MISSIONI`, `NUM_PLT_MOVIMENTATI`, `ORE_PRESENZA`, missioni/ora) coerenti con le attese operative; sanity vs `F_MOV_CARR`.
- Quadrature funzionali documentate; DQ interni verdi.

## Esito
— (pendente, richiede PROD)

## Follow-up
Eventuali fix emersi dalla validazione → ACT emergenti 9000+.
