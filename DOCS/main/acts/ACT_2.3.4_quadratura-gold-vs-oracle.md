# ACT_2.3.4 · Quadratura Gold vs Oracle (PESO_NETTO, QTA_RICEVUTA)

**Status**: in-progress
**Type**: dq
**Origin**: sprint 2.3
**Sprint**: 2.3
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD — richiede ambiente cloud + Oracle
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.3.2, ACT_2.1.6 (backfill storico)   **Blocca**: ACT_2.4.3 (validazione BA)
**ADR collegate**: ADR-0006 (grain/misure F_CARICO)   **OP collegati**: —

## Contesto e motivazione
Il fact `gold_dev.logistica.F_CARICO` va quadrato contro l'Oracle legacy `CDT_DW.F_CARICO` (calcolato da ODI) sulle misure chiave per certificare la correttezza della migrazione. Lo script parametrico è pronto ma serve accesso a cloud+Oracle e allo storico ([[ACT_2.1.6]]). Piano dettagliato in `DOCS/main/07_certifica_gold_vs_cdtdw.md` §1.1.

> Nota misure: nell'implementazione le colonne sono `QTA_CARICO`/`QTA_UF_CARICO` e `PES_CARICO` (nomi ODI mantenuti per quadratura-per-nome, [[ADR-0006]] + fase_2 OP-NAMING). "QTA_RICEVUTA" e "PESO_NETTO" del titolo mappano su queste: CDT_DW non espone un `PESO_NETTO` separato — si confronta `PES_CARICO` (peso da anagrafica articolo).

## Analisi tecnica
- **Script**: `scripts/quadratura/quadratura_fact.py --fact CARICO` (parametrico, sostituisce il vecchio `quadratura_f_carico.py`). Confronto CDT_DW/ODI vs Gold/Delta.
- **Grain di confronto**: `(SITO canonico, PERIODO)` con `PERIODO` = giorno (default) o mese (`--per-mese`). Aggregato = `COUNT(*)` + `SUM` misure `QTA_CARICO`, `QTA_UF_CARICO`, `PES_CARICO`.
  - ⚠️ Il **COUNT righe non è comparabile** finché il grain non coincide: `CDT_DW.F_CARICO` è a grain **etichetta** (`≈ MAG_SITO_COD, NUM_DOC_CARICO, NUM_ETICH`); dopo il porting a grain etichetta ([[ADR-0006]]) il COUNT torna confrontabile. Il confronto su QTA/PESO resta valido a prescindere.
- **Semantica data**: lato CDT_DW `GIORNO_CARICO_ID` è FK surrogate → JOIN `CDT_DW.L_GIORNO` per `GIORNO_DT`; lato Gold `DATA_CARICO` (DATE).
- **Mapping sito**: `MAG_SITO_COD` (es. `0005C`) → codice canonico (`05`) via `CDT_ESTR.S_LOGISTIX` (`FLAG_ATTIVO=1`), `int(cifre)+zfill(2)` (memory `sito-mapping-slogistix`).
- **Lettura Gold**: diretta parquet via pandas/pyarrow **senza Spark**, contando SOLO i file live (`live_delta_files` legge `_delta_log` = add−remove) per non gonfiare con i tombstone da full_refresh (OP-CAR-4; memory `delta-tombstone-pyarrow-read`).
- **Soglia**: `--soglia` default 1.0% (in `07_certifica` la prima quadratura post-fix sito è stata a 5%). Colonne CDT_DW validate via `--discover`.
- **Connessione Oracle**: READ-ONLY, `.env` in `scripts/landing_simulator/` (`ORACLE_HOST/PORT/SERVICE/USER/PASSWORD`), stesso utente del cdtdw extractor. Non eseguibile offline.
- **Criticità note aperte** (`07_certifica_gold_vs_cdtdw.md`): (1) `PES_CARICO`/PESO_LORDO ≈ 0 in Gold in locale — la formula peso va presa da anagrafica articolo (`LU_ART_UNITA_LOGISTICA`), NON dalla pesata fisica (memory `odi-f-carico-grain-peso`); (2) landing storica incompleta → dipende da [[ACT_2.1.6]].
- Metodologia: `DOCS/main/08_playbook_certifica_wave.md`; runbook `09_runbook_recert_carichi_prepsped.md`.

## Sviluppo (diario)
- 2026-07-03 · SQL/script scritto; avanzamento ~20%; bloccato su accesso cloud+Oracle.

## Verifica
- `quadratura_fact.py --fact CARICO --discover` → colonne CDT_DW OK.
- `quadratura_fact.py --fact CARICO --da <da> --a <a> [--per-mese] --soglia <s>` → esce 0 (nessuna anomalia): scostamenti su `QTA_CARICO`/`QTA_UF_CARICO`/`PES_CARICO` entro soglia per ogni `(SITO, periodo)`, nessuna chiave "solo in ODI"/"solo in Gold" residua.
- Esito registrato in `07_certifica_gold_vs_cdtdw.md` (§1.1) con stato `OK`.

## Esito
— (in attesa di accesso cloud/PROD)

## Follow-up
Nessuna al momento.
