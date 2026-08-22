# ACT_DQ-01 · Analisi chiave `silver_storico_bolle_uniche` (DQ S7)

**Status**: done   **Type**: analysis   **Origin**: backlog DQ-01, DQ-02, DQ-03
**Sprint**: fuori-sprint (analisi)   **Fase / Wave**: trasversale (DQ Silver)
**Closed**: 2026-06-20
**ADR collegate**: —   **OP collegati**: — (check DQ S7)

## Contesto
Il check DQ S7 segnalava che `BOL_NRO_BOLLA` varia all'interno della chiave di aggregazione (8 colonne) di
`silver_storico_bolle_uniche`, sollevando il dubbio che la chiave fosse troppo larga o semanticamente errata
(il `MIN()` tecnico su valori multipli poteva produrre incoerenze a valle).

## Obiettivo
Stabilire se `BOL_NRO_BOLLA` vada nelle KEYS o sia atteso variare; correggere se errata; tracciare i record
a bolla non costante.

## Esito
**Chiave a 8 colonne CONFERMATA corretta** (replica WL1 legacy): `BOL_NRO_BOLLA` **non** è chiave — una
gabbia/ordine può coprire più bolle; la varianza segnalata da S7 è un'anomalia dati **upstream** (Oracle),
non un difetto del modello (DQ-01, da confermare con BA in validazione). **No-action** su DQ-02: aggiungere
`BOL_NRO_BOLLA` cambierebbe il grain e spezzerebbe il JOIN con `storico_liste_uniche`; il warning S7 resta
informativo, non bloccante. **DQ-03 done**: aggiunto flag booleano `_bolla_multipla`
(`COUNT(DISTINCT BOL_NRO_BOLLA)>1` per chiave di prelievo) in `silver_storico_bolle_uniche.py`, utile per
auditing a valle in `silver_prep_prep_sped`.
