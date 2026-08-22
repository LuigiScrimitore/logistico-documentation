# ACT_GATE-7 · Gate cloud FASE 7 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 7 — Aggregati & MSTR
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da GATE-2..6 (fact certificati) + workspace TEST + SQL Warehouse
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 7 (done offline), [[ACT_GATE-2]]..[[ACT_GATE-6]] (fact a monte)   **Blocca**: chiusura reale FASE 7, sign-off KPI
**ADR collegate**: ADR-0008, ADR-0009, ADR-0015 (tuning cloud), ADR-0017   **OP collegati**: OP-24, V-07/V-08 (sign-off KPI)

## Contesto e motivazione
FASE 7 (DataMart A_* + MicroStrategy) è **done offline**. Gli aggregati derivano dai fact: il gate ha senso
solo dopo che i fact a monte sono certificati (GATE-2..6). Gate per il "done reale" in cloud (DoD di fase,
[`README.md`](README.md)).

## Obiettivo
DataMart + SQL Warehouse + connettore MicroStrategy attivi in TEST, schedulati e certificati; sign-off KPI
con BA (V-07/V-08).

## Analisi tecnica — cosa deployare/validare
- **Workflow**: `workflows/logistica_aggregati.yml` (`logistica_datamart`, cron 06:00) → `A_*` mensili.
- **Serving**: SQL Warehouse ([[ACT_7.2.4]] tuning — ADR-0015, si ritara su cloud), 10 viste
  `gold_prod.logistica.kpi_*`, connettore MicroStrategy ([[ACT_7.2.1]]); rename MSTR da recepire (doc `13`).
- **Certificazione**: aggregati **indiretta** (se i fact sono certificati, gli A_* sono corretti per
  costruzione) + sanity check vs report MicroStrategy; sign-off KPI BA (V-07/V-08, tolleranza < 1%).
- Compute serverless [[ACT_9007]].

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori; SQL Warehouse + viste attive.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali.
3. **Qualità**: DQ verdi; performance baseline E2E entro SLA ([[ACT_7.3.3]]).
4. **Dati certificati**: KPI entro soglia vs CDT_DW + **sign-off business** (V-08).

## Esito
— (bloccato su GATE-2..6 e infra cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_7.md`. Promozione PROD → [[ACT_GATE-PROD]].
