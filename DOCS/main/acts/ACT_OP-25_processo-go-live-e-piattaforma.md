# ACT_OP-25 · Processo go-live + servizi di piattaforma (alerting/SP/test/accettazione)

**Status**: on-hold   **Type**: doc   **Origin**: open-point OP-18, OP-20, OP-22, OP-23, OP-24, OP-25
**Sprint**: fuori-sprint (dipendenza Reply/Technology)   **Fase / Wave**: FASE 8 (go-live)
**Gg (stima)**: —   **Blocco**: 🤝 Reply / ⏸️ Technology
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: risposte Reply/Technology   **Blocca**: sign-off go-live formale
**ADR collegate**: ADR-0017 (go-live a fasi), ADR-0014 (DQ/alerting interni come ponte)   **OP collegati**: OP-18, OP-20, OP-22, OP-23, OP-24, OP-25

## Contesto e motivazione
Il go-live formale richiede alcuni servizi/processi di piattaforma che dipendono da Reply/Technology e non
sono sviluppo interno. Raggruppati qui come registro di dipendenze del gate go-live (coerente con ADR-0017,
rilascio a fasi). Nel frattempo il team usa ponti interni (email su failure, DQ custom — ADR-0014).

## Obiettivo
Formalizzare processo e servizi mancanti prima del cut-over.

## Analisi tecnica
- **OP-18** ⏸️ — Service Principal: Technology valuta un **SP unico** per la data platform; recepire l'ID
  quando disponibile (ping mensile a Ippazio).
- **OP-20** 🟡 — alerting Databricks del team Reply: oggi email su failure come ponte; integrare al rilascio.
- **OP-22** 🟡 — SLA di risposta ai failure: formalizzare nel `runbook.md` (soglie ripristino, profili
  abilitati al riavvio job in prod).
- **OP-23** 🟡 — dataset sintetico rappresentativo per test E2E (dev/prod speculari): definire con Reply.
- **OP-24** 🟡 — criteri accettazione parallel run per wave (durata, tolleranza, responsabile): formalizzare
  in `piani/cutover_plan.md`.
- **OP-25** 🟡 — processo formale di go-live (approvazione, evidenze test, checklist, promozione dev→prod):
  produrre proposta e condividerla con Reply.

## Sviluppo (diario)
- 2026-07-05 · registro dipendenze consolidato; ponti interni attivi.

## Verifica
Ogni punto formalizzato nel documento pertinente (runbook/cutover_plan) o recepito dal servizio di piattaforma.

## Esito
— (in attesa Reply/Technology)

## Follow-up
Confluisce nel gate go-live di FASE 8 (sprint 8.2/8.3). Collegato a [[release-kit]].
