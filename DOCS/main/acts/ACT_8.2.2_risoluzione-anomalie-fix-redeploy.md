# ACT_8.2.2 · Risoluzione anomalie (fix + redeploy CI/CD)

**Status**: proposed
**Type**: fix
**Origin**: sprint 8.2
**Sprint**: 8.2 — Shadow Mode Run 10+ gg
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 4
**Blocco**: ☁️ richiede anomalie rilevate dal monitoraggio (ACT_8.2.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.2.1   **Blocca**: ACT_8.2.4
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0016_multi_repo_gitlab]], [[0014_dq_alerting_interni]]   **OP collegati**: —

## Contesto e motivazione
Le anomalie di quadratura rilevate durante lo shadow mode (ACT_8.2.1) vanno corrette e ridistribuite in
PROD via CI/CD, finché i delta non rientrano stabilmente sotto soglia (≤ 0.1%) per abilitare il sign-off
(ACT_8.2.4). È il ciclo iterativo fix→redeploy→verifica che porta lo shadow al criterio di go/no-go.

## Obiettivo
Anomalie risolte con fix e redeploy tramite CI/CD. Fatto = i giorni fuori soglia sono indagati, corretti e
la fix è deployata in PROD; il delta del fact interessato rientra entro 0.1% nei giorni successivi.

## Analisi tecnica
- **Input**: giorni/fact fuori soglia da `dq_results` e dalla serie delta (ACT_8.2.1).
- **Triage**: distinguere anomalie **strutturali** (bug pipeline: grana, join, mapping sito
  `MAG_SITO_COD`→`SITO_COD`, LAD) da **limiti noti verbalizzati** (grain pesata OP-CAR-5, listini corrieri
  assenti → costi trasporto non valorizzati, [[0013_scope_trasporti_mtv]]) che **non** si "fixano" ma si
  documentano nel report (ACT_8.2.4).
- **Fix & redeploy** (multi-repo GitLab, [[0016_multi_repo_gitlab]], [[11_devops_handoff_databricks]]
  FASI B/C):
  - modifica su notebook/pipeline (`logistico-workflows`) o lib (`logistico-lib`) su feature branch → MR;
  - `databricks bundle validate/deploy -t prod` (KIT-06); ogni fix tracciata su commit.
- **Rollback pipeline se un deploy peggiora** (KIT-07, [[14_release_kit]] §3.H): Delta `RESTORE TABLE … TO
  VERSION AS OF <v_buona>` sulla tabella toccata.
- **Verifica idempotenza** dopo il fix (KIT-07): 2 run stesso `run_date` → stesse righe/SUM (crescita ⇒
  MERGE key errata).
- Bug significativi → **ACT emergenti 9000+** dedicate.

## Sviluppo (diario)
- 2026-07-03 · in attesa di anomalie dal run shadow.

## Verifica
- Dopo il redeploy la quadratura del fact interessato rientra sotto soglia (≤ 0.1%) nei giorni successivi
  e resta stabile fino a fine run.
- Nessuna anomalia strutturale aperta al momento del sign-off (ACT_8.2.4).

## Esito
— (bloccato)

## Follow-up
Possibili ACT emergenti 9000+ per singole anomalie. Learnings confluiscono nel runbook (ACT_8.1.5) e nel
report shadow (ACT_8.2.4).
