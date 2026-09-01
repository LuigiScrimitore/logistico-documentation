# Piano di Sviluppo — Logistico 2.0

**Ultimo aggiornamento:** 2026-08-27  
**Versione documento:** 3.1 (stato corrente + certifica wave + readiness brownfield)  
**Progetto:** Logistico 2.0 — CNO Data Platform  
**Stack:** PySpark · Delta Lake · Azure ADLS Gen2 · Unity Catalog · Databricks Workflows · GitLab CI/CD · Terraform

> 🧭 **Navigazione**: attività → [`acts/`](acts/) · decisioni → [`adr/`](adr/) · indice unico →
> [`15_backlog_master.md`](15_backlog_master.md). Stato di avanzamento → `sprint_agile/`.

> **SSOT:** questo file in `docs/main/` è la versione canonica, aggiornata giornalmente.  
> Il file Excel `DOCS/Piano di Sviluppo - Logistico 2.0.xlsx` viene aggiornato on-demand per i SAL con il cliente.

---

## 1. Stato Globale del Progetto

| Fase | Descrizione | Sprint | Gg totali | Gg completati | Stato | Note |
|------|-------------|--------|-----------|---------------|-------|------|
| **FASE 0** | Fondamenta Infrastrutturali | 0.1–0.3 | 18 | 13 | 🔵 IN CORSO | Sprint 0.1 IN CORSO (Terraform scritto, apply pendente provisioning workspace); D1/D2/D3/D5 ✅ decisi; 0.1.4 ridisegnata (AKV → GitLab CI/CD); 0.2/0.3 ✅; **multi-repo eseguito**: 4 repo GitHub + 3 su GitLab con CI in DEV via Managed Identity — lib (wheel nel Package Registry ✅), workflows (deploy_dev DEV ✅, 7 job), infrastructure (plan DEV ✅, apply in attesa grant UC alla MI — OP-INF-1). ACT_9011/9017/9018 |
| **FASE 1** | Master Data & Dimensioni | 1.1–1.3 | 19 | 17 | 🔵 PARZ. | DIM offline ✅; first-run landing + workflow yml da eseguire su cloud |
| **FASE 2** | Wave A — Carichi (Inbound) | 2.1–2.4 | 26 | 21 | 🔵 PARZ. | F_CARICO 0.0% orphan locale; backfill/quadratura/BA-validation pendenti |
| **FASE 3** | Wave B — Giacenze (Stock) | 3.1–3.4 | 26 | 22 | 🔵 PARZ. | T_STOCK OK locale; backfill/quadratura/BA-validation pendenti |
| **FASE 4** | Wave C — Prep Spedizioni | 4.1–4.5 | 33 | 28 | 🔵 PARZ. | Row-hash pruning ~22%; backfill/quadratura/edge-cases/BA pendenti |
| **FASE 5** | Wave D — Trasporti | 5.1–5.4 | 28 | 23 | 🔵 PARZ. | F_TRASPORTO OK locale; backfill/quadratura/BA-validation pendenti |
| **FASE 6** | Wave E — Tracciabilità & Carrellisti | 6.1–6.3 | 19 | 17 | 🔵 PARZ. | CE178, missioni, sessioni OK; workflow yml + validazione funzionale pendenti |
| **FASE 7** | KPI Aggregati & Reporting | 7.1–7.3 | 19 | 12 | 🔵 PARZ. | DataMart + KPI views OK; MicroStrategy/tuning/validazione BA pendenti |
| **FASE 8** | Shadow Mode & Cut-Over | 8.1–8.4 | 27 | 4 | 🔵 PARZ. | Bozze piani preparate; esecuzione bloccata da provisioning infra prod |
| | **TOTALE** | | **216** | **158** | | |

**Ultimo run validato (2026-06-17):** Bronze 36/36 ✅ · Silver 45/45 ✅ · Gold 26/26 ✅ · Orphan rate 0.0%

---

## 2. KPI di Progetto

