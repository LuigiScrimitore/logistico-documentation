# ACT_9001 · Rebuild F_CARICO a grain etichetta (catena WL_CARICO)

**Status**: done   **Type**: feature   **Origin**: emerged (allineamento ODI grain carico)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (Wave A Carichi)
**Closed**: 2026-07-04
**Dipende da**: estrazione `LU_ART_UNITA_LOGISTICA`   **Blocca**: certifica F_CARICO ([[ACT_9000]])
**ADR collegate**: ADR-0006 (grain etichetta + peso da anagrafica)   **OP collegati**: OP-CAR-2, OP-CAR-5

## Contesto
La certifica ha mostrato che `CDT_DW.F_CARICO` è a grain **per etichetta** (chiave ≈ SITO+NUM_DOC+NUM_ETICH),
mentre il nostro Gold era a grain riga-dettaglio (testata⋈dettaglio semplificato). Allinearsi = ricostruire
la catena worklist ODI `PESATE/STO_* → WL2 → WL3 → WL4 → T_CARICO`, non un ritocco. Fonte autoritativa:
`DOCS/99. SCRIPT/CDT_ESTR.sql` + `CDT_SA.sql` (non `mapping_carichi.md`, speculativo). Vedi [[odi-f-carico-grain-peso]].

## Obiettivo
`gold_f_carico` a grain etichetta, con `PES_CARICO`/`VOL_CARICO` da **anagrafica articolo**
(`LU_ART_UNITA_LOGISTICA`), non dalla pesata fisica; LAD handler allineato.

## Esito
Costruita la catena `silver` WL_CARICO a grain etichetta; articolo pesata risolto via **MSI** (OP-CAR-2:
`PSP_ARTEAN13` = codice MSI, overlap 100% con `dettaglio.MSI_COD` → nessuna anagrafica EAN/sorgente morta
necessaria). `PES_CARICO = ART_UNITA_LOGISTICA_PESO_LORDO × QTA_UF_CARICO` (o QTA_UF se ART_MODL_PES>1);
`VOL_CARICO = QTA_CARICO × ALT×LAR×PRO / 1000`. `LU_ART_UNITA_LOGISTICA` aggiunta al cdtdw extractor
(READ-ONLY, `ART_UNITA_LOGISTICA_COD=1`). `gold_f_carico` + `gold_late_arriving_handler` allineati al nuovo
grain. Grain INNER-join pesata confermato fedele all'ODI (OP-CAR-5). Peso fisico pesato → fact separato F_PESATE.
