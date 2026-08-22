# ACT_8.3.1 · Rollback Plan approvato

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.3
**Sprint**: 8.3 — Preparazione Cut-Over
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ finalizzazione/approvazione dipende dall'esito shadow mode
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.2.4   **Blocca**: ACT_8.4.1
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: OP-22 (SLA failure), OP-25 (processo go-live)

## Contesto e motivazione
Il cut-over necessita di un piano di rollback approvato: se il go-live PROD fallisce, deve esistere una
procedura sicura per tornare al flusso Oracle (ODI + MicroStrategy su Oracle DWH) senza perdita dati. Il
release-kit prevede già il meccanismo tecnico di rollback per pipeline (KIT-07, [[14_release_kit]] §3.H).
È pre-requisito #10 del `piani/cutover_plan.md` ("Rollback plan distribuito e letto dal team").

## Obiettivo
Rollback Plan approvato. Fatto = documento con trigger, passi, responsabilità (RACI) e verifica del
rollback, validato e approvato, distribuito e letto dal team di cut-over.

## Analisi tecnica
- **Bozza esistente**: `DOCS/piani/rollback_plan.md` v1.0 (2026-05-29), già strutturata (PARZ. 50%) —
  finalizzazione/approvazione dopo il sign-off shadow (ACT_8.2.4).
- **Contenuti del piano** (`piani/rollback_plan.md`):
  - **Trigger automatici** (rollback immediato): T1 delta KPI (>5% KPI con delta >1% vs Oracle),
    T2 report MicroStrategy non accessibili > 30 min, T3 workflow bronze/silver falliti > 2 cicli,
    T4 Delta corruption (`DELTA_INVALID`/`SNAPSHOT_NOT_FOUND`), T5 impatto operativo grave.
    **Trigger discrezionali** (PM+BA): T6 performance report > 3× baseline > 2h, T7 volume righe devia
    > 2%, T8 > 10 segnalazioni utente.
  - **RACI** (§3): PM = Accountable sulla decisione; Cloud Architect sospende workflow; DBA riabilita ODI;
    Team BI redirige MicroStrategy.
  - **Procedura 6 step** (§4, ~3h tot): 1) decisione+comunicazione (30'), 2) sospensione workflow
    Databricks — Pause degli 8 job `wf_*_daily` (15'), 3) riabilitazione scenari ODI `SCN_*_GIORNALIERO`
    (Enable, 30'), 4) verifica Oracle (query CDT_DW.F_CARICO/F_STOCK/F_PREP_SPED + 3 report MSTR, 60'),
    5) redirect MicroStrategy DB instance `LOGISTICO_DWH_DATABRICKS`→`LOGISTICO_DWH_ORACLE` + invalidate
    cache (30'), 6) comunicazione utenti (15').
  - **Verifica post-rollback**: checklist 10 punti (§6), entro le 08:00.
  - **Condizione abilitante**: mantenere Oracle ODI + DWH **operativi in parallelo ≥ 30 giorni** dopo il
    go-live (shadow post-cutover) — nesso con ACT_8.4.4 (ODI si **disabilita, non elimina**).
- **Aggancio tecnico release-kit** (KIT-07): per il rollback *dei dati* di una singola pipeline,
  Delta time-travel/`RESTORE TABLE … TO VERSION AS OF <v>`; annotare la versione Delta pre-cutover.
- **Coerenza** con runbook (ACT_8.1.5), cut-over plan (ACT_8.3.2) e spegnimento ODI (ACT_8.4.4).

## Sviluppo (diario)
- 2026-07-03 · bozza `piani/rollback_plan.md` (PARZ. 50%).

## Verifica
- Il piano definisce trigger di attivazione, sequenza 6-step con durate, RACI e checklist post-rollback.
- **Approvazione formale** registrata (firme condizioni re-go-live §8: PM, Responsabile Business, Cloud
  Architect, BA); documento distribuito e **letto** da tutti i partecipanti al cut-over (pre-req. #10
  cutover_plan).

## Esito
— (parziale: bozza in corso)

## Follow-up
Compilare contatti di emergenza (§7, oggi placeholder). Definire SLA failure (OP-22).
