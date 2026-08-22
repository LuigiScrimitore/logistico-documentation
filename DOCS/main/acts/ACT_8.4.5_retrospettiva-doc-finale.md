# ACT_8.4.5 · Retrospettiva + documentazione finale

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.4
**Sprint**: 8.4 — Cut-Over & Stabilizzazione Post-Live
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ chiusura dipende dal completamento del go-live
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.4.1, ACT_8.4.2, ACT_8.4.3, ACT_8.4.4   **Blocca**: —
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: OP-21 (DQ interno candidabile a standard), OP-NAMING

## Contesto e motivazione
A chiusura della FASE 8 servono una retrospettiva (cosa ha funzionato, lezioni apprese) e la documentazione
finale del progetto, per consolidare il passaggio in esercizio. È il deliverable di chiusura di fase per il
cliente (milestone `fase_8.md`).

## Obiettivo
Retrospettiva svolta e documentazione finale completata. Fatto = verbale retro + doc finale aggiornata e
archiviata, coerente con lo stato go-live.

## Analisi tecnica
- **Bozza esistente** in `DOCS/Archive/` (PARZ. 30%).
- **Consolidare gli esiti** della fase: report shadow mode (ACT_8.2.4), esecuzione cut-over con log
  step-by-step (ACT_8.4.1), presidio post-live D+0/D+1 (ACT_8.4.2) e supporto D+1→D+5 (ACT_8.4.3),
  spegnimento ODI (ACT_8.4.4).
- **Doc da aggiornare al completamento** (processo README acts §Ciclo di vita): chiudere le ACT 8.x
  (Status=done, Closed, Esito), aggiornare `15_backlog_master.md`, la milestone `fase_8.md` e i documenti
  globali impattati (piano `04`, architettura `01`, pipeline `02`, open points `05`).
- **Punti aperti da tirare le somme** (milestone §7): OP-22 (SLA failure), OP-24 (criteri accettazione
  parallel run), OP-25 (processo go-live), **OP-NAMING** (revisione naming oggetti/colonne legacy, da
  pianificare in fase successiva), e la nota strategica OP-21 (il modello DQ interno KIT-03/04 candidabile
  a standard se arriviamo prima del cliente).
- **Learnings tecnici**: cosa del tuning cloud si è dovuto ri-tarare ([[0015_tuning_cloud_non_trasferibile]]),
  esito idempotenza/late-arrival (ACT_8.2.3, V-04), eventuali fix ricorrenti (ACT_8.2.2).

## Sviluppo (diario)
- 2026-07-03 · bozza in `DOCS/Archive/` (PARZ. 30%).

## Verifica
- Verbale retrospettiva presente; documentazione finale aggiornata e coerente con lo stato go-live; ACT 8.x
  e registri (`15_backlog_master.md`, `fase_8.md`) allineati.

## Esito
— (parziale: bozza in corso)

## Follow-up
Pianificare le attività di lungo periodo emerse: OP-NAMING (revisione naming), dismissione definitiva Oracle
(post-parallelismo, rif. ACT_8.4.4), automazione completa monitoraggio quadrature post go-live.
