# ACT_GATE-5 · Gate cloud FASE 5 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 5 — Wave D Trasporti
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (I-02) + GATE-1
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 5 (done offline), [[ACT_GATE-1]], [[ACT_5.3.4]] (quadratura)   **Blocca**: chiusura reale FASE 5
**ADR collegate**: ADR-0009, ADR-0010, ADR-0013 (F_TRASPORTO MTV), ADR-0017   **OP collegati**: OP-24, OP-27 (KPI proxy), Q-04

## Contesto e motivazione
FASE 5 (Trasporti/Ordini) è **done offline** (F_ORDINI scope fornitore, F_TRASPORTO grana MTV — ADR-0013).
Gate per il "done reale" in cloud (DoD di fase, [`README.md`](README.md)).

## Obiettivo
Pacchetto Trasporti deployato in TEST, workflow schedulato stabile, F_ORDINI/F_TRASPORTO certificati.

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_trasporti.yml` (cron 05:00; silver ordini/trasporti/swap/costo → gold).
- **Certificazione**: F_TRASPORTO vs `CDT_DW.F_TRASP_MTV` (Q-04) — grain `(SITO, GIORNO_BOLLA_SPED)`, SUM KM;
  **config TRASPORTO da aggiungere a `quadratura_fact.py`** ([[ACT_9009]]). `COSTO_EUR` non valorizzato
  (listini corrieri assenti) → escluso dalla soglia; KPI = proxy OP-27 (da esplicitare).
- Compute serverless da allineare [[ACT_9007]].

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali.
3. **Qualità**: DQ verdi.
4. **Dati certificati**: quadratura F_TRASPORTO (MTV) entro soglia; COSTO escluso e documentato.

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_5.md`. Promozione PROD → [[ACT_GATE-PROD]].