| Metrica | Valore attuale | Obiettivo | Stato |
|---------|---------------|-----------|-------|
| Notebook Bronze operativi | 39 | 39 | ✅ |
| Notebook Silver operativi | 46 | 46 | ✅ |
| Notebook Gold operativi | 26 | 26 | ✅ |
| Orphan rate (tutti i fact) | 0.0% | < 1% | ✅ |
| Test suite pytest (64 test) | 64 OK | ≥ 60 | ✅ |
| Pipeline run completo 22 siti | 36+45+26 OK | 100% | ✅ |
| Giorni uomo stimati totali | 216 | 216 | — |
| Giorni uomo completati | 158 | 216 | 73% |
| FASE 8 (Shadow Mode) | Non avviata | Q3 2026 | ⏳ |

---

## 3. Stato Sprint (dashboard)

> Il **dettaglio attività** di ogni sprint (con blocchi, decisioni, note SAL) è nel doc di sprint dedicato in [`sprint_agile/`](sprint_agile/). La **chiusura di fase** (deliverable cliente) è in [`milestones/`](milestones/). Questo file resta il quadro di portfolio.

| Sprint | Area | Gg (compl./stim.) | % | Stato | Doc |
|--------|------|-------------------|---|-------|-----|
| 0.1 | Unity Catalog & Storage | 0/7 | ~85%* | 🔵 IN CORSO | [0.1](sprint_agile/sprint_0.1.md) |
| 0.2 | CI/CD & DAB | 5/5 | 100% | ✅ | [0.2](sprint_agile/sprint_0.2.md) |
| 0.3 | Connettività & Template | 7/7 | 100% | ✅ | [0.3](sprint_agile/sprint_0.3.md) |
| 1.1 | DIM Calendario & Merceologie | 5/5 | 100% | ✅ | [1.1](sprint_agile/sprint_1.1.md) |
| 1.2 | DIM Articoli, Fornitori, PDV | 6/7 | 86% | 🔵 PARZ. | [1.2](sprint_agile/sprint_1.2.md) |
| 1.3 | DIM Logistiche (Siti, Operatori, Corrieri) | 6/7 | 86% | 🔵 PARZ. | [1.3](sprint_agile/sprint_1.3.md) |
| 2.1 | Bronze Carichi | 6/7 | 86% | 🔵 PARZ. | [2.1](sprint_agile/sprint_2.1.md) |
| 2.2 | Silver Carichi | 7/7 | 100% | ✅ | [2.2](sprint_agile/sprint_2.2.md) |
| 2.3 | Gold F_CARICO | 5/7 | 71% | 🔵 PARZ. | [2.3](sprint_agile/sprint_2.3.md) |
| 2.4 | KPI & Validazione Carichi | 3/5 | 60% | 🔵 PARZ. | [2.4](sprint_agile/sprint_2.4.md) |
| 3.1 | Bronze Giacenze | 6/7 | 86% | 🔵 PARZ. | [3.1](sprint_agile/sprint_3.1.md) |
| 3.2 | Silver Giacenze | 7/7 | 100% | ✅ | [3.2](sprint_agile/sprint_3.2.md) |
| 3.3 | Gold F_GIACENZE | 6/7 | 86% | 🔵 PARZ. | [3.3](sprint_agile/sprint_3.3.md) |
| 3.4 | Workflow & Validazione Giacenze | 3/5 | 60% | 🔵 PARZ. | [3.4](sprint_agile/sprint_3.4.md) |
| 4.1 | Bronze Prep Spedizioni | 6/7 | 86% | 🔵 PARZ. | [4.1](sprint_agile/sprint_4.1.md) |
| 4.2 | Silver Prep Spedizioni | 8/8 | 100% | ✅ | [4.2](sprint_agile/sprint_4.2.md) |
| 4.3 | Gold F_PREP_SPED | 7/8 | 88% | 🔵 PARZ. | [4.3](sprint_agile/sprint_4.3.md) |
| 4.4 | KPI Picking & Workflow | 4/5 | 80% | 🔵 PARZ. | [4.4](sprint_agile/sprint_4.4.md) |
| 4.5 | Edge Cases Prep Spedizioni | 3/5 | 60% | 🔵 PARZ. | [4.5](sprint_agile/sprint_4.5.md) |
| 5.1 | Bronze Trasporti | 6/7 | 86% | 🔵 PARZ. | [5.1](sprint_agile/sprint_5.1.md) |
| 5.2 | Silver Trasporti | 8/8 | 100% | ✅ | [5.2](sprint_agile/sprint_5.2.md) |
| 5.3 | Gold F_ORDINI & F_TRASPORTO | 6/8 | 75% | 🔵 PARZ. | [5.3](sprint_agile/sprint_5.3.md) |
| 5.4 | KPI Trasporti & Workflow | 3/5 | 60% | 🔵 PARZ. | [5.4](sprint_agile/sprint_5.4.md) |
| 6.1 | CE178 Silver & Gold | 7/7 | 100% | ✅ | [6.1](sprint_agile/sprint_6.1.md) |
| 6.2 | Carrellisti Bronze-Silver-Gold | 7/7 | 100% | ✅ | [6.2](sprint_agile/sprint_6.2.md) |
| 6.3 | Workflow Wave E & Validazione | 3/5 | 60% | 🔵 PARZ. | [6.3](sprint_agile/sprint_6.3.md) |
| 7.1 | Aggregati Mensili DataMart | 7/7 | 100% | ✅ | [7.1](sprint_agile/sprint_7.1.md) |
| 7.2 | MicroStrategy & Ottimizzazione Query | 3/7 | 43% | 🔵 PARZ. | [7.2](sprint_agile/sprint_7.2.md) |
| 7.3 | Validazione KPI End-to-End | 2/5 | 40% | 🔵 PARZ. | [7.3](sprint_agile/sprint_7.3.md) |
| 8.1 | Shadow Mode Setup | 1/5 | 20% | 🔵 PARZ. | [8.1](sprint_agile/sprint_8.1.md) |
| 8.2 | Shadow Mode Run (10+ gg) | 1/10 | 10% | 🔵 PARZ. | [8.2](sprint_agile/sprint_8.2.md) |
| 8.3 | Preparazione Cut-Over | 2/5 | 40% | 🔵 PARZ. | [8.3](sprint_agile/sprint_8.3.md) |
| 8.4 | Cut-Over & Stabilizzazione | 0/7 | 0% | ⏳ | [8.4](sprint_agile/sprint_8.4.md) |

