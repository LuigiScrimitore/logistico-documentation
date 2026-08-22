# ACT_9000 · Certificazione strutturale Gold vs CDT_DW (wave A0-A9)

**Status**: in-progress
**Type**: analysis
**Origin**: emerged (ri-certifica fact Gold vs Oracle/ODI)   **Sprint**: fuori-sprint (emergente)
**Fase / Wave**: trasversale (qualità Gold)   **Gg (stima)**: —
**Blocco**: ☁️ quadratura dati + pruning column-level = cloud-gated (Oracle READ-ONLY / `--discover` live)
**Created**: 2026-06-25   **Closed**: —
**Dipende da**: [[ACT_9001]] (rebuild F_CARICO), P-01 mapping sito   **Blocca**: sign-off funzionale wave
**ADR collegate**: ADR-0006, ADR-0008, ADR-0013 (F_TRASPORTO MTV)   **OP collegati**: OP-CAR-3/4/5, OP-PSP-1/2, OP-MOV-1

## Contesto e motivazione
Emerso dalla ri-certifica di `F_CARICO`/`F_PREP_SPED`: serve verificare, per ogni fact Gold, la fedeltà alla
controparte CDT_DW (grain, colonne, misure) col playbook A0-A9. **SSOT del dettaglio** =
[`07_certifica_gold_vs_cdtdw.md`](../07_certifica_gold_vs_cdtdw.md); metodologia in
[`08_playbook_certifica_wave.md`](../08_playbook_certifica_wave.md); runbook in
[`09_runbook_recert.md`](../09_runbook_recert.md). Questa ACT è il **tracker** del work-stream, non ne duplica
il contenuto.

## Obiettivo
Ogni fact Gold certificato strutturalmente vs CDT_DW (decode reale + pruning + eventuale riscrittura) e poi
quadrato sui dati entro soglia, oppure con divergenze **deliberate e documentate**.

## Analisi tecnica
- **Certificati end-to-end**: F_CARICO, F_PREP_SPED (P1-P8 fatti; P9 quadratura dati cloud-gated).
- **Decode A0-A2 fatto per tutti (2026-07-05)**: F_TRASPORTO (scope **MTV** deliberato, ADR-0013),
  F_ORDINI (scope **fornitore** deliberato), F_TURNO_PREP_SITO / F_TRACCIABILITA_LOTTI / F_GIACENZE_DAILY
  (allineati, resta pruning column-level), dimensioni LU_* (lookup 1:1).
- **Unica sovra-semplificazione accidentale**: F_MOVIMENTAZIONE → risolta in [[ACT_9003]] (NUM_PLT).
- **Findings certifica** (CERT-01..06, backlog §5i): tombstone quadratura → [[ACT_9006]]; SCARTATE (OP-PSP-1)
  e DATA_PREL_INIZ (OP-PSP-2) risolti; OP-CAR-5 grain INNER confermato; OP-CAR-3 → [[ACT_9002]].

## Sviluppo (diario)
- 2026-07-01 · F_CARICO fix sito (S_LOGISTIX), grain etichetta deciso.
- 2026-07-02 · F_PREP_SPED P7-P8; script quadratura parametrico.
- 2026-07-05 · decode A0-A2 completato per tutti i fact + dimensioni; triage strutturale chiuso.

## Verifica
Per ogni fact: decode documentato in `07`; quadratura `scripts/quadratura/quadratura_fact.py --fact ...`
entro soglia (cloud) o divergenza documentata.

## Esito
F_CARICO/F_PREP_SPED certificati (dati cloud-gated); decode strutturale completo per gli altri 6 + LU_*.
Residuo: pruning column-level fine + quadratura dati vs Oracle = **cloud-gated**. Stato in
[[certifica-gold-vs-cdtdw-stato]].

## Follow-up
Quadratura dati per-fact all'accesso cloud; verifica aggregati DM via MicroStrategy.
