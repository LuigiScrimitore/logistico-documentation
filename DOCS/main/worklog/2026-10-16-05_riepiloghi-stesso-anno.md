---
data: 2026-10-16
titolo: "Estrattore: i riepiloghi collegati alle liste vanno presi dello stesso anno (numeri riciclati) — correzione + pulizia di 666 riepiloghi 2019–2025"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "split dopo merge"
push_gitlab: "nessuno (estrattore sul relay odi3: copia a mano)"
act: [ACT_9030]
adr: []
lesson: [LL-006]
op: [OP-INF-4]
---

## Contesto
Recupero di ottobre ([[ACT_9030]]), `logistica_prep_sped` del 07/10: dopo la correzione di `julian_to_date`
(worklog 2026-10-16-04) il `dq_gate` blocca su `orphan_PREPARATORE_COD` di `F_TURNO_PREP_SITO`: 2 righe del
**15/11/2021** (sito 05, preparatore 70119).

## Diagnosi
La selezione `parent` di `storico_riepiloghi` collega i riepiloghi alle liste selezionate con (sito, nro riepilogo,
negozio). **I numeri di riepilogo si riciclano negli anni**: insieme al riepilogo del 2026 arrivano quelli degli anni
precedenti con lo stesso numero. Il legacy (`package_replica_prep_sped_new.sql`, `ESTRAI_PREP_SPED.sql`) mette in più
la condizione **stesso anno** tra `LSPRL_DATA_PREPARAZ` e `RPLPR_DATA_PREPARAZ` (`TO_CHAR(TO_DATE(...,'J'),'yyyy')`),
che non era stata replicata.
Effetto: **666 riepiloghi 2019–2025** nel bronze `storico_riepiloghi` (caricamenti del recupero 01–07/10) e da lì in
`prep_riepilogo`, `turno_prep_sito`, `F_TURNO_PREP_SITO` (stesse 666 righe). Prima del recupero non ce n'erano.
Possibile effetto anche su `logistica_curated.prep_sped` (join liste ↔ riepiloghi senza data): si ricalcola con la
chiusura del recupero.

## Decisioni
1. Estrattore: nelle chiavi `parent` ammessa la forma `YEAR_J(<colonna>)` = anno della data giuliana
   (`CASE WHEN col > 0 THEN TO_CHAR(TO_DATE(col,'J'),'YYYY') END`, lo `0` non è una data valida per Oracle). Riepiloghi:
   chiave in più `[YEAR_J(RPLPR_DATA_PREPARAZ), YEAR_J(LSPRL_DATA_PREPARAZ)]`, come il legacy.
2. Pulizia (Delta `DELETE`, recuperabile con il time travel; versioni registrate nella fotografia del recupero): righe
   con data di preparazione precedente al 2026 da `bronze_dev.logistica.storico_riepiloghi`,
   `silver_dev.logistica.prep_riepilogo`, `silver_dev.logistica_curated.turno_prep_sito`,
   `gold_dev.logistica.F_TURNO_PREP_SITO`, `gold_dev.logistica_dm.A_TURNO_PREP_SITO`.
3. Copia su odi3 dell'estrattore corretto **prima del job ODI delle 06:00 del 17/10**.

## Esito
- PR [#42](https://github.com/LuigiScrimitore/Logistico2.0/pull/42) mergiata. Verifica Oracle (bolle timbrate 07/10): riepiloghi
  selezionati tutti del 2026 (8.500). Pulizia: 666 righe pre-2026 cancellate da bronze (versione prima: 60), silver
  `prep_riepilogo` (125), `turno_prep_sito` (104), `F_TURNO_PREP_SITO` (80); `A_TURNO_PREP_SITO` già pulita.
- I file di recupero nella landing (estratti prima della correzione) contengono ancora i riepiloghi vecchi: il rilancio
  07–16/10 è stato fatto **escludendo `bronze_prep_riepiloghi`** (verificato: 0 righe pre-2026 dopo il rilancio).
- Da fare: copia dell'estrattore corretto su odi3 **prima del job ODI delle 06:00 del 17/10**, rigenerazione dei soli
  riepiloghi 01–16/10, passaggio mirato su Databricks (riepiloghi → turni → `prep_sped` con `full_refresh`).