\* 0.1: infra su GitLab, CI via **MSI**. **apply v0.1.5 parziale** (2026-09-01): 8 schemi + Volume di landing creati (OP-INF-1 chiuso); grants falliti per nome gruppo errato → fix `Group-Engineering-dev` (OP-INF-2 chiuso), applicati con **v0.1.6**. Trasporto landing = **AzCopy** ([[ADR-0023]], backend in main); resta il gate **accesso container** per l'ingestion.

---

## 4. Dettaglio attività per sprint

> **Spostato.** Il dettaglio delle attività di ogni sprint (stato, blocchi, decisioni, note SAL) vive ora nei doc di sprint in [`sprint_agile/`](sprint_agile/), master dei SAL settimanali. La chiusura tecnica/funzionale di ogni fase (deliverable cliente) è in [`milestones/`](milestones/).

| Fase | Milestone (chiusura) | Sprint |
|------|----------------------|--------|
| FASE 0 | [fase_0](milestones/fase_0.md) | 0.1–0.3 |
| FASE 1 | [fase_1](milestones/fase_1.md) | 1.1–1.3 |
| FASE 2 | [fase_2](milestones/fase_2.md) | 2.1–2.4 |
| FASE 3 | [fase_3](milestones/fase_3.md) | 3.1–3.4 |
| FASE 4 | [fase_4](milestones/fase_4.md) | 4.1–4.5 |
| FASE 5 | [fase_5](milestones/fase_5.md) | 5.1–5.4 |
| FASE 6 | [fase_6](milestones/fase_6.md) | 6.1–6.3 |
| FASE 7 | [fase_7](milestones/fase_7.md) | 7.1–7.3 |
| FASE 8 | [fase_8](milestones/fase_8.md) | 8.1–8.4 |

---

## 5. Riepilogo Risorse

