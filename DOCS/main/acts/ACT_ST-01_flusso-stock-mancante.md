# ACT_ST-01 · Flusso stock mancante (`cndstostock` / VAL_STOCK)

**Status**: on-hold   **Type**: analysis   **Origin**: backlog ST-01, ST-02
**Sprint**: fuori-sprint (analisi)   **Fase / Wave**: trasversale (Giacenze/Carichi)
**Gg (stima)**: —   **Blocco**: 🟠 sorgente (`cndstostock` dismessa, dati fermi al 2020)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: identificazione sorgente stock as-is   **Blocca**: valorizzazione `VAL_STOCK_*` / `VAL_COSTO_CARICO`
**ADR collegate**: —   **OP collegati**: OP-CAR-1 (VAL_COSTO_CARICO NULL)

## Contesto e motivazione
Il flusso `silver_t_stock` → `silver.logistica.cndstostock_clean` è assente dall'analisi as-is: la sorgente
`cndstostock` risulta dismessa (dati fermi al 2020). Di conseguenza i campi `VAL_STOCK_*` restano a 0 e
`VAL_COSTO_CARICO` è NULL (OP-CAR-1, fisiologico). Va deciso se e come recuperare il dato valore-stock.

## Obiettivo
Identificare la sorgente reale dello stock a valore nell'as-is (CND? Logistix?) e documentarla nel mapping
(ST-01); implementare il flusso solo se la sorgente è disponibile e prioritizzata con BA (ST-02).

## Analisi tecnica
- Oggi: nessun flusso valore-stock; `VAL_STOCK_*`=0. Collegato a OP-CAR-1.
- ST-01 (prerequisito): tracciare la sorgente nel `02_pipeline_mapping.md` come gap noto.
- ST-02 (successivo): implementare se sorgente disponibile.

## Sviluppo (diario)
- 2026-07-05 · gap documentato; sorgente non identificata.

## Verifica
Sorgente stock identificata e documentata; (se implementato) `VAL_STOCK_*` valorizzati e quadrati.

## Esito
— (in attesa identificazione sorgente / priorità BA)

## Follow-up
ST-02 dopo ST-01. Rivalutare con BA.
