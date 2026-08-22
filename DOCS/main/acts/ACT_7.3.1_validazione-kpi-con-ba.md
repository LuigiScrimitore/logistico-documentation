# ACT_7.3.1 · Sessione validazione KPI con BA/Key User (3 mesi vs Oracle)

**Status**: proposed
**Type**: analysis
**Origin**: sprint 7.3
**Sprint**: 7.3 — Validazione KPI End-to-End
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD + BA (richiede PROD e disponibilità Business Analyst/Key User)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_7.2.3 (viste KPI)   **Blocca**: ACT_7.3.2 (sign-off)
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Prima del sign-off business (ACT_7.3.2), i KPI Gold vanno validati end-to-end confrontando **3 mesi** di dati
contro Oracle/CDT_DW (fonte legacy) insieme a BA e Key User. Non avviabile offline: serve **PROD** (dati completi
sul warehouse cloud) e la **presenza del business**. Corrisponde ai punti aperti **V-07/V-08** (`06_backlog.md`,
`milestones/fase_7.md` §7).

## Obiettivo
Sessione di validazione KPI completata: 3 mesi confrontati vs Oracle con BA/Key User, scostamenti tracciati.
Fatto = validazione eseguita e differenze documentate, con scostamenti KPI entro tolleranza concordata.

## Analisi tecnica
- **Oggetto del confronto**: le 10 viste KPI (`gold_prod.logistica.kpi_*`, `sql/kpi/gold_kpi_*.sql`) e i 6 DataMart
  `A_*` ([[ACT_7.2.3_kpi-views-chiavi-naturali]], sprint 7.1) vs gli **aggregati Oracle CDT_DW `A_*`** (l'analisi
  sorgente è ACT_7.1.1) su finestra 3 mesi.
- **Tolleranza di riferimento**: la soglia operativa del progetto è **delta < 1%** su ogni KPI principale
  (`ALERT_KPI_DELTA` in `02_pipeline_mapping.md`, SLA "quadratura delta < 1%"); confermare/adattare col business.
- **Metodologia**: allineata al **playbook di certificazione fact vs ODI/CDT_DW** (memory `playbook-certifica-wave`,
  `07_*` certificazione). Riuso del pattern quadratura già applicato ai fact (F_CARICO/PREP_SPED certificati).
- **Attenzioni note (non sono difetti da spiegare come scostamenti)**: `A_OUTBOUND_MENSILE` ha misure costo/quantità
  **NULL** finché mancano i listini corrieri (Fase 5, [[adr/0013_scope_trasporti_mtv]]); `A_INBOUND` v4.0 espone
  **ammanco in pezzi** (non "scarto") con concentrazione ordinato sulla prima etichetta (OP-CAR-3) → confrontare
  aggregato, non riga (`13_registro_rename_gold_microstrategy` §D); produttività in **cartoni/ora** (non colli/ora).
- Output atteso: report di confronto per KPI/mese con delta% e note sugli scostamenti fuori tolleranza.

## Sviluppo (diario)
- 2026-07-03 · pendente: non avviabile offline (richiede PROD + BA).

## Verifica
Report di confronto 3 mesi con scostamenti KPI entro tolleranza concordata con il business (rif. delta < 1%);
scostamenti residui spiegati (misure NULL note, differenze di grain/definizione ammanco).

## Esito
— (pendente PROD + BA)

## Follow-up
Nessuna al momento.
