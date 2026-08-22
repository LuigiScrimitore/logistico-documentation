# ACT_8.3.2 · Cut-Over Plan dettagliato (sequenza, timing)

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.3
**Sprint**: 8.3 — Preparazione Cut-Over
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 2
**Blocco**: ☁️ finalizzazione dipende dall'esito shadow mode
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.2.4   **Blocca**: ACT_8.4.1
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: OP-25 (processo formale di go-live)

## Contesto e motivazione
Il go-live va eseguito in modo controllato: serve un piano di cut-over dettagliato con sequenza operativa,
timing e criteri go/no-go, così che l'esecuzione (ACT_8.4.1) sia deterministica e ripetibile. La finestra
utente di indisponibilità reportistica MicroStrategy è **< 2h** (sprint 8.3). È il documento base del
processo formale di go-live (OP-25).

## Obiettivo
Cut-Over Plan dettagliato con sequenza e timing. Fatto = piano passo-passo con tempistiche, responsabili e
criteri di go/no-go, pronto per l'esecuzione e distribuito al team 7 giorni prima del go-live.

## Analisi tecnica
- **Bozza esistente**: `DOCS/piani/cutover_plan.md` v1.0 (2026-05-29), già strutturata (PARZ. 50%) —
  finalizzazione dopo il sign-off shadow (ACT_8.2.4).
- **Contenuti del piano** (`piani/cutover_plan.md`):
  - **Pre-requisiti d'ingresso** (§1, firmati dal PM ≥ 48h prima): 12 voci — shadow ≥ 10 gg con report
    delta < 0.5% (ACT_8.2.4), DQ score > 95%, approvazioni PM+BA, comunicazione utenti > 7 gg (ACT_8.3.3),
    comunicazione a sistemi dipendenti (AtTraspo, Logistix), Oracle/ODI congelati 72h, ambiente Databricks
    validato (workflow < 4h), connection string MicroStrategy testata (ACT_8.3.4), rollback distribuito
    (ACT_8.3.1), backup Oracle < 24h, ticket Azure Premium P2 aperto.
  - **Finestra & presidio** (§2): sabato notte **22:00 → 02:00** (4h) + presidio 02:00–08:00; team Cloud
    Architect/DBA Oracle/Team BI/BA/PM; canali Teams "Logistico 2.0 — CutOver Night" + WhatsApp backup.
  - **Sequenza step-by-step con orari** (§3): T-7gg comunicazione utenti; T-1gg verifiche; T=22:00 freeze
    Oracle (`DB_PARMS`=FREEZE, 0 job ODI running); T=22:15 ultimo ciclo ODI sync
    (`CDT_SA.SP_CARICA_CDT_SYNC`); T=22:30 backfill finale Databricks (`ops/backfill_completo.py`);
    T=23:30 quadratura finale (`ops/quadratura_cutover.py`, CDT_DW vs gold, delta < 0.5%); T=00:00 redirect
    MicroStrategy DB instance a `LOGISTICO_DWH_DATABRICKS` + invalidate cache; T=00:30 smoke test 15 check;
    T=01:00 comunicazione go-live; T=01:00–08:00 presidio.
  - **Smoke test** (§4): 15 check funzionali su report MicroStrategy (5 critici ★); criterio 12/15 OK,
    0 critici KO.
  - **Criteri go/no-go per fase** (§5) e **matrice escalation** (§6).
- **Coerenza** con rollback (ACT_8.3.1: gli stessi trigger/soglie), comunicazione utenti (ACT_8.3.3:
  finestra allineata < 2h), permessi PROD (ACT_8.3.4: connection string MSTR) e runbook (ACT_8.1.5).
- **Note da definire alla pianificazione**: data specifica finestra, contatti/accessi (§7 oggi placeholder).

## Sviluppo (diario)
- 2026-07-03 · bozza `piani/cutover_plan.md` (PARZ. 50%).

## Verifica
- Piano con sequenza numerata a orari, timing, responsabili e punti go/no-go; smoke test 15 check definito.
- **Prova a tavolino** con gli attori coinvolti; distribuzione al team ≥ 7 gg prima del go-live.

## Esito
— (parziale: bozza in corso)

## Follow-up
Nominare data finestra e compilare contatti/accessi (§7). Formalizzare processo go-live con Reply (OP-25).
