# ACT_8.4.1 · Esecuzione Cut-Over (step by step, timestamp/responsabile)

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.4
**Sprint**: 8.4 — Cut-Over & Stabilizzazione Post-Live
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ dipende dall'approvazione shadow mode e dai piani cut-over/rollback
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.3.1, ACT_8.3.2, ACT_8.3.3, ACT_8.3.4   **Blocca**: ACT_8.4.2
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: OP-25 (processo formale di go-live)

## Contesto e motivazione
È l'atto di go-live: si esegue il Cut-Over Plan (ACT_8.3.2) portando la produzione su Databricks,
registrando ogni step con timestamp e responsabile per tracciabilità e per un eventuale rollback
(ACT_8.3.1). Tutti i 12 pre-requisiti d'ingresso (`piani/cutover_plan.md` §1) devono essere firmati dal PM ≥ 48h
prima; se anche uno solo non è soddisfatto, il cut-over viene posticipato.

## Obiettivo
Cut-over eseguito secondo il piano, con log step-by-step (timestamp + responsabile). Fatto = produzione su
Databricks attiva entro la finestra prevista e tutti i go/no-go superati; comunicazione go-live inviata.

## Analisi tecnica
- **Sequenza operativa** (`piani/cutover_plan.md` §3, finestra sabato 22:00→02:00):
  - **T=22:00** freeze Oracle (DBA): `DB_PARMS`=FREEZE su Logistix/AtTraspo; verifica **0 job ODI running**.
  - **T=22:15** ultimo ciclo ODI sincrono (`CDT_SA.SP_CARICA_CDT_SYNC`, RetCod=0; ~30').
  - **T=22:30** backfill finale Databricks (`ops/backfill_completo.py`, run_date=oggi, force_reload):
    Bronze→Silver→Gold; nessun job FAILED.
  - **T=23:30** quadratura finale (`ops/quadratura_cutover.py`): CDT_DW (F_CARICO/F_STOCK/F_PREP_SPED) vs
    gold_prod; **delta < 0.5% su tutte le aree** (righe + misure) → BA notifica OK/KO.
  - **T=00:00** redirect MicroStrategy: DB instance `LOGISTICO_DWH_ORACLE`→`LOGISTICO_DWH_DATABRICKS` +
    invalidate cache (primo report < 60s).
  - **T=00:30** smoke test 15 check (§4): criterio 12/15 OK, **0 check critici ★ KO**.
  - **T=01:00** comunicazione go-live (ACT_8.3.3) + aggiornamento ticket stato = PRODUZIONE.
- **Criteri go/no-go per fase** (§5) e **matrice escalation** (§6): ogni fallimento ha primo contatto,
  timeout e azione (fino ad attivare il Rollback Plan ACT_8.3.1). Script di decisione go/no-go: se fix
  stimato < 30' e siamo prima delle 00:30 → tentare; altrimenti rollback.
- **Log**: registrare orario effettivo e responsabile per ogni step (tracciabilità + input a rollback).
- **Rollback pronto all'uso** (ACT_8.3.1): trigger T1…T5 automatici; procedura 6-step ~3h, da completare
  entro le 08:00. Delta `RESTORE` per pipeline (KIT-07) se necessario ripristinare dati.

## Sviluppo (diario)
- 2026-07-03 · attività pendente (go-live futuro).

## Verifica
- Tutti gli step del piano completati e **loggati** (timestamp + responsabile); quadratura finale < 0.5%;
  smoke test 12/15 con 0 critici KO; MicroStrategy su Databricks operativo; go-live confermato e comunicato.

## Esito
— (pendente)

## Follow-up
Subentra il presidio post-cutover (ACT_8.4.2). Se attivato rollback → post-mortem e condizioni re-go-live
(rollback_plan §8).
