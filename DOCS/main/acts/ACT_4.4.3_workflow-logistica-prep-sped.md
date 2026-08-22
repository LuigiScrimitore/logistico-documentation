# ACT_4.4.3 · Workflow logistica_prep_sped (04:30)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 4.4
**Sprint**: 4.4 — KPI Picking & Workflow
**Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)
**Gg (stima)**: 1
**Blocco**: 🏗️ infra — deploy cloud pendente
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_4.3.4 (gold_f_prep_sped), ACT_4.4.1, ACT_4.4.2   **Blocca**: esercizio in PROD Wave C
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: —

## Contesto e motivazione
Workflow end-to-end della Wave C picking + carrellisti, schedulato alle **04:30 Europe/Rome**, che
orchestra Bronze Logistix → Silver → Gold. Definito in
[`workflows/logistica_prep_sped.yml`](../../../workflows/logistica_prep_sped.yml) (v3.0.0), il
workflow è ~90% ma il **deploy su cloud** è pendente in attesa di accesso Databricks. Sprint
[`../sprint_agile/sprint_4.4.md`](../sprint_agile/sprint_4.4.md) (4.4.3, 🔵 PARZ. 90%). Dipende dal
workflow a monte `logistica_landing_ingestion` (i 3 Bronze STAT riepiloghi/bolle + CND `t_prep_sped`
sono già caricati lì). Vedi [[ADR-0009]] (job cluster serverless) e [[ADR-0015]] (tuning non
ereditabile dal locale).

## Obiettivo
Workflow `logistica_prep_sped` schedulato alle 04:30 deployato e funzionante in cloud.
Fatto = run schedulato verde su job cluster serverless (ADR-0009), output Gold aggiornati, costo
serverless verificato.

## Analisi tecnica
- **Schedule**: `quartz_cron_expression: "0 30 4 * * ?"`, `timezone_id: Europe/Rome`, `UNPAUSED`;
  `max_concurrent_runs: 1` (idempotenza, cfr. [`../02_pipeline_mapping.md`](../02_pipeline_mapping.md)
  riga 671). `email_notifications.on_failure`: luigi.scrimitore@aperion.it.
- **Parametri job**: `env`, `run_date={{job.start_time.iso_date}}`, `landing_base_path=${var.landing_base_path}`,
  `file_format=auto`, `siti=lgax,lgcx,lcax,lccx,lexx,locx,lonx,lscx,lslx`.
- **DAG task** (bronze→silver→gold):
  - Bronze Logistix DELTA_MERGE: `bronze_dettaglio_carr` (→ `bronze_missioni_carr`), `bronze_imbfmovim`
    (→ `bronze_movimenti_magazzino`; OP-14 due tabelle distinte), `bronze_cartellino`
    (dipende da ACT_4.1.6). `max_retries: 2`.
  - Silver: `silver_prep_riepilogo`, `silver_prep_bolle`, `silver_timbrature_sessioni` (da CND
    `t_prep_sped`, OP-17); `silver_prep_sped_integrata` (`depends_on` riepilogo+timbrature,
    consolidamento OP-17); carrellisti `silver_missione_carrellista` (← bronze_dettaglio_carr),
    `silver_sessione_carrellista` (← bronze_cartellino).
  - Gold: `gold_f_prep_sped` (`depends_on` silver_prep_riepilogo+silver_timbrature_sessioni; regola
    30 min OP-27), `gold_f_movimentazione_carrellisti` (`depends_on` missione+sessione; no
    ORE_PRODUTTIVE, OP-27).
- **Compute**: **serverless** ([[ADR-0009]]), allineato in [[ACT_9007]]: il .yml non definisce più
  `job_clusters`; i task senza compute dichiarato girano su serverless e prendono il wheel
  `logistica_utils` dal blocco job-level `environments` (`environment_key: default`,
  `environment_version: "2"`, `dependencies: [../lib/dist/logistica_utils-*.whl]`), con
  `environment_key: default` su ogni task. Rimossi `spark_conf` (eventuali conf a livello **sessione**
  nel notebook, ADR-0015) e `custom_tags` (attribuzione costi via serverless usage/budget policy,
  [[ACT_9013]]). Il sizing è gestito da Databricks e il tuning si ritara in cloud
  ([[adr/0015_tuning_cloud_non_trasferibile]]).
- **KPI**: i "task KPI" citati nell'ACT non sono task del workflow — i KPI sono **view**
  `gold_prod.logistica.kpi_*` (`kpi_produttivita_operatore` 4.4.1 ✅, `kpi_efficienza_sito_prep`
  4.4.2 ✅), non notebook orchestrati qui. Da verificare se aggiungere un task di refresh view.
- **Deploy**: via DAB (release kit KIT-06, memoria release-kit). Richiede accesso Databricks →
  bloccato. Tuning memoria/spill non ereditato dal locale (ADR-0015): da ritarare su serverless al
  primo run.

## Sviluppo (diario)
- 2026-07-03 · workflow definito (~90%); deploy in attesa di cloud.
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.

## Verifica
- Deploy via DAB, poi run schedulato/manuale: tutti i task in SUCCESS; output Gold `F_PREP_SPED` +
  `F_MOVIMENTAZIONE_CARRELLISTI` aggiornati per `run_date`.
- Definizione di "workflow completato" (02 riga 1159): tutti i task gold in SUCCESS + check quadratura
  delta < 1% + nessun alert critico.
- Costo serverless verificato: su serverless l'attribuzione non passa dai `custom_tags` del cluster
  (rimossi) ma dalle **serverless usage/budget policy** — cfr. [[ACT_9013]].

## Esito
— (in attesa di deploy cloud)

## Follow-up
- Al gate infra: deploy via DAB e verifica del primo run schedulato; ritarare tuning su serverless.
- Target compute chiarito: serverless, allineamento .yml fatto in [[ACT_9007]] (resta la validazione in cloud).
