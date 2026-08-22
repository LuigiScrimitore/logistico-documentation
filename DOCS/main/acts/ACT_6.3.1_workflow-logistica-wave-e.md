# ACT_6.3.1 · Orchestrazione Wave E (CE178 in `logistica_carichi`, carrellisti in `logistica_prep_sped`)

**Status**: in-progress
**Type**: infra
**Origin**: sprint 6.3
**Sprint**: 6.3
**Fase / Wave**: FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD (deploy Databricks pendente)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_6.1.4 (gold CE178), ACT_6.2.5 (gold carrellisti)   **Blocca**: ACT_6.3.2 (validazione)
**ADR collegate**: ADR-0009 (job cluster serverless), ADR-0010 (incrementale)   **OP collegati**: —

## Contesto e motivazione
Le pipeline CE178 (Sprint 6.1) e carrellisti (Sprint 6.2) devono girare in modo schedulato,
orchestrando bronze→silver→gold e le viste. La validazione funzionale ([[ACT_6.3.2_validazione-ce178-carrellisti]])
non può partire finché i Gold di Wave E non sono prodotti in autonomia. Dettaglio sprint in
[`../sprint_agile/sprint_6.3.md`](../sprint_agile/sprint_6.3.md).

⚠️ **AGGIORNAMENTO STATO REALE (rispetto all'assunto "unico workflow wave_e"):** il placeholder
`workflows/logistica_wave_e.yml` (`STATO: DEPRECATO`, `pause_status: PAUSED`, `tasks: []`) è stato
**RIMOSSO il 2026-08-04** ([[ACT_9008]]) — un job con `tasks: []` non è valido per l'API Jobs e avrebbe
fatto fallire `bundle validate/deploy`. **Non esiste (né serve) un workflow Wave E dedicato**: i task
funzionali sono **ridistribuiti** nei workflow già esistenti:
- **CE178** → `workflows/logistica_carichi.yml` (schedule **02:00**): task `bronze_tracciace178`
  (`../notebooks/bronze/carichi/bronze_traccia_ce178`), `silver_traccia_ce178`,
  `silver_tracciabilita_lotto`, `gold_f_tracciabilita_lotti`. (Coerente con [`../milestones/fase_6.md`](../milestones/fase_6.md) §5: "fact lotti schedulato nel workflow `logistica_carichi`".)
- **Carrellisti** → `workflows/logistica_prep_sped.yml`: task `bronze_missioni_carr`
  (`../notebooks/bronze/carrellisti/bronze_missioni_carr`), `bronze_cartellino`,
  `silver_missione_carrellista`, `silver_sessione_carrellista`,
  `gold_f_movimentazione_carrellisti` (`../notebooks/gold/carrellisti/gold_f_movimentazione_carrellisti`).
- **Dimensione** carrellisti in `logistica_dim_refresh.yml` (`silver dim_operatore`, UNION 4 anagrafiche, OP-15).

⇒ **L'attività va reinterpretata**: non "deployare un nuovo workflow wave_e", ma **verificare che
CE178 e carrellisti siano correttamente orchestrati nei workflow ospitanti** (il destino del placeholder
è deciso: rimosso, [[ACT_9008]]).

## Obiettivo
La catena CE178 + carrellisti (bronze → silver → gold) gira schedulata in cloud senza errori e
produce i Gold di Wave E (`F_TRACCIABILITA_LOTTI`, `F_MOVIMENTAZIONE_CARRELLISTI`). Fatto = i due
Gold risultano aggiornati dai run di `logistica_carichi` (02:00) e `logistica_prep_sped`.

## Analisi tecnica
- **CE178** (Sprint 6.1) — in `logistica_carichi.yml` (02:00): `bronze_traccia_ce178` →
  `silver_traccia_ce178` → `silver_tracciabilita_lotto` (aggregato CE178 per lotto) →
  `gold_f_tracciabilita_lotti` (grana etichetta CE178, replaceWhere `ANNO_MESE`; cfr. 07 §1.8).
- **Carrellisti** (Sprint 6.2) — in `logistica_prep_sped.yml`: `bronze_missioni_carr` +
  `bronze_cartellino` → `silver_missione_carrellista` (da `bronze.dettaglio_carr`) +
  `silver_sessione_carrellista` (da `bronze.cartellino`) → `gold_f_movimentazione_carrellisti`.
  ⚠️ Il Gold reale è **`gold_f_movimentazione_carrellisti`** (v3.1, grana `CARRELLISTA_COD × DATA_PRESENZA × SITO_COD`, replaceWhere `DATA_PRESENZA`), **non** un `gold_f_turno`. Misura `NUM_PLT_MOVIMENTATI` allineata a `F_MOV_CARR.NUM_PLT_MOV_CARR` (07 §1.7). OP-27: il Silver sessione non ha `ORE_PRODUTTIVE` (usa `ORE_PRESENZA`).
- **Compute**: **serverless** ([[adr/0009_job_cluster_serverless]]) — dal [[ACT_9007]] i workflow ospitanti (`logistica_carichi`, `logistica_prep_sped`) non dichiarano più `job_clusters` e il wheel `logistica_utils` arriva dal blocco job-level `environments` (`environment_key: default`); sizing gestito da Databricks, tuning da ritarare in cloud ([[adr/0015_tuning_cloud_non_trasferibile]]). Scritture Gold incrementali via MERGE/replaceWhere ([[adr/0010_incrementale_watermark_pattern2_pruning]]).
- Definizione via DAB (release kit, KIT-06 — cfr. memoria `release-kit`).
- ⚠️ Deploy in cloud pendente (manca accesso/PROD): definizione pronta.

## Sviluppo (diario)
- 2026-07-03 · workflow definito al 90%; deploy cloud pendente (stato PARZIALE in sprint 6.3).
- 2026-08-04 · compute allineato a serverless ([[ACT_9007]]); validazione bundle/run al gate cloud.
- (nota doc) · `logistica_wave_e.yml` deprecato → task CE178/carrellisti spostati in `logistica_carichi`/`logistica_prep_sped`.

## Verifica
- I run di `logistica_carichi` (02:00) e `logistica_prep_sped` completano in cloud senza errori.
- Gold `F_TRACCIABILITA_LOTTI` e `F_MOVIMENTAZIONE_CARRELLISTI` risultano aggiornati sulla partizione del `run_date`.
- Smoke-test/DQ interni verdi ([[adr/0014_dq_alerting_interni]]).

## Esito
— (deploy cloud pendente)

## Follow-up
- ✅ Destino del placeholder `logistica_wave_e.yml` deciso e attuato: **rimosso** ([[ACT_9008]], 2026-08-04).
  Un'eventuale futura estensione Wave E dedicata si crea come nuovo workflow con task reali.
- Alla validazione su dati reali vedi [[ACT_6.3.2_validazione-ce178-carrellisti]].
