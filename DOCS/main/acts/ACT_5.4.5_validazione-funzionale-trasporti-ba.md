# ACT_5.4.5 · Validazione funzionale trasporti con BA

**Status**: proposed
**Type**: analysis
**Origin**: sprint 5.4
**Sprint**: 5.4 — KPI Trasporti & Workflow
**Fase / Wave**: FASE 5 — Wave D: Trasporti (Outbound)
**Gg (stima)**: 1
**Blocco**: ☁️ PROD + disponibilità BA
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_5.3.4 (quadratura), ACT_5.4.4 (workflow)   **Blocca**: chiusura Wave D Trasporti
**ADR collegate**: ADR-0013 (F_TRASPORTO grana MTV)   **OP collegati**: —

## Contesto e motivazione
Prima di chiudere la Wave D i fact e le viste KPI trasporti vanno validati funzionalmente con il Business Analyst su dati PROD. Vedi [`../sprint_agile/sprint_5.4.md`](../sprint_agile/sprint_5.4.md) (5.4.5: ⏳ PENDENTE, "richiede PROD + BA"). Dipende da [[ACT_5.3.4_quadratura-vs-oracle]] (quadratura) e [[ACT_5.4.4_workflow-logistica-trasporti]] (workflow deployato).

## Obiettivo
Validazione funzionale dei KPI/fact trasporti approvata dal BA su dati PROD. Fatto = sign-off BA documentato; rilievi tracciati.

## Analisi tecnica
Oggetti da rivedere con il BA (viste SQL in `sql/kpi/`, schema `gold_prod.logistica`):
- **`kpi_fill_rate`** (`gold_kpi_fill_rate.sql`, sorgente `A_OUTBOUND_MENSILE`). ⚠️ **OP-27**: F_ORDINI non ha qta ordinate/consegnate → il fill-rate quantitativo canonico **non è calcolabile**; si espone `NUM_TRASPORTI/NUM_ORDINI` come **proxy di servizio**. Da spiegare/validare col BA.
- **`kpi_costo_trasporto`** (`gold_kpi_costo_trasporto.sql`, sorgente `F_TRASPORTO`). ⚠️ `COSTO_STIMATO_EUR` è **PLACEHOLDER** (`peso*0.15`); PESO/VOLUME reali non disponibili (OP-27) → costo/KG, /M3, /ordine sono indicativi finché mancano i **listini corrieri**.
- **`kpi_resa_corrieri`** (`gold_kpi_resa_corrieri.sql`, sorgente `F_TRASPORTO`). ⚠️ OP-27: nessun `FLG_RITARDO`/`DATA_CONSEGNA_EFFETTIVA` → proxy `LEAD_TIME_GG` vs `DATA_CONSEGNA_PREV` (ritardato se `DATA_AZIONE > DATA_CONSEGNA_PREV`).
- **Grana MTV di F_TRASPORTO** ([[adr/0013_scope_trasporti_mtv]]): 1 riga = movimento automezzo; niente livelli TRATTA/BOLLA (né costo per tratta). Chiarire col BA che i KPI vanno letti a grana movimento e che la valorizzazione economica è rimandata all'arrivo dei listini.

## Sviluppo (diario)
- 2026-07-03 · PENDENTE; richiede accesso PROD e disponibilità BA.

## Verifica
- Sign-off del BA sui 3 KPI trasporti, con presa d'atto esplicita dei **proxy OP-27** (fill-rate di servizio, costo placeholder, resa via lead-time).
- Coerenza dei KPI con la quadratura vs Oracle ([[ACT_5.3.4_quadratura-vs-oracle]]).
- Eventuali rilievi tracciati come ACT emergenti (9000+).

## Esito
— (in attesa di PROD + BA)

## Follow-up
Eventuali rilievi BA → ACT emergenti 9000+.
