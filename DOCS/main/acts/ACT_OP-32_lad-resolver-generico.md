# ACT_OP-32 · LAD resolver generico (ri-risoluzione orphan Late-Arriving Dimensions)

**Status**: done   **Type**: feature   **Origin**: backlog L-01..L-04 / OP-32
**Sprint**: fuori-sprint (sviluppo tecnico offline)   **Fase / Wave**: trasversale (manutenzione Gold)
**Closed**: 2026-07-05
**Dipende da**: —   **Blocca**: chiusura residuo orphan ART/FORN (gated OP-02)
**ADR collegate**: ADR-0011 (LAD via `_COD_NAT`)   **OP collegati**: OP-32, OP-02 (residuo)

## Contesto
Quando un'anagrafica arriva **dopo** il fatto che la referenzia, la FK resta al sentinel −1 e non si
auto-corregge. L'`gold_late_arriving_handler` gestiva solo il late-arriving del *fatto* (Carichi), non
della *dimensione*. Serviva un job generico che ri-risolvesse gli orphan quando la dim arriva in ritardo.
Copre le attività backlog L-01..L-04 e chiude il framework OP-32.

## Obiettivo
Job generico, config-driven, che risolve le righe `FK=−1 AND NAT NOT NULL` via join sulla dim, idempotente
e non distruttivo, su tutti i fact core.

## Esito
Consegnato `notebooks/gold/maintenance/gold_lad_resolver.py` (parametrico su fact/fk/dim/nat_key; widget
env/fact_table/retail_master_schema/dry_run/retention_days). Chiave naturale `<dim>_COD_NAT` presente nei
**5 fact core** (F_CARICO, F_PREP_SPED, F_TURNO_PREP_SITO, F_TRASPORTO, F_ORDINI — L-01). Partitioning
preservato da `DESCRIBE DETAIL`. Validato runtime 2026-07-05: F_PREP_SPED 77 orphan `ART_RADICE_COD` →
segnalati per quarantena (residui = articoli non nel master, **gated OP-02**); F_CARICO CORRIERE_COD (NAT
null) correttamente skippato. **Residui** (non bloccanti): risoluzione ART/FORNITORE richiede Retail Master
completo (OP-02); quarantena oggi solo segnalazione DQ; scheduling dopo `dim_refresh` dipende da FASE 0
(L-03/L-04 pendenti). Dettaglio in [[op32-late-arriving-dimensions]].

## Follow-up
- L-03 (scheduling LAD dopo dim_refresh nei workflow) e L-04 (test idempotenza) → dipendono da deploy PROD.
- Chiusura residuo ART/FORN → alla risoluzione di OP-02 (Retail Master).
