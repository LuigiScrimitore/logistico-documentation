# ACT_8.2.4 · Report finale Shadow Mode (sign-off)

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.2
**Sprint**: 8.2 — Shadow Mode Run 10+ gg
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ dipende dall'esito del run shadow (ACT_8.2.1/8.2.2)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.2.1, ACT_8.2.2, ACT_8.2.3   **Blocca**: ACT_8.3.1, ACT_8.3.2
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0014_dq_alerting_interni]]   **OP collegati**: OP-24 (criteri accettazione), OP-25 (processo formale di go-live)

## Contesto e motivazione
Il passaggio al cut-over richiede un **sign-off formale** sull'esito dello shadow mode: il report finale
riassume le quadrature del run e certifica il raggiungimento dei criteri di accettazione. È il documento
che sblocca la preparazione cut-over (ACT_8.3.1/8.3.2) e alimenta il processo formale di go-live (OP-25) e
il pre-requisito #1 del `piani/cutover_plan.md` (shadow ≥ 10 gg con report delta).

## Obiettivo
Report finale Shadow Mode con sign-off. Fatto = report compilato con i risultati del run e approvazione a
procedere con la preparazione cut-over (sprint 8.3).

## Analisi tecnica
- **Template report già pronto** (PARZ. 50%); da popolare con:
  - la **serie delta giornaliera** per fact dal monitoraggio (ACT_8.2.1, `control_prod.etl.dq_results`);
  - l'esito dei **fix** (ACT_8.2.2) e dello **stress test** late-arrival/idempotenza (ACT_8.2.3, V-04).
- **Criteri di accettazione da certificare** (milestone `fase_8.md` §6bis, [[0014_dq_alerting_interni]]):
  - **delta ≤ 0.1% su ≥ 95% dei giorni** shadow (target D-06);
  - **orphan-rate 0.0%** (R-01); **Silver/Gold 0 FAIL** (R-02/R-03);
  - **limiti noti verbalizzati** con criteri di tolleranza (OP-24): grain pesata (OP-CAR-5), listini
    corrieri assenti → costi trasporto non valorizzati ([[0013_scope_trasporti_mtv]]).
- **Nota soglie**: il criterio di sign-off shadow è 0.1%; il `piani/cutover_plan.md` (pre-requisito #1) parla di
  delta < 0.5% su 10 gg per l'ingresso al cutover — il report deve rendere espliciti entrambi.
- **Sign-off**: firme richieste (rif. `piani/cutover_plan.md` pre-req. #3/#4): **PM Progetto** + **BA Funzionale**
  (email di approvazione). Formalizzare il processo di go-live con Reply (OP-25).

## Sviluppo (diario)
- 2026-07-03 · template report pronto (PARZ. 50%); dati assenti finché lo shadow mode non gira.

## Verifica
- Report contiene la serie giornaliera dei delta per fact e la valutazione dei criteri (≥ 95% gg ≤ 0.1%,
  orphan 0.0%, 0 FAIL) + i limiti noti verbalizzati.
- **Sign-off registrato** (email PM + BA) → sblocca sprint 8.3.

## Esito
— (parziale: template pronto, dati in attesa del run)

## Follow-up
Formalizzare con Reply il processo di go-live (OP-25). Il report è pre-requisito d'ingresso del
`piani/cutover_plan.md`.
