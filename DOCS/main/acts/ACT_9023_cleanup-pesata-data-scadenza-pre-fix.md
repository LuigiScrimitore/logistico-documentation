# ACT_9023 · Cleanup righe pesata con DATA_SCADENZA pre-fix (full_refresh)

**Status**: proposed
**Type**: fix (manutenzione dati)
**Origin**: emerged (follow-up [[ACT_9021]])
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: FASE 2 — Wave A Carichi
**Gg (stima)**: <0.5
**Blocco**: nessuno (azione in DEV)
**Created**: 2026-09-02   **Closed**: —
**Dipende da**: [[ACT_9021]] (fix JDN, mergiato)   **Blocca**: quadratura pulita pesate
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Dopo il fix JDN ([[ACT_9021]], PR #2), in `silver_dev.logistica.pesata` restano **93 righe** scritte dal run
**pre-fix** del 2026-09-02 (`_silver_ts` 09:25, vecchio `.cast("date")`) con `DATA_SCADENZA` malformata
(anno ~2461321). Il MERGE incrementale di `silver_pesate` **non le corregge** perché sono pesate con chiave
diversa da quelle del delta corrente → non matchate. Le righe post-fix (17.102, `_silver_ts` 14:50) sono corrette.

## Obiettivo
`silver_dev.logistica.pesata` senza righe con `YEAR(DATA_SCADENZA)` fuori range (nessun anno > 3000).

## Analisi tecnica
`silver_pesate` espone il widget **`full_refresh`** (default false). Un run con `full_refresh=true` riprocessa
l'intero bronze pesate applicando `julian_to_date` a tutte le righe → riscrive la tabella pulita. In alternativa
le 93 righe si auto-correggono quando quelle chiavi rientrano in un delta futuro (ma non garantito a breve).
NB: `logistica_carichi` (job) non passa `full_refresh` come parametro → serve lanciare il notebook `silver_pesate`
con `full_refresh=true` (via `databricks bundle run ... --params` se esposto, o run notebook mirato), o un giro
one-off. Coordinare col watermark (il full_refresh ignora l'incrementale).

## Verifica
`SELECT COUNT(*) FROM silver_dev.logistica.pesata WHERE YEAR(DATA_SCADENZA) > 3000` = **0**.

## Esito
— (proposed)

## Lezioni
Correlata a [[LL-022]] (le righe corrotte erano pre-fix; la lezione previene il ripetersi).

## Follow-up
- Valutare se esporre `full_refresh`/`process_from` come parametri del job `logistica_carichi` (riusabile,
  gotcha watermark [[LL-021]]) → eventuale ACT dedicata.
