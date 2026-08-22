# ACT_GATE-4 · Gate cloud FASE 4 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 4 — Wave C Prep Spedizioni
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (I-02) + GATE-1
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 4 (done offline), [[ACT_GATE-1]], [[ACT_4.3.6]] (quadratura)   **Blocca**: chiusura reale FASE 4
**ADR collegate**: ADR-0009, ADR-0010, ADR-0017   **OP collegati**: OP-24, OP-33 (grain), Q-03

## Contesto e motivazione
FASE 4 (Prep Spedizioni) è **done offline** (F_PREP_SPED v4 grain 9 chiavi, F_TURNO_PREP_SITO). Gate per il
"done reale" in cloud (DoD di fase, [`README.md`](README.md)).

## Obiettivo
Pacchetto Prep Spedizioni deployato in TEST, workflow schedulato stabile, F_PREP_SPED/F_TURNO certificati.

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_prep_sped.yml` (cron 04:30) — include anche i **carrellisti** (vedi [[ACT_9008]]).
- **Certificazione**: `quadratura_fact.py --fact PREP_SPED` (Q-03) — SUM `QTA_PREP`/`VAL_PREP_CES`/`VAL_PREP_VEN`
  per `(SITO, data)`; nota asimmetria SCARTATE (OP-PSP-1, sempre 0 ODI vs N Gold). F_TURNO_PREP_SITO: config
  TURNO da aggiungere a `quadratura_fact.py` ([[ACT_9009]]).
- Compute serverless da allineare [[ACT_9007]]; task DQ [[ACT_9010]].

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali.
3. **Qualità**: DQ verdi.
4. **Dati certificati**: quadratura F_PREP_SPED / F_TURNO entro soglia (o divergenze documentate).

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_4.md`. Promozione PROD → [[ACT_GATE-PROD]].