| Sprint | Durata (gg) | Cloud Solution Architect | Cloud DevOps Engineer Sr | Cloud Solution Developer Sr | BI Developer Sr | BA / PM | Tot Sprint |
|--------|-------------|--------------------------|--------------------------|------------------------------|-----------------|---------|------------|
| **FASE 0** | | | | | | | |
| 0.1 Unity Catalog & Storage | 7 | 2 | 4 | 1 | — | — | 7 |
| 0.2 CI/CD & DAB | 5 | 1 | 3 | 1 | — | — | 5 |
| 0.3 Connettività & Template | 7 | 1 | — | 5 | — | 1 | 7 |
| **Subtotale FASE 0** | **19** | **4** | **7** | **7** | **—** | **1** | **19** |
| **FASE 1** | | | | | | | |
| 1.1 DIM Calendario & Merceologie | 5 | — | — | 4 | — | 1 | 5 |
| 1.2 DIM Articoli, Fornitori, PDV | 7 | — | — | 6 | — | 1 | 7 |
| 1.3 DIM Siti, Operatori, Corrieri | 7 | 1 | — | 5 | — | 1 | 7 |
| **Subtotale FASE 1** | **19** | **1** | **—** | **15** | **—** | **3** | **19** |
| **FASE 2** | | | | | | | |
| 2.1 Bronze Carichi | 7 | — | — | 7 | — | — | 7 |
| 2.2 Silver Carichi | 7 | — | — | 6 | — | 1 | 7 |
| 2.3 Gold F_CARICO | 7 | 1 | — | 5 | — | 1 | 7 |
| 2.4 KPI & Validazione Carichi | 5 | — | — | 3 | — | 2 | 5 |
| **Subtotale FASE 2** | **26** | **1** | **—** | **21** | **—** | **4** | **26** |
| **FASE 3** | | | | | | | |
| 3.1 Bronze Giacenze | 7 | — | — | 7 | — | — | 7 |
| 3.2 Silver Giacenze | 7 | — | — | 6 | — | 1 | 7 |
| 3.3 Gold F_GIACENZE | 7 | 1 | — | 5 | — | 1 | 7 |
| 3.4 Workflow & Validazione Giacenze | 5 | — | — | 3 | — | 2 | 5 |
| **Subtotale FASE 3** | **26** | **1** | **—** | **21** | **—** | **4** | **26** |
| **FASE 4** | | | | | | | |
| 4.1 Bronze Prep Spedizioni | 7 | — | — | 7 | — | — | 7 |
| 4.2 Silver Prep Spedizioni | 8 | 1 | — | 6 | — | 1 | 8 |
| 4.3 Gold F_PREP_SPED | 8 | 1 | — | 6 | — | 1 | 8 |
| 4.4 KPI Picking & Workflow | 5 | — | — | 3 | — | 2 | 5 |
| 4.5 Edge Cases Prep Spedizioni | 5 | — | — | 5 | — | — | 5 |
| **Subtotale FASE 4** | **33** | **2** | **—** | **27** | **—** | **4** | **33** |
| **FASE 5** | | | | | | | |
| 5.1 Bronze Trasporti | 7 | — | — | 7 | — | — | 7 |
| 5.2 Silver Trasporti | 8 | — | — | 7 | — | 1 | 8 |
| 5.3 Gold F_ORDINI & F_TRASPORTO | 8 | 1 | — | 6 | — | 1 | 8 |
| 5.4 KPI Trasporti & Workflow | 5 | — | — | 3 | — | 2 | 5 |
| **Subtotale FASE 5** | **28** | **1** | **—** | **23** | **—** | **4** | **28** |
| **FASE 6** | | | | | | | |
| 6.1 CE178 Silver & Gold | 7 | — | — | 6 | — | 1 | 7 |
| 6.2 Carrellisti Bronze-Silver-Gold | 7 | — | — | 6 | — | 1 | 7 |
| 6.3 Workflow Wave E & Validazione | 5 | — | — | 3 | — | 2 | 5 |
| **Subtotale FASE 6** | **19** | **—** | **—** | **15** | **—** | **4** | **19** |
| **FASE 7** | | | | | | | |
| 7.1 Aggregati Mensili | 7 | 1 | — | 5 | 1 | — | 7 |
| 7.2 MicroStrategy & Ottimizzazione | 7 | — | — | 3 | 3 | 1 | 7 |
| 7.3 Validazione KPI E2E | 5 | — | — | 2 | 1 | 2 | 5 |
| **Subtotale FASE 7** | **19** | **1** | **—** | **10** | **5** | **3** | **19** |
| **FASE 8** | | | | | | | |
| 8.1 Shadow Mode Setup | 5 | 1 | 1 | 2 | — | 1 | 5 |
| 8.2 Shadow Mode Run (10+ gg) | 10 | — | — | 8 | — | 2 | 10 |
| 8.3 Preparazione Cut-Over | 5 | 2 | — | 1 | — | 2 | 5 |
| 8.4 Cut-Over & Stabilizzazione | 7 | 1 | 1 | 2 | 1 | 2 | 7 |
| **Subtotale FASE 8** | **27** | **4** | **2** | **13** | **1** | **7** | **27** |
| | | | | | | | |
| **TOTALE STIMATO** | **216** | **15** | **9** | **152** | **6** | **30** | **216** |
| **GG COMPLETATI (✅ + 🔵 PARZ. 90%)** | **~158** | **~10** | **7** | **~119** | **~5** | **~17** | **~158** |
| **RESIDUO (parziali + pendenti + FASE 8)** | **~58** | **~5** | **2** | **~33** | **~1** | **~13** | **~58** |

