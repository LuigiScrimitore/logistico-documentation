# ACT_8.4.3 · Supporto utenti D+1→D+5 (presidio, bug fixing)

**Status**: proposed
**Type**: fix
**Origin**: sprint 8.4
**Sprint**: 8.4 — Cut-Over & Stabilizzazione Post-Live
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 2
**Blocco**: ☁️ dipende dal go-live (ACT_8.4.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.4.1   **Blocca**: —
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0016_multi_repo_gitlab]]   **OP collegati**: OP-22 (SLA failure)

## Contesto e motivazione
Nei primi giorni post-live (D+1→D+5) gli utenti finali possono segnalare problemi su dati/report: serve un
presidio con bug fixing rapido per stabilizzare la produzione. È la fase di stabilizzazione che consolida
il go-live prima dello spegnimento ODI (ACT_8.4.4) e della retrospettiva (ACT_8.4.5).

## Obiettivo
Supporto utenti D+1→D+5 garantito con bug fixing. Fatto = segnalazioni gestite e risolte/istradate; nessun
problema critico aperto a fine periodo; produzione stabile a D+5.

## Analisi tecnica
- **Canale di raccolta segnalazioni** dai referenti business per area (Carichi, Giacenze, Prep Spedizioni,
  Trasporti — gli stessi elencati in rollback_plan §6.2). Triage per severità/impatto.
- **Bug fixing & redeploy** (rif. ACT_8.2.2, [[0016_multi_repo_gitlab]]): fix su `logistico-workflows`/
  `logistico-lib` → MR → `databricks bundle deploy -t prod`; rollback pipeline (Delta `RESTORE`, KIT-07) se
  un fix regredisce. Ogni fix tracciata su commit.
- **Watch trigger di rollback** (rollback_plan §2): se le segnalazioni superano le soglie (T8: > 10
  segnalazioni errore dati su report diversi) valutare rollback con PM+BA.
- **SLA di risposta** (OP-22, da runbook ACT_8.1.5): tempi di presa in carico/risoluzione per severità.
- Bug significativi → **ACT emergenti 9000+** dedicate.

## Sviluppo (diario)
- 2026-07-03 · attività pendente.

## Verifica
- Backlog segnalazioni chiuso o istradato; nessun problema **critico** aperto; produzione stabile a D+5
  (precondizione, con ACT_8.4.2, per lo spegnimento ODI).

## Esito
— (pendente)

## Follow-up
Possibili ACT emergenti 9000+ per bug post-live. Learnings → retrospettiva (ACT_8.4.5) e runbook (ACT_8.1.5).
