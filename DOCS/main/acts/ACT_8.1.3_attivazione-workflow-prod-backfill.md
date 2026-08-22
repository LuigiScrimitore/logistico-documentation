# ACT_8.1.3 · Attivazione workflow PROD + backfill storico

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.1
**Sprint**: 8.1 — Shadow Mode Setup
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (dipende da deploy PROD)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.2   **Blocca**: ACT_8.1.4, ACT_8.2.1
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0010_incrementale_watermark_pattern2_pruning]], [[0003_uc_volume_landing]], [[0005_no_secret_oracle_export_landing]]   **OP collegati**: —

## Contesto e motivazione
Perché lo shadow mode produca dati confrontabili con Oracle, i workflow PROD vanno attivati/schedulati e lo
storico va caricato (backfill) così che il warehouse PROD parta allineato prima del run giornaliero. È il
primo run reale end-to-end su PROD e abilita la quadratura giornaliera (ACT_8.1.4).

## Obiettivo
Workflow PROD attivi e schedulati; backfill storico completato. Fatto = il warehouse PROD contiene lo
storico e i job girano su schedule pronti per il confronto giornaliero (→ ACT_8.1.4).

## Analisi tecnica
- **Ingestion / landing PROD**: concordare col team sorgente il **push SFTP** su Volume landing PROD,
  struttura `<source>-landing/{tabella}/YYYY/MM/DD/`, formato CSV (Parquet supportato), **SLA 04:00**
  ([[12_checklist_infra_setup]] §C, [[11_devops_handoff_databricks]] §4 FASE D). Oracle resta read-only,
  ingestion in push (nessun JDBC, [[0005_no_secret_oracle_export_landing]]). Lo script di send è
  `scripts/sftp/send_to_sftp.py` (KIT-01: dry-run testato 8419 file/31GB, idempotente+retry).
- **Backfill storico** bronze→silver→gold: caricare lo storico dai file landing. Ordine DAG
  ([[14_release_kit]] §2): fondamenta → dimensioni/anagrafiche → F_CARICO (pilota) → altri fact per wave →
  aggregati A_* disaccoppiati. Le dimensioni **prima** dei fact (altrimenti orphan; il LAD resolver
  [[0011_lad_via_cod_nat]] copre il late-arriving, non sostituisce l'ordine).
- **Schedule workflow**: abilitare gli schedule dei job deployati (ACT_8.1.2). Con SLA push 04:00 →
  landing check 04:30, primo processing 05:00 ([[12_checklist_infra_setup]] C4). Trigger schedule
  giornaliero o **file arrival** sul Volume ([[10_piano_migrazione_databricks]] §6).
- **Incrementale a regime** ([[0010_incrementale_watermark_pattern2_pruning]]): dopo il backfill, i run
  giornalieri usano watermark su `config_prod.logistica_etl` + pruning; job parameters `env=prod`,
  `run_date`, `full_refresh` (già compatibili, nessuna modifica).
- **Sizing serverless da ri-tarare** ([[0015_tuning_cloud_non_trasferibile]], KIT-08): il tuning locale
  (driver 12g, spill, `partitionOverwriteMode`) **non si trasferisce**; osservare spill/timing dai Spark UI
  e stabilire una baseline timing/costo per pipeline (durata workflow target < 4h, rif. cutover_plan
  prereq. 8).

## Sviluppo (diario)
- 2026-07-03 · in attesa di ACT_8.1.2.

## Verifica
- Job schedulati in stato **attivo**; primo file atterrato su landing PROD.
- Run di backfill completato senza errori (nessun job FAILED); conteggi gold_prod coerenti con lo storico
  atteso e con i conteggi validati in locale/DEV.
- Orphan-rate 0.0% mantenuto (R-01); Silver/Gold 0 FAIL (R-02/R-03) via smoke-test acceptance (KIT-02).
- Durata workflow entro la finestra batch (< 4h).

## Esito
— (bloccato)

## Follow-up
Baseline timing/costo per pipeline → tuning iterativo (KIT-08). Se il backfill evidenzia degenerazioni di
grana/volumi → ACT emergente 9000+.
