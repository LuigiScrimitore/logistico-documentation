# FASE 8 — Shadow Mode, Validazione & Cut-Over

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** — | **Stato:** 🔴 bloccata da cloud (dipende FASE 0)

## 1. Obiettivo & scope
Validare il nuovo flusso in parallelo all'ODI legacy (shadow mode), quadrare i fact vs CDT_DW, e
gestire il cut-over con rollback plan. È la fase di go-live.

## 2. Prerequisiti
FASE 0 completata (provisioning brownfield), tutte le wave fact deployate su Databricks, push sorgenti
attivo su landing.

## 3. Attività
| # | Attività | Rif. |
|---|---|---|
| D-02 | Backfill storico completo (22 siti, da go-live) | script pronti |
| D-06 | Shadow mode ≥ 10 giorni (delta ≤ 0.1% su ≥ 95% giorni) | monitoring |
| Q-01..Q-04 | Quadrature F_CARICO/F_GIACENZE/F_PREP_SPED/F_TRASPORTO vs Oracle | `quadratura_fact.py` |
| V-01..V-08 | Validazioni funzionali con BA per wave + sign-off KPI | — |
| C-01..C-08 | Rollback plan, cut-over plan, esecuzione, verifica D+0/D+1, spegnimento ODI | bozze pronte |

## 4. Quadratura (strumento certificato)
`scripts/quadratura/quadratura_fact.py` (parametrico per fact, sito×periodo vs CDT_DW). Su Databricks
gira Spark-native (nessun problema tombstone). **D5**: confermare canale di lettura del DWW legacy
(diretto vs export su landing).

## 5. Criteri di accettazione
- Delta ≤ 0.1% su ≥ 95% dei giorni shadow (target D-06).
- Orphan-rate 0.0% mantenuto (R-01).
- Silver/Gold 0 FAIL (R-02/R-03).
- Note certifica wave: OP-CAR-5 (grain pesata) e listini corrieri sono limiti noti da verbalizzare
  coi criteri di tolleranza (OP-24).

## 6. Open points di fase
- OP-24 criteri accettazione parallel run (Reply).
- OP-25 processo formale go-live (Reply).
- OP-22 SLA risposta ai failure (runbook).

## 7. Stato & dipendenze
Bloccata da cloud. Bozze `cutover_plan.md`/`rollback_plan.md` pronte. Dipende da FASE 0-7.

## 8. Riferimenti
`../06_backlog.md` §2/§3/§4/§6, `DOCS/cutover_plan.md`, `DOCS/rollback_plan.md`,
`../09_runbook_recert_carichi_prepsped.md`, `scripts/quadratura/quadratura_fact.py`.
