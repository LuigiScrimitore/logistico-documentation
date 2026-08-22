# ACT_GATE-PROD · Deploy in PRODUZIONE — go-live dell'intero pacchetto (capstone)

**Status**: proposed   **Type**: infra   **Origin**: gate di fine progetto
**Sprint**: fuori-sprint (capstone)   **Fase / Wave**: FASE 8 — Shadow mode & Cut-over
**Gg (stima)**: —   **Blocco**: 🏗️☁️ dipende da GATE-1..7 (tutte le fasi certificate in TEST) + infra PROD
**Created**: 2026-08-01   **Closed**: —
**Dipende da**: [[ACT_GATE-1]]..[[ACT_GATE-7]] (fasi chiuse in cloud TEST)   **Blocca**: chiusura progetto
**ADR collegate**: ADR-0017 (go-live a fasi), ADR-0014 (DQ/alerting), ADR-0004 (naming `_prod`)   **OP collegati**: OP-24, OP-25, D-01..D-07

## Contesto e motivazione
Punto d'ingresso unico del **go-live in produzione** dell'intero pacchetto logistico. **Non duplica** le
attività di FASE 8: le **coordina**. Ha senso solo quando tutte le fasi 1-7 sono chiuse in cloud TEST
(GATE-1..7) — cioè deployate, schedulate stabili e certificate. Coerente con ADR-0017 (go-live a fasi, no
big-bang).

## Obiettivo
Pacchetto logistico in **PRODUZIONE**: provisioning PROD, deploy, shadow mode superato, cut-over eseguito,
post-live stabile, flusso Oracle ODI spento.

## Analisi tecnica — sequenza (rimanda alle ACT 8.x, SSOT di dettaglio)
1. **Provisioning PROD** → [[ACT_8.1.1]] (workspace + ADLS) · [[ACT_8.1.2]] (terraform + DAB `-t prod`) · [[ACT_8.1.3]] (attivazione workflow + backfill).
2. **Shadow mode** → [[ACT_8.1.4]] quadratura automatica · [[ACT_8.2.1]] monitoraggio (delta ≤ 0.1% su ≥ 95% giorni) · [[ACT_8.2.4]] report + sign-off.
3. **Prep cut-over** → [[ACT_8.3.1]] rollback plan · [[ACT_8.3.2]] cut-over plan · [[ACT_8.3.3]] comunicazione · [[ACT_8.3.4]] permessi PROD MicroStrategy.
4. **Cut-over & post-live** → [[ACT_8.4.1]] esecuzione · [[ACT_8.4.2]] verifica D+0/D+1 · [[ACT_8.4.3]] supporto D+1→D+5 · [[ACT_8.4.4]] spegnimento ODI · [[ACT_8.4.5]] retrospettiva.

## Verifica — Definition of Done (produzione)
1. Tutte le GATE-1..7 chiuse (fasi certificate in TEST).
2. Shadow mode PROD superato (criteri D-06 / OP-24).
3. Cut-over eseguito; verifica post-cut-over OK; nessun rollback attivo.
4. Flusso Oracle ODI disabilitato; MicroStrategy su `gold_prod`; progetto chiuso.

## Esito
— (capstone di fine progetto)

## Follow-up
Retrospettiva e documentazione finale ([[ACT_8.4.5]]).
