# ACT_8.3.4 · Verifica permessi PROD (MicroStrategy su gold_prod)

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.3
**Sprint**: 8.3 — Preparazione Cut-Over
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (dipende da PROD attivo)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.2   **Blocca**: ACT_8.4.1
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0008_chiavi_naturali_gold]]   **OP collegati**: —

## Contesto e motivazione
Al cut-over la reportistica MicroStrategy deve leggere dal Gold PROD. Vanno verificati i permessi UC su
`gold_prod` per l'utenza/servizio MicroStrategy, così che al go-live i report funzionino senza interruzioni.
È il pre-requisito #9 del `piani/cutover_plan.md` ("MicroStrategy connection string Databricks configurata e
testata — almeno 3 report aperti correttamente puntando a Databricks").

## Obiettivo
Permessi PROD verificati: MicroStrategy legge `gold_prod`. Fatto = grant UC in essere e test di lettura da
MicroStrategy su tabelle gold_prod riuscito (≥ 3 report aperti correttamente).

## Analisi tecnica
- **Reader grant UC**: in Terraform brownfield il reader grant è **condizionale** (`enable_reader_grants`,
  default false) perché il **gruppo analisti/MicroStrategy non esisteva ancora** in DEV (A5,
  [[12_checklist_infra_setup]] §A; D6 [[11_devops_handoff_databricks]]). Per PROD: creato/identificato il
  gruppo, impostare `enable_reader_grants=true` + `group_readers=<nome>` in `terraform.tfvars` (prod) →
  `terraform apply` (nesso con ACT_8.1.2). Nome gruppo PROD: **da verificare** col cliente.
- **Scope grant**: SELECT su `gold_prod.logistica` (fact F_* e dim_*) e `gold_prod.logistica_dm`
  (aggregati). MicroStrategy accede in **sola lettura**.
- **Connection string / DB instance MicroStrategy**: configurare e testare l'istanza
  `LOGISTICO_DWH_DATABRICKS` (SQL warehouse su gold_prod) — è la stessa che il cutover_plan (T=00:00) e il
  rollback_plan (§5) commutano. Sizing warehouse SQL per MSTR da ri-tarare (KIT-08,
  [[0015_tuning_cloud_non_trasferibile]]).
- **Chiavi naturali Gold** ([[0008_chiavi_naturali_gold]]): il Gold usa natural key validate (no ID
  surrogati interi ora); verificare che i report MSTR mappino correttamente le chiavi/nomi (rif. registro
  rename `13_registro_rename_gold_microstrategy.md`).

## Sviluppo (diario)
- 2026-07-03 · in attesa di PROD deployato (ACT_8.1.2).

## Verifica
- Grant UC in essere sul gruppo reader; query di test da MicroStrategy su `gold_prod` restituisce dati.
- **≥ 3 report** MicroStrategy aperti correttamente puntando a Databricks (pre-req. #9 cutover_plan);
  nessun errore di permessi.

## Esito
— (bloccato)

## Follow-up
Se il gruppo reader PROD non è ancora creato: sollecitare il cliente (analogo A5/A7 DEV). Coordinare l'apply
del reader grant con ACT_8.1.2.
