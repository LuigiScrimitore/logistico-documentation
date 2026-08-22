# ACT_8.4.4 · Spegnimento flusso Oracle ODI (disabilita, non elimina)

**Status**: proposed
**Type**: infra
**Origin**: sprint 8.4
**Sprint**: 8.4 — Cut-Over & Stabilizzazione Post-Live
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ dipende da stabilizzazione post-live (ACT_8.4.2/8.4.3)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.4.2, ACT_8.4.3   **Blocca**: —
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: —

## Contesto e motivazione
A produzione stabilizzata il vecchio flusso Oracle ODI va spento per evitare doppie elaborazioni. Si
**disabilita, non elimina**, per mantenere la reversibilità (rollback) finché il go-live non è consolidato
— decisione out-of-scope esplicita della milestone `fase_8.md` §8 ("disabilitare, non eliminare gli oggetti
legacy per rollback safety").

## Obiettivo
Flusso Oracle ODI disabilitato (non eliminato). Fatto = scenari/schedule ODI disattivati e documentati, con
possibilità di riattivazione in caso di rollback.

## Analisi tecnica
- **Oggetti da disabilitare** (ODI Studio): gli scenari giornalieri `SCN_CARICO_GIORNALIERO`,
  `SCN_STOCK_GIORNALIERO`, `SCN_PREP_SPED_GIORNALIERO`, `SCN_TRASPORTI_GIORNALIERO`,
  `SCN_CARRELLISTI_GIORNALIERO` (gli stessi che il rollback_plan §3 riabilita) — Disable dei trigger di
  scheduling, **nessuna cancellazione** di scenari/tabelle/oggetti.
- **Precondizioni**: produzione stabile (ACT_8.4.2 D+0/D+1 senza anomalie bloccanti; ACT_8.4.3 nessun
  critico aperto a D+5).
- **Finestra di parallelismo Oracle**: il rollback_plan (§1) impone di mantenere **Oracle ODI + DWH
  operativi e aggiornati in parallelo ≥ 30 giorni** dopo il go-live. Lo spegnimento qui è la
  **disabilitazione dello scheduling**; il mantenimento in parallelo per 30 gg e l'eventuale dismissione
  definitiva (eliminazione) sono decisioni successive, **fuori scope** di questa ACT.
- **Documentazione**: registrare stato disabilitato di ogni scenario e la procedura di riattivazione
  (puntare al rollback_plan §3), per garantire che il rollback resti eseguibile.

## Sviluppo (diario)
- 2026-07-03 · attività pendente.

## Verifica
- Scenari/schedule ODI in stato **disabilitato**; nessuna elaborazione Oracle attiva (no doppi
  caricamenti); artefatti/oggetti legacy **conservati** (riattivabili via rollback_plan §3).

## Esito
— (pendente)

## Follow-up
La dismissione **definitiva** (eliminazione) di ODI/DWH legacy è decisione futura, dopo il periodo di
parallelismo (≥ 30 gg) — eventuale ACT successiva, non in FASE 8.
