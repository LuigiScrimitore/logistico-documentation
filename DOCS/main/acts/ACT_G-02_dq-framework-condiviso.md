# ACT_G-02 · Framework Data Quality condiviso (allineamento a standard piattaforma)

**Status**: on-hold   **Type**: dq   **Origin**: backlog G-02 / OP-21
**Sprint**: fuori-sprint (dipendenza Reply)   **Fase / Wave**: trasversale (DQ)
**Gg (stima)**: da definire   **Blocco**: 🤝 Reply (OP-21 senza risposta — bloccante)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: risposta Reply su standard DQ   **Blocca**: —
**ADR collegate**: ADR-0014 (DQ & alerting interni come ponte)   **OP collegati**: OP-21 🔴, OP-20 (alerting)

## Contesto e motivazione
Non è chiarito se la piattaforma abbia un framework DQ standard (Great Expectations / Lakehouse Monitoring
/ Soda). Nel frattempo il team usa `dq_helper.py` custom in `logistica_utils` (ADR-0014). OP-21 è marcato
**bloccante senza risposta**: va ri-sottoposto a Reply con priorità alta per evitare un doppio impianto DQ.

## Obiettivo
Decisione su framework DQ di piattaforma; se esiste uno standard, allineare `dq_helper` o migrare; altrimenti
consolidare il custom come soluzione ufficiale.

## Analisi tecnica
- Stato attuale: `dq_helper.py` (check S1..S7, orphan-rate, soglie) interno — vedi ADR-0014.
- Se Reply adotta uno standard: valutare porting dei check esistenti; mantenere le soglie note (orphan > 0.0%,
  Silver/Gold 0 FAIL).

## Sviluppo (diario)
- 2026-07-05 · in attesa; ri-sottomissione a Reply pianificata.

## Verifica
Decisione formalizzata + eventuale allineamento del `dq_helper` allo standard scelto.

## Esito
— (in attesa Reply)

## Follow-up
Collegato a OP-20 (alerting Databricks) e OP-25 (processo go-live).
