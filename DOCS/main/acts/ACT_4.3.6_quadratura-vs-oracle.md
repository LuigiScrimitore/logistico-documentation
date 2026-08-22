# ACT_4.3.6 · Quadratura vs Oracle (COLLI_PREPARATI, ORE_PRODUTTIVE)

**Status**: in-progress
**Type**: dq
**Origin**: sprint 4.3
**Sprint**: 4.3 — Gold F_PREP_SPED
**Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)
**Gg (stima)**: 1
**Blocco**: 🏗️ infra — richiede cloud + accesso Oracle sorgente
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_4.3.4 (gold_f_prep_sped)   **Blocca**: certificazione Gold prep sped
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: —

## Contesto e motivazione
Il fact `gold_f_prep_sped` è realizzato (0.0% orphan PREPARATORE/OPERATORE,
[`../02_pipeline_mapping.md`](../02_pipeline_mapping.md) riga 8; v4.0 grain riga-prelievo con
`SEQ_PREL_PREP`) ma manca la **quadratura numerica** delle misure contro Oracle/CDT_DW. Senza
quadratura il fact non è certificabile. Sprint
[`../sprint_agile/sprint_4.3.md`](../sprint_agile/sprint_4.3.md) (4.3.6, 🔵 PARZ. 20%): "Residuo:
quadratura; richiede cloud+Oracle". Il registro di certificazione
[`../07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md) §1.2 indica lo **script
parametrico già pronto** e l'esecuzione "dopo il re-run del Gold". Vedi [[ADR-0008]] (chiavi naturali
Gold) e memoria "Certificazione gold vs CDT_DW".

> **Nota misure**: il titolo storico dell'ACT cita COLLI_PREPARATI / ORE_PRODUTTIVE, ma queste
> appartengono all'aggregato di **turno/produttività** (`F_TURNO_PREP_SITO`, regola 30 min), non al
> grain riga-prelievo di `F_PREP_SPED`. Le misure realmente quadrate dallo script su F_PREP_SPED sono
> **`QTA_PREP`, `VAL_PREP_CES`, `VAL_PREP_VEN`** (più il COUNT righe). La quadratura di
> COLLI_PREPARATI/ORE_PRODUTTIVE è **da verificare** come confronto separato su F_TURNO_PREP_SITO.

## Obiettivo
Quadratura di F_PREP_SPED Gold vs CDT_DW entro tolleranza concordata su `(SITO, PERIODO)`.
Fatto = delta di `CNT`, `QTA_PREP`, `VAL_PREP_CES`, `VAL_PREP_VEN` entro soglia documentato,
blocco scartate (OP-PSP-1) verificato, fact certificabile e registro `07` aggiornato.

## Analisi tecnica
- **Script**: [`scripts/quadratura/quadratura_fact.py`](../../../scripts/quadratura/quadratura_fact.py)
  `--fact PREP_SPED` (parametrico, generalizza `quadratura_f_carico.py`). Confronta CDT_DW (ODI legacy)
  vs Gold Delta letto **senza Spark** (pandas/pyarrow su `_delta_log` add−remove, `live_delta_files`,
  per evitare i tombstone di full_refresh — OP-CAR-4, memoria delta-tombstone-pyarrow-read).
- **Grain di confronto**: `(SITO canonico, PERIODO)` con `PERIODO` = giorno (default) o mese
  (`--per-mese`); aggregato `COUNT(*)` + `SUM(NVL(misura,0))`.
- **Config FACTS["PREP_SPED"]**: oracle `CDT_DW.F_PREP_SPED` (204 colonne, §1.2), data via
  `GIORNO_BOLLA_SPED_ID` (YYYYMMDD numerico, nessun join L_GIORNO); Gold `f_prep_sped`, sito
  `MAG_SITO_COD`, data `DATA_BOLLA_SPED`. Misure `QTA_PREP→QTA_PREP`, `VAL_CES→VAL_PREP_CES`,
  `VAL_VEN→VAL_PREP_VEN`.
- **Mapping sito** (memoria sito-mapping-slogistix): `MAG_SITO_COD` CDT_DW (es. `0005C`) → canonico
  (`05`) via `CDT_ESTR.S_LOGISTIX` (`FLAG_ATTIVO=1`), `int(cifre)+zfill(2)`.
- **Blocco scartate (OP-PSP-1)**: righe senza bolla `GIORNO_BOLLA_SPED_ID=0` (ODI) vs
  `DATA_BOLLA_SPED IS NULL` (Gold), filtrate per data prelievo `GIORNO_PREL_INIZ_ID` /
  `DATA_PREL_INIZ` — TIPO_SCAR 09/10; report separato in `print_no_bolla_report`.
- **Prerequisito**: re-run del Gold dopo il cambio schema v4.0 (§1.2 nota re-run: droppare
  `silver.logistica_curated.prep_sped` e `gold.logistica.F_PREP_SPED` prima del re-run, CTAS pulito).
- **Riferimento legacy**: costruzione ODI-generated `CDT_DW.SP_LOAD_F_PREP_SPED_ODI`
  (`DOCS/99. SCRIPT/CDT_DW.sql`); `SP_CHECK_PREP_SPED_NEW` (F_PREP_SPED vs LOGISTIX.RIEPILOGHI) come
  riferimento delta storici accettati.
- **Connessione**: `.env` in `scripts/landing_simulator/` (`ORACLE_HOST/PORT/SERVICE/USER/PASSWORD`);
  deps `oracledb python-dotenv pandas pyarrow`. Colonne validabili con `--discover`. Richiede accesso
  cloud + Oracle → bloccato offline. Seguire il playbook di certificazione wave (memoria
  "Playbook certifica wave").

## Sviluppo (diario)
- 2026-07-03 · impostazione confronto (~20%); esecuzione bloccata su cloud/Oracle.

## Verifica
- Comandi: `python quadratura_fact.py --fact PREP_SPED --discover` (valida colonne), poi
  `python quadratura_fact.py --fact PREP_SPED --da 2026-06-15 --a 2026-06-21 --soglia 5.0`
  (per le prime quadrature soglia **5%** per isolare le differenze strutturali, §"soglia"; a regime 1%).
- Criterio "fatto": `RIEPILOGO PREP_SPED ... 0 con anomalie` (exit 0); delta per SITO/PERIODO su
  `CNT`, `QTA_PREP`, `VAL_PREP_CES`, `VAL_PREP_VEN` entro soglia; blocco scartate (OP-PSP-1) senza
  anomalie; scostamenti residui spiegati e documentati (es. giorni con landing incompleta, cfr. §1.1
  nota 17 giugno "unico giorno con landing completa").

## Esito
— (in attesa di accesso cloud + Oracle)

## Follow-up
- Al gate infra: eseguire la quadratura e aggiornare
  [`../07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md) §1.2.
- Valutare quadratura separata COLLI_PREPARATI/ORE_PRODUTTIVE su F_TURNO_PREP_SITO (da verificare).
- Anomalie strutturali → eventuali ACT emergenti 9000+.
