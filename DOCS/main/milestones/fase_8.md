# Milestone — FASE 8: Shadow Mode, Validazione & Cut-Over

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (8.1–8.4).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (4/27 gg) — bozze piani pronte; esecuzione bloccata da provisioning infra PROD

## 1. Executive summary (funzionale)
Fase finale di **messa in produzione**: deploy su PROD, esecuzione in **shadow mode** (Databricks in parallelo a Oracle con quadratura giornaliera), validazione, e **cut-over** con spegnimento del flusso legacy. È la fase che porta il progetto in esercizio.

## 2. Perimetro
Provisioning PROD, shadow mode ≥ 10 giorni (target delta ≤ 0.1% su ≥ 95% giorni), piani di rollback/cut-over, go-live e stabilizzazione post-live.

## 3. Deliverable (in preparazione)
Quadratura automatica giornaliera, runbook operativo PROD, report shadow mode, Rollback Plan (`DOCS/piani/rollback_plan.md`), Cut-Over Plan (`DOCS/piani/cutover_plan.md`), comunicazione utenti, retrospettiva finale.

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 8.1 | Shadow Mode Setup | 🔵 PARZ. | [8.1](../sprint_agile/sprint_8.1.md) |
| 8.2 | Shadow Mode Run (10+ gg) | 🔵 PARZ. | [8.2](../sprint_agile/sprint_8.2.md) |
| 8.3 | Preparazione Cut-Over | 🔵 PARZ. | [8.3](../sprint_agile/sprint_8.3.md) |
| 8.4 | Cut-Over & Stabilizzazione | ⏳ | [8.4](../sprint_agile/sprint_8.4.md) |

## 5. Prerequisiti bloccanti
- **Provisioning Azure Databricks Workspace PROD + ADLS Gen2** (I-01): prerequisito assoluto di tutta la fase.
- Naming catalog PROD `_prod` (D4) — configurazione PROD non ancora attivata.
- Approvazione shadow mode → sblocca cut-over.

## 6. Punti risolti
- Bozze piani (rollback, cut-over, comunicazione) predisposte.
- Logica quadratura automatica scritta offline.

## 6bis. Criteri di accettazione (parallel run / shadow mode)
- **Delta ≤ 0.1%** su **≥ 95%** dei giorni shadow (target D-06).
- **Orphan-rate 0.0%** mantenuto (R-01).
- Silver/Gold **0 FAIL** (R-02/R-03).
- Limiti noti da **verbalizzare** coi criteri di tolleranza (OP-24): grain pesata (OP-CAR-5) e listini corrieri assenti (costi trasporto non valorizzati).
- **Strumento quadratura:** `scripts/quadratura/quadratura_fact.py` (parametrico per fact, sito×periodo vs CDT_DW). Su Databricks gira Spark-native (nessun problema tombstone). Quadrature Q-01…Q-04 su F_CARICO/F_GIACENZE/F_PREP_SPED/F_TRASPORTO.

## 7. Punti aperti
- Tutta l'esecuzione dipende dal **provisioning PROD** (non ancora avviato).
- **V-04** — stress test idempotenza su PROD.
- **OP-24** — criteri di accettazione del parallel run (da concordare con Reply).
- **OP-25** — processo formale di go-live (Reply).
- **OP-22** — SLA di risposta ai failure (runbook).
- Sign-off finale e go/no-go.

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Spegnimento Oracle ODI: **disabilitare, non eliminare** gli oggetti legacy (rollback safety).
- Ambiente stage `_stage`: non configurato per questo rilascio.

## 9. Sviluppi futuri
- Attivazione ambiente PROD (e stage se necessario) alla data di rilascio.
- Automazione completa monitoraggio quadrature post go-live.

## 10. Riferimenti
`../06_backlog.md` (§2 Deploy, §6 Cut-Over), `DOCS/piani/cutover_plan.md`, `DOCS/piani/rollback_plan.md`, `../sprint_agile/` (8.1-8.4).
