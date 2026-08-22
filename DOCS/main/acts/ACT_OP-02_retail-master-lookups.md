# ACT_OP-02 · Lookup master Retail (nomi/percorsi + permessi lettura)

**Status**: on-hold   **Type**: analysis   **Origin**: open-point OP-02 (dip. Reply)
**Sprint**: fuori-sprint (dipendenza Reply)   **Fase / Wave**: trasversale (anagrafiche Gold)
**Gg (stima)**: —   **Blocco**: 🤝 Reply (schema/nomi lookup master Retail)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: risposta Reply (schema master Retail)   **Blocca**: join master ART/FORN in Gold, chiusura residuo [[ACT_OP-32]]
**ADR collegate**: ADR-0008 (chiavi naturali Gold)   **OP collegati**: OP-02, OP-01, OP-04, OP-05

## Contesto e motivazione
Le fact Gold portano le chiavi naturali e la join alle anagrafiche master è oggi **commentata** (D2 = LU_*
in `bronze_dev.condiviso`, ADR-0002). Per agganciare definitivamente ART/FORNITORE al Retail Master servono
i nomi/percorsi esatti delle lookup (`LU_ART_RADICE`, `LU_FORNITORE`, `LU_PDV`, `LU_GIORNO`, `LU_MESE`) e i
permessi di lettura. È il **blocker** che tiene i residui orphan ART/FORN del LAD resolver (ACT_OP-32) in
quarantena.

## Obiettivo
Ricevere da Reply schema e nomi esatti (es. `gold_prod.<schema_master>.LU_ART_RADICE`) + grant di lettura;
ripuntare `retail_master_schema` e abilitare le join master oggi commentate.

## Analisi tecnica
- Placeholder attuale: `retail_master_schema = gold_prod.condiviso` (dormiente).
- Alla risposta: ripuntare lo schema, decommentare le join master nei notebook Gold, ri-eseguire il LAD
  resolver (ACT_OP-32) per risolvere i residui ART/FORN.
- Collegati: OP-01 (schema condiviso non previsto da Reply), OP-04 (confine merceologica logistica vs Retail),
  OP-05 (arricchimenti logistici su master).

## Sviluppo (diario)
- 2026-07-02 · D2 confermato (LU_* in `bronze_dev.condiviso`); join master commentate; in attesa OP-02.

## Verifica
Join master attive; residui orphan ART/FORN del LAD resolver → risolti (non più in quarantena).

## Esito
— (in attesa Reply)

## Follow-up
Alla risoluzione: chiudere il residuo di ACT_OP-32; rivalutare OP-01/04/05.
