# ACT_8.2.1 · Monitoraggio giornaliero quadrature (log anomalie)

**Status**: proposed
**Type**: dq
**Origin**: sprint 8.2
**Sprint**: 8.2 — Shadow Mode Run 10+ gg
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 4
**Blocco**: ☁️ richiede shadow mode attivo (sprint 8.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.4   **Blocca**: ACT_8.2.4
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0014_dq_alerting_interni]]   **OP collegati**: OP-24 (criteri accettazione parallel run)

## Contesto e motivazione
Durante il run shadow (**≥ 10 giorni lavorativi consecutivi**) le quadrature giornaliere vanno presidiate:
registrare i delta e loggare le anomalie è la base per misurare il criterio di sign-off (milestone
`fase_8.md` §6bis): **delta ≤ 0.1% su ≥ 95% dei giorni**, **orphan-rate 0.0%** (R-01), **Silver/Gold 0 FAIL**
(R-02/R-03).

## Obiettivo
Monitoraggio giornaliero delle quadrature con log anomalie. Fatto = per ogni giorno del run è tracciato il
delta per fact e le anomalie sono registrate; si può calcolare la percentuale di giorni entro soglia
(target ≥ 95% gg con delta ≤ 0.1%).

## Analisi tecnica
- **Input**: output della quadratura automatica (ACT_8.1.4) + DQ interno (KIT-03/04,
  `control_prod.etl.dq_results`, [[0014_dq_alerting_interni]]).
- **Serie storica**: costruire la serie dei delta giornalieri per fact (Q-01…Q-04: F_CARICO / F_GIACENZE /
  F_PREP_SPED / F_TRASPORTO) leggendo `dq_results` (già storicizza run_date + metric_value + threshold).
- **Presidio quotidiano**: ogni giorno del run verificare delta, orphan-rate, esiti smoke-test acceptance
  (KIT-02, `acceptance.py`: 7 famiglie di check → severità BLOCKING per grana/orphan/row_count, WARNING per
  misure/volume/SLA). Segnalare i giorni **fuori soglia** → risoluzione (ACT_8.2.2).
- **Metriche di accettazione** (milestone §6bis): oltre al delta 0.1%, tenere orphan-rate 0.0% e 0 FAIL
  Silver/Gold; verbalizzare i limiti noti (grain pesata OP-CAR-5, listini corrieri assenti — OP-24).
- **Alerting**: `Notifier` su fail (LogNotifier default; WebhookNotifier Teams/Slack in cloud, KIT-04).
- **Volume-anomaly** (`check_volume_anomaly`, max_dev_pct default 30%) come segnale complementare al delta.

## Sviluppo (diario)
- 2026-07-03 · in attesa di shadow mode attivo.

## Verifica
- Serie giornaliera dei delta disponibile per l'**intero run** (≥ 10 gg), per ciascun fact.
- Percentuale gg entro soglia (delta ≤ 0.1%) calcolabile; anomalie tracciate su `dq_results` e istradate a
  ACT_8.2.2.

## Esito
— (bloccato)

## Follow-up
Alimenta il report finale shadow (ACT_8.2.4). Anomalie ricorrenti → fix ACT_8.2.2 / ACT emergenti 9000+.
