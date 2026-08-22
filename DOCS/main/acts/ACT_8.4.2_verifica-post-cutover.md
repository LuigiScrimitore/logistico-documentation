# ACT_8.4.2 · Verifica post-cut-over D+0, D+1 (monitoring 4h)

**Status**: proposed
**Type**: dq
**Origin**: sprint 8.4
**Sprint**: 8.4 — Cut-Over & Stabilizzazione Post-Live
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 2
**Blocco**: ☁️ dipende dall'esecuzione cut-over (ACT_8.4.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.4.1   **Blocca**: ACT_8.4.4
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0014_dq_alerting_interni]]   **OP collegati**: OP-22 (SLA failure)

## Contesto e motivazione
Subito dopo il go-live serve un presidio intensivo su D+0 e D+1 per intercettare regressioni o anomalie di
quadratura prima di dichiarare la stabilizzazione e spegnere ODI (ACT_8.4.4). Include il **presidio
notturno post-go-live** del `piani/cutover_plan.md` (§3, 02:00–08:00, verifica dashboard ogni 30', 5 KPI alle
06:00, report per la riunione delle 08:00).

## Obiettivo
Verifica post-cut-over su D+0 e D+1 completata. Fatto = quadrature e job PROD verificati nei primi due
giorni senza anomalie bloccanti aperte.

## Analisi tecnica
- **Presidio notturno D+0** (cutover_plan §3): Cloud Architect connesso 02:00–08:00; verifica Dashboard
  Databricks (workflow, alert) ogni 30'; verifica manuale 5 KPI principali in MicroStrategy alle 06:00;
  report go-live per riunione 08:00.
- **Monitoring 4h su D+0 e D+1**: presidio dedicato sui primi run schedulati giornalieri; quadratura
  automatica (ACT_8.1.4) + DQ interno (`control_prod.etl.dq_results`, [[0014_dq_alerting_interni]]) — in
  post-live la severità di quadratura può tornare **BLOCKING**/alerting attivo (WebhookNotifier).
- **Trigger di rollback attivi** (rollback_plan §2): monitorare T1 (delta KPI), T2 (report non
  accessibili > 30'), T3 (workflow falliti > 2 cicli), T7 (volume righe devia > 2%). Escalation immediata
  su anomalia (matrice cutover_plan §6 / runbook ACT_8.1.5).
- **Riuso**: runbook (ACT_8.1.5) per procedure di ripartenza; smoke-test acceptance (KIT-02) sui fact.

## Sviluppo (diario)
- 2026-07-03 · attività pendente.

## Verifica
- Quadrature D+0/D+1 entro soglia; job schedulati OK (nessun FAILED); 5 KPI MicroStrategy verificati.
- Nessuna anomalia **bloccante** aperta → precondizione per lo spegnimento ODI (ACT_8.4.4).

## Esito
— (pendente)

## Follow-up
Se emergono anomalie non bloccanti → istradare al supporto post-live (ACT_8.4.3). Aggiornare runbook con i
timing reali.
