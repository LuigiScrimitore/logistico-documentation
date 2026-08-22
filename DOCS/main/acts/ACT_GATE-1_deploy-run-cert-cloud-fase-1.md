# ACT_GATE-1 · Gate cloud FASE 1 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 1 — Dimensioni
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (terraform apply, I-02) + workspace TEST
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: tutte le ACT di FASE 1 (done offline), [[ACT_0.1.2]], [[ACT_8.1.2]] (deploy DAB)   **Blocca**: chiusura reale FASE 1
**ADR collegate**: ADR-0009, ADR-0010, ADR-0017   **OP collegati**: OP-24 (criteri accettazione), OP-02 (residuo dim ART/FORN)

## Contesto e motivazione
Le attività di FASE 1 sono **done offline** (codice validato in locale). Una fase è chiusa **davvero** solo
quando il suo pacchetto gira in cloud, schedulato e certificato — vedi *Definition of Done di fase* in
[`../acts/README.md`](README.md). Questa ACT è il **gate** che porta FASE 1 dal "done offline" al "done reale".

## Obiettivo
Pacchetto Dimensioni deployato in Azure Databricks TEST, eseguito a schedule con regolarità e certificato,
secondo la DoD di fase.

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_dim_refresh.yml` (refresh DIM/LU) via DAB `databricks bundle deploy -t dev`.
- **Output attesi**: `gold_*.logistica.LU_SITO/OPERATORE/CORRIERE/TOPOGRAFIA/AREA` + `DIM_CALENDARIO`,
  `DIM_STRUTTURA_MERCEOLOGICA` popolati.
- **Certificazione**: dimensioni LU_* vs CDT_DW (cardinalità + chiavi naturali) — cfr. [[ACT_9000]] §dimensioni.
- Nota: residuo join master ART/FORN gated su [[ACT_OP-02]]; compute serverless da allineare [[ACT_9007]].

## Verifica — Definition of Done (cloud)
1. **Deploy** in Azure Databricks TEST (dev) via DAB, senza errori.
2. **Run schedulato** ≥ 5 esecuzioni consecutive **senza errori né rilanci manuali** (soglia N da confermare, OP-24).
3. **Qualità**: DQ verdi ad ogni run (orphan-rate 0.0%, 0 FAIL).
4. **Dati certificati**: quadratura dimensioni entro soglia (o divergenze documentate).

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Alla chiusura: aggiornare `15_backlog_master.md` (riga fase) e `milestones/fase_1.md`. Promozione PROD → [[ACT_GATE-PROD]].