---

## 6. Pendenze Tecniche (non bloccanti FASE 8, da pianificare)

| Item | Rif. OP | Priorità | Effort stim. | Stato | Note |
|------|---------|----------|-------------|-------|------|
| LAD ri-risoluzione orphan (job generico + nat_key in fact) | OP-32 | 🔴 Alta | 5 gg DE | Impl. base fatta | `gold_lad_resolver` + nat_key (L-01/L-02); dipende OP-02 per full |
| Watermark rollout (clean, carichi, spedizioni, ordini) | OP-35 | 🟡 Media | 3 gg DE | ✅ Completato | Rollout 2026-06-19 su tutti i _clean |
| Supporto Parquet in Bronze (widget file_format, auto-detect) | Gap #2 | 🔴 Alta | 3 gg DE | ✅ Fatto | G-01, 2026-06-20 |
| **Certifica F_CARICO — grain pesata INNER JOIN** | OP-CAR-5 | 🟠 Media | 2 gg DE | Design pendente | LEFT join pesata vs grain da catena WL; sessione dedicata |
| **Migrazione brownfield Databricks** (schemi, Volume, DAB, multi-repo GitLab) | D1-D5 | 🟡 Media | 4-6 gg DevOps | **CI in DEV via MSI (fatto); grant MI ottenuto → `apply` da eseguire** | 4 repo GitHub (SoT) / 3 GitLab cliente **tutti con CI in DEV via Managed Identity**: lib `v1.0.4`, workflows `deploy_dev` verde (7 job), infra `plan` verde. **OP-INF-1 chiuso (2026-09-01)** → ri-lanciare pipeline `infrastructure` + `apply`. Vedi `16_runbook_multirepo_github_gitlab.md` |
| Schema definitivo lookup Retail (OP-02) | OP-02 | 🟡 Media | — | In attesa Reply | Sblocca join master articolo/fornitore; lega D2 migrazione |
| Framework DQ condiviso (Great Expectations / Soda) | OP-21 | 🔴 Alta | — | Senza risposta Reply | Ri-sottoporre con priorità |

---

## Riferimenti

- `docs/main/05_open_points.md` — registro completo open points (aggiornato 2026-07-03)
- `docs/main/01_architettura.md` — architettura tecnica, pattern, decisioni chiave
- `docs/main/02_pipeline_mapping.md` — mapping sorgente→Bronze→Silver→Gold (validato 2026-06-17)
- `docs/main/10_piano_migrazione_databricks.md` — piano migrazione brownfield + decisioni D1-D5
- `docs/main/11_devops_handoff_databricks.md` — handoff DevOps (Terraform brownfield, multi-repo GitLab, DAB)
- `docs/main/12_checklist_infra_setup.md` — checklist infra + mail al cliente + stato punti aperti
- `docs/main/sprint_agile/` — master SAL settimanali per sprint (0.1 … 8.4)
- `docs/main/milestones/` — deliverable di chiusura per fase (fase_0 … fase_8); assorbono i vecchi `fasi/F*` (archiviati in `docs/Archive/fasi/`)
- `DOCS/piani/cutover_plan.md` — piano cut-over (T-7gg→T=08:00, 15 smoke test, go/no-go)
- `DOCS/piani/rollback_plan.md` — procedura rollback 6 step (~3h totali)
- `DOCS/runbook.md` — runbook operativo (scheduling, alert, anomalie, SLA)
- `DOCS/Piano di Sviluppo - Logistico 2.0.xlsx` — versione Excel per SAL cliente
- `docs/Archive/Piano di Sviluppo - Logistico 2.0.md` — versione originale v1.0 (2026-05-29)
