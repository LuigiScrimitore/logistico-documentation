# ACT_7.3.2 · Approvazione KPI da business (sign-off)

**Status**: proposed
**Type**: analysis
**Origin**: sprint 7.3
**Sprint**: 7.3 — Validazione KPI End-to-End
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 1
**Blocco**: ☁️ cloud/PROD + BA (dipende dalla validazione 7.3.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_7.3.1 (validazione KPI)   **Blocca**: —
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Formalizzazione dell'accettazione dei KPI da parte del business, a valle della sessione di validazione
([[ACT_7.3.1_validazione-kpi-con-ba]]). È il **gate** che dichiara i KPI pronti per il go-live reporting
(punti V-07/V-08, `milestones/fase_7.md` §7). Precede il collegamento definitivo di MicroStrategy alle viste KPI.

## Obiettivo
Sign-off business sui KPI ottenuto e registrato.
Fatto = approvazione formale del business acquisita e archiviata.

## Analisi tecnica
- **Dipende interamente dall'esito di ACT_7.3.1**; nessuna componente tecnica ulteriore da sviluppare.
- Precondizione al sign-off: scostamenti della validazione 3 mesi entro tolleranza (delta < 1%, cfr. ACT_7.3.1)
  e chiusura/recepimento dei rename 🔴 che impattano le metriche esposte (`13_registro_rename_gold_microstrategy` §B/C —
  A_INBOUND scarto→ammanco, `kpi_lead_time_fornitore`→`kpi_volumi_inbound_fornitore`, `kpi_qualita_ricevimento`).
- Governance: rientra nel perimetro decisionale **interno al team** per i flussi/KPI (Reply solo su anagrafiche/setup,
  cfr. [[adr/0018_reply_scope_governance]]).

## Sviluppo (diario)
- 2026-07-03 · pendente: dipende da 7.3.1.

## Verifica
Approvazione formale registrata (verbale/mail di sign-off), con riferimento al report di validazione 3 mesi
e alla lista scostamenti accettati.

## Esito
— (pendente)

## Follow-up
Nessuna al momento.
