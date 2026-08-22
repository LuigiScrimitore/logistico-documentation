# ACT_GATE-3 · Gate cloud FASE 3 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 3 — Wave B Giacenze
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (I-02) + GATE-1
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 3 (done offline), [[ACT_GATE-1]], [[ACT_3.3.6]] (quadratura)   **Blocca**: chiusura reale FASE 3
**ADR collegate**: ADR-0009, ADR-0010, ADR-0017   **OP collegati**: OP-24, OP-29 (ordering), Q-02, ST-01 (VAL_STOCK)

## Contesto e motivazione
FASE 3 (Giacenze) è **done offline**. Gate per il "done reale" in cloud (DoD di fase, [`README.md`](README.md)).
In cloud il DAG risolve l'ordering `silver_catena_unificata`→`silver_t_stock` (OP-29 è fisiologico solo in locale).

## Obiettivo
Pacchetto Giacenze deployato in TEST, workflow schedulato stabile, F_GIACENZE_DAILY certificato.

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_giacenze.yml` (cron 03:30; bronze snapshot → silver → gold daily).
- **Certificazione**: quadratura vs `CDT_DW.F_STOCK` (Q-02) — SUM giacenza per `(SITO, DATA_FOTO)`; **config
  GIACENZE da aggiungere a `quadratura_fact.py`** ([[ACT_9009]]); misure reali `QTA_PEZZI`/`QTA_UF` (non
  `QTA_DISPONIBILE`); `VAL_STOCK`=0 gap noto ([[ACT_ST-01]]).
- Compute serverless da allineare [[ACT_9007]].

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali; F_GIACENZE_DAILY scrive righe ogni giorno.
3. **Qualità**: DQ verdi.
4. **Dati certificati**: quadratura giacenze entro soglia (VAL_STOCK escluso, documentato).

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_3.md`. Promozione PROD → [[ACT_GATE-PROD]].
