# ACT_0.1.7 · Grants least-privilege sugli schemi logistici

**Status**: in-progress
**Type**: infra
**Origin**: sprint 0.1   **Sprint**: 0.1   **Fase / Wave**: FASE 0 — Fondamenta
**Gg (stima)**: 2   **Blocco**: 🏗️ infra (gruppo reader non ancora creato lato piattaforma)
**Created**: 2026-07-05   **Closed**: —
**Dipende da**: ACT_0.1.2 (schemi), ACT_0.1.6 (apply brownfield)   **Blocca**: accesso MicroStrategy/analisti a Gold
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Gli schemi logistici richiedono accessi least-privilege: chi scrive (engineering) deve avere pieni
diritti sui tre layer, chi legge (analisti / MicroStrategy) solo `SELECT` su Gold. Il grant reader non è
attivabile finché il gruppo reader non esiste lato piattaforma → il grant è reso condizionale per non
bloccare l'apply del resto.

## Obiettivo
Grant applicati: `engineer_group` full sugli schemi logistici; reader con `SELECT` sul solo Gold, attivo
solo quando il gruppo reader esisterà. Fatto = writer verificato, reader gated senza errori di apply.

## Analisi tecnica
- File: `infra/terraform/brownfield/main.tf` — risorse grant.
- **Writer**: `Engineering-dev` confermato — gruppo engineering **trasversale** della piattaforma (vede
  retail + logistica: scelta intenzionale, non un over-grant da correggere).
- **Reader**: gruppo analisti/MicroStrategy **non ancora creato** → grant condizionale
  `enable_reader_grants=false`. Quando esisterà: `enable_reader_grants=true` + `group_readers=<nome>`.

## Sviluppo (diario)
- 2026-07-03 · writer confermato; reader gated a false.

## Verifica
Apply senza errori con reader gated; a gruppo reader creato → `enable_reader_grants=true` + apply + test:
il reader legge Gold, riceve **accesso negato** su bronze/silver.

## Esito
— (writer pronto; reader in attesa gruppo)

## Follow-up
Quando il gruppo reader è creato → riattivare grant + test accesso negato (chiude questa ACT).
