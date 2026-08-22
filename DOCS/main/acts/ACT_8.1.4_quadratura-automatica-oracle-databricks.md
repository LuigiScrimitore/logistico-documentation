# ACT_8.1.4 · Quadratura automatica giornaliera Oracle vs Databricks

**Status**: in-progress
**Type**: dq
**Origin**: sprint 8.1
**Sprint**: 8.1 — Shadow Mode Setup
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ richiede shadow mode attivo (ACT_8.1.3)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.3   **Blocca**: ACT_8.2.1
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0014_dq_alerting_interni]], [[0005_no_secret_oracle_export_landing]], [[0013_scope_trasporti_mtv]]   **OP collegati**: OP-24 (criteri accettazione parallel run)

## Contesto e motivazione
Lo shadow mode confronta ogni giorno l'output Databricks con Oracle (CDT_DW). Serve un check di quadratura
**automatico** che calcoli i delta per fact/misura e logghi le anomalie, così da misurare il criterio di
sign-off (**delta ≤ 0.1% su ≥ 95% dei giorni** — milestone `fase_8.md` §6bis, target D-06; sprint 8.2).

## Obiettivo
Quadratura automatica giornaliera Oracle vs Databricks che produce delta e log anomalie. Fatto = job di
confronto gira ad ogni ciclo e scrive un report/tabella di quadratura consumabile dal monitoraggio (ACT_8.2.1).

## Analisi tecnica
- **Strumento**: `scripts/quadratura/quadratura_fact.py` (parametrico per fact, confronto sito×periodo vs
  CDT_DW) + `quadratura_f_carico.py`. Su Databricks gira **Spark-native** (`spark.table` su `gold_prod.
  logistica.*`): nessun problema tombstone (il pyarrow+`live_delta_files()` hack resta solo per il locale,
  [[10_piano_migrazione_databricks]] §4.4, [[0014_dq_alerting_interni]]).
- **Lettura legacy CDT_DW** (D5, [[0005_no_secret_oracle_export_landing]]): via **export su landing**
  (CSV letto con `spark.read`), non JDBC diretto. L'export Oracle è READ-ONLY.
- **Quadrature in scope** (milestone §6bis): Q-01…Q-04 su **F_CARICO / F_GIACENZE / F_PREP_SPED /
  F_TRASPORTO**. Nota: F_TRASPORTO è scope MTV deliberato ([[0013_scope_trasporti_mtv]]); listini corrieri
  assenti → costi trasporto non valorizzati (limite da verbalizzare, OP-24).
- **Collegamento al DQ interno** (KIT-03/04, `lib/logistica_utils/dq_monitor.py`, [[14_release_kit]] §3.F):
  esiti su `control_prod.etl.dq_results` (schema: run_id, env, pipeline, layer, table_name, check_name,
  **severity**, passed, metric_value, threshold, run_date…). Severità: quadratura fuori soglia = **WARNING**
  in shadow (non blocca il run shadow), diventa criterio di go/no-go al cut-over. `gate()` + `Notifier`
  (LogNotifier ora; WebhookNotifier Teams/Slack da attivare in cloud, KIT-04).
- **Chiavi/misure e soglia**: per ogni fact definire chiave di confronto (grana) e misure (es. F_CARICO:
  righe + `qta_ricevuta`/`PES_CARICO`; F_PREP_SPED: righe + `num_imb_nuco_prep`; F_GIACENZE: righe +
  `qta_disponibile`). Soglia delta **0.1%** per il sign-off shadow; il cutover_plan usa 0.5% come soglia di
  quadratura finale della notte (più permissiva, contesto diverso).
- **Stato**: logica di confronto **già scritta offline** (PARZ. 50%); esecuzione reale possibile solo con
  shadow mode attivo (ACT_8.1.3).

## Sviluppo (diario)
- 2026-07-03 · logica di quadratura scritta; manca l'ambiente shadow per eseguirla (PARZ. 50%).

## Verifica
- Run giornaliero produce delta per fact (righe + misure) e li storicizza su `dq_results`.
- Anomalie loggate con severità; soglia 0.1% valutabile su base giornaliera per il conteggio "gg entro
  soglia" (ACT_8.2.1).
- Almeno un ciclo end-to-end confrontato con Oracle export per tutti i fact Q-01…Q-04.

## Esito
— (parziale: logica pronta, esecuzione in attesa di shadow mode)

## Follow-up
Verbalizzare con Reply i criteri di tolleranza (OP-24): grain pesata (OP-CAR-5) e listini corrieri assenti.
Attivazione `WebhookNotifier` in cloud (KIT-04).
