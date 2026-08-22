# ACT_8.1.5 · Runbook operativo PROD

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.1
**Sprint**: 8.1 — Shadow Mode Setup
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: nessuno (finalizzazione dipende da PROD attivo)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.3   **Blocca**: —
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0014_dq_alerting_interni]], [[0010_incrementale_watermark_pattern2_pruning]]   **OP collegati**: OP-22 (SLA di risposta ai failure)

## Contesto e motivazione
Il presidio PROD (schedule, ripartenze, gestione errori, escalation) richiede un runbook operativo che
permetta al team di condurre lo shadow mode e il post-live in autonomia. È il documento a cui il presidio
si appoggia in ACT_8.4.2 (monitoring D+0/D+1) e ACT_8.4.3 (supporto post-live), e che formalizza gli SLA
di risposta ai failure (OP-22, ancora aperto in milestone `fase_8.md` §7).

## Obiettivo
Runbook operativo PROD completo e utilizzabile. Fatto = procedure per avvio/monitoraggio/ripartenza job,
gestione anomalie ed escalation documentate, validate con una prova a tavolino.

## Analisi tecnica
- **Bozza esistente** in `DOCS/runbook.md` (PARZ. 50%).
- **Contenuti da coprire**:
  - **Schedule & trigger**: SLA push 04:00 → landing check 04:30 → primo processing 05:00
    ([[12_checklist_infra_setup]] C4); trigger file-arrival/schedule sul Volume landing.
  - **Avvio/ripartenza job**: run manuale con job parameters (`env=prod`, `run_date`, `full_refresh`);
    ordine DAG dim→fact→aggregati ([[14_release_kit]] §2); comportamento incrementale/watermark
    ([[0010_incrementale_watermark_pattern2_pruning]]).
  - **Gestione anomalie**: lettura `control_prod.etl.dq_results`, severità INFO/WARNING/**BLOCKING**,
    `gate()` che ferma il job su BLOCKING ([[0014_dq_alerting_interni]], KIT-03/04); alerting via
    LogNotifier/WebhookNotifier.
  - **Late-arrival / ritardo sorgente**: recupero al ciclo successivo (rif. stress test ACT_8.2.3).
  - **Rollback per pipeline** (KIT-07, [[14_release_kit]] §3.H): annotare la **versione Delta pre-run** di
    ogni tabella toccata; `DESCRIBE HISTORY` → `RESTORE TABLE … TO VERSION AS OF <v>`; su tabelle
    partizionate preferire `replaceWhere`.
  - **Escalation & SLA** (OP-22): matrice chi-chiamare (riusare la matrice del `piani/cutover_plan.md` §6 e del
    `piani/rollback_plan.md` §7 come base per il presidio ordinario).
- **Integrazioni**: procedure di quadratura (ACT_8.1.4), rollback go-live (ACT_8.3.1), cut-over
  (ACT_8.3.2 / ACT_8.4.1). Questo runbook è per il **presidio ordinario/shadow**; i piani straordinari di
  cut-over e rollback restano documenti a sé.

## Sviluppo (diario)
- 2026-07-03 · bozza `DOCS/runbook.md` avviata (PARZ. 50%).

## Verifica
- Il runbook copre i casi operativi principali (avvio, ripartenza, anomalie DQ, late-arrival, rollback
  pipeline, escalation) ed è validato con una **prova a tavolino** sul flusso PROD con gli attori coinvolti.

## Esito
— (parziale: bozza in corso)

## Follow-up
Definire con Reply gli SLA di risposta ai failure (OP-22). Aggiornare dopo il primo run reale con i timing
effettivi.
