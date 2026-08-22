# ACT_GATE-2 · Gate cloud FASE 2 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 2 — Wave A Carichi
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (I-02) + GATE-1 (dimensioni)
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 2 (done offline), [[ACT_GATE-1]], [[ACT_2.1.6]] (backfill), [[ACT_2.3.4]] (quadratura)   **Blocca**: chiusura reale FASE 2
**ADR collegate**: ADR-0006, ADR-0009, ADR-0010, ADR-0017   **OP collegati**: OP-24, Q-01

## Contesto e motivazione
FASE 2 (Carichi) è **done offline** (F_CARICO ricostruito a grain etichetta [[ACT_9001]], ammanco [[ACT_9002]]).
Gate per portarla al "done reale" in cloud secondo la *Definition of Done di fase* ([`README.md`](README.md)).

## Obiettivo
Pacchetto Carichi deployato in Azure TEST, backfill storico eseguito, workflow schedulato stabile, F_CARICO
certificato vs CDT_DW.

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_carichi.yml` (bronze→silver→gold→[+DQ da aggiungere, [[ACT_9010]]]).
- **Backfill**: storico 22 siti ([[ACT_2.1.6]]).
- **Certificazione**: `quadratura_fact.py --fact CARICO` vs `CDT_DW.F_CARICO` (Q-01) — SUM `QTA_CARICO`/`PES_CARICO`,
  mapping sito S_LOGISTIX; residui PESO_LORDO/grain in [[ACT_9000]].
- Compute serverless da allineare [[ACT_9007]].

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali (OP-24).
3. **Qualità**: DQ verdi (orphan 0.0%, 0 FAIL).
4. **Dati certificati**: quadratura F_CARICO entro 1% (o divergenze documentate).

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_2.md`. Promozione PROD → [[ACT_GATE-PROD]].
