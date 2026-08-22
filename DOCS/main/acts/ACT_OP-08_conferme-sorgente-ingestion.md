# ACT_OP-08 · Conferme sorgente su ingestion (delta/naming/filtri/swap)

**Status**: on-hold   **Type**: analysis   **Origin**: open-point OP-08, OP-09, OP-10, OP-11, OP-31
**Sprint**: fuori-sprint (dipendenza sorgente)   **Fase / Wave**: trasversale (Bronze/landing)
**Gg (stima)**: —   **Blocco**: 🟠 sorgente (Logistix/CND/STAT) + parziale Reply
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: conferme sistemi sorgente   **Blocca**: irrigidimento modalità Bronze / scheduling
**ADR collegate**: ADR-0010 (incrementale)   **OP collegati**: OP-08, OP-09, OP-10, OP-11, OP-31

## Contesto e motivazione
Diversi comportamenti di ingestion sono implementati secondo l'analisi as-is ma **da confermare** con i
sistemi sorgente. Finché non confermati restano rischi latenti (doppio conteggio, separatore CSV, finestre).
Raggruppati qui perché condividono l'interlocutore (sorgente) e la natura (conferma, non sviluppo).

## Obiettivo
Ottenere dalle sorgenti le conferme che irrigidiscono le scelte Bronze/scheduling.

## Analisi tecnica
- **OP-08** — FULL vs DELTA e naming file: delta per transazionali? full per anagrafiche/giacenze? un
  file/giorno `YYYY/MM/DD` o intra-day con timestamp? separatore CSV per sorgente (CND as-is usava `,`,
  Bronze usa `;` → valutare widget).
- **OP-09** — SLA push confermato entro le **04:00** (call 2026-07-03); azione: ri-fasare scheduling Workflows
  dopo le 04:00 (landing check 04:30, processing 05:00) quando i Workflows esisteranno (DBR-06).
- **OP-10** — filtro statico `AREE_MERCEOLOGICHE WHERE ARM_TIPO_AREA = 1`: applicato a monte o Bronze deve
  mantenerlo?
- **OP-11** — carichi trasferiti via SWAP (`STCAR_TRASFERITO_SWAP`): come sono marcati nel delta (rischio
  doppio conteggio)?
- **OP-31** — validazioni delta sorgente: semi-join `ESTRAI_SPEDIZIONI` (oggi finestra piena su
  `SP_DATABOLLA`); `merge_keys`/`date_column` di `spedizioni`/`storico_liste` da validare su più giorni.

## Sviluppo (diario)
- 2026-07-03 · OP-09 SLA confermato (04:00); restanti in attesa sorgente.

## Verifica
Ogni sotto-punto confermato dalla sorgente e recepito (widget/scheduling/filtri) senza regressioni sul delta.

## Esito
— (OP-09 SLA confermato; resto in attesa)

## Follow-up
OP-09 → riscadenzare i Workflows (collegato a DBR-06 / sprint deploy). Restanti → recepire alla conferma.
