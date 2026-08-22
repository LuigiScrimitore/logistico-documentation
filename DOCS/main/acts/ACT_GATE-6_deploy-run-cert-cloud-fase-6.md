# ACT_GATE-6 · Gate cloud FASE 6 — deploy + run schedulato + certificazione (Azure TEST)

**Status**: proposed   **Type**: infra   **Origin**: gate di chiusura fase
**Sprint**: fuori-sprint (gate)   **Fase / Wave**: FASE 6 — Wave E CE178 & Carrellisti
**Gg (stima)**: 1   **Blocco**: 🏗️☁️ dipende da FASE 0 in cloud (I-02) + GATE-1; V-06 compliance BA
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: ACT di FASE 6 (done offline), [[ACT_GATE-1]], [[ACT_9008]] (orchestrazione Wave E)   **Blocca**: chiusura reale FASE 6
**ADR collegate**: ADR-0009, ADR-0010, ADR-0014, ADR-0017   **OP collegati**: OP-24, OP-MOV-1, V-06 (compliance CE178)

## Contesto e motivazione
FASE 6 (CE178 + carrellisti) è **done offline**. ⚠️ Non esiste un workflow `logistica_wave_e` attivo: la
tracciabilità CE178 gira in `logistica_carichi.yml` e i carrellisti in `logistica_prep_sped.yml` (vedi
[[ACT_9008]]). Gate per il "done reale" in cloud (DoD di fase, [`README.md`](README.md)).

## Obiettivo
Output Wave E (F_TRACCIABILITA_LOTTI, F_MOVIMENTAZIONE_CARRELLISTI) deployati e schedulati in TEST,
certificati; compliance CE178 verificata su dati reali (V-06).

## Analisi tecnica — cosa deployare/validare
- **Orchestrazione**: task CE178 dentro `logistica_carichi.yml`; carrellisti dentro `logistica_prep_sped.yml`
  (chiarire/consolidare via [[ACT_9008]]).
- **Fact reali**: `gold_f_tracciabilita_lotti`, `gold_f_movimentazione_carrellisti` (con `NUM_PLT_MOVIMENTATI`,
  [[ACT_9003]]) — **non** `gold_f_turno`.
- **Certificazione**: F_TRACC vs `CDT_DW.F_TRACC` (COUNT etichette CE178); F_MOV vs famiglia `F_MOV_CARR`
  (SUM NUM_PLT). **Compliance CE178 (V-06)** su dati reali con BA.

## Verifica — Definition of Done (cloud)
1. **Deploy** DAB in TEST senza errori.
2. **Run schedulato** ≥ 5 run consecutivi senza errori né rilanci manuali.
3. **Qualità**: DQ verdi; vista conformità CE178 senza lotti scaduti-con-residuo imprevisti.
4. **Dati certificati**: quadratura F_TRACC / F_MOV entro soglia; compliance CE178 validata (V-06).

## Esito
— (bloccato su FASE 0 in cloud)

## Follow-up
Aggiornare backlog master + `milestones/fase_6.md`. Promozione PROD → [[ACT_GATE-PROD]].
