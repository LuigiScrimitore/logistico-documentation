# Backlog Master — Logistico 2.0

**Creato**: 2026-07-05 · **Owner**: Team Logistico 2.0
**Scopo**: **indice unico** (SSOT) di **tutte le attività (ACT)** e **tutte le decisioni (ADR)** del
progetto. Ogni riga punta al file di dettaglio in [`acts/`](acts/) o [`adr/`](adr/), che resta la SSOT
del singolo tema. Questo file è la **mappa**; i file ACT/ADR sono il **territorio**.

> **Sostituisce** il vecchio [`06_backlog.md`](06_backlog.md), ora **archiviato** (deprecato 2026-08-01).
> Gli **open points** restano nel registro vivo [`05_open_points.md`](05_open_points.md) (loro SSOT).
> Convenzioni ACT → [`acts/README.md`](acts/README.md); ADR → [`adr/README_adr.md`](adr/README_adr.md).

## Legenda stato
| Stato | Significato |
|-------|-------------|
| ✅ done | completata (record) |
| 🔵 in-progress / parziale | in corso |
| ⬜ proposed | da fare, non iniziata |
| ⏸️ on-hold | sospesa (dipendenza) |
| ❌ cancelled / superseded | chiusa senza consegna / sostituita |

**Blocco**: 🟢 nessuno · ☁️ cloud/PROD · 🏗️ infra (Azure/GitLab) · 🤝 Reply (anagrafiche/OP-02)

---

## 1. ACT da Sprint (per fase / wave)

> Una riga per ogni attività sprint; codice = `N.N.N`. Popolato in Fase 2 (2026-08-01).

### FASE 0 — Piattaforma & Setup
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 0.1.1 | Cataloghi Unity Catalog (solo DEV) | 0.1 | 🔵 in-progress | 🏗️ | [acts/ACT_0.1.1](acts/ACT_0.1.1_cataloghi-unity-catalog-dev.md) |
| 0.1.2 | Schemi per dominio | 0.1 | 🔵 in-progress | 🏗️ | [acts/ACT_0.1.2](acts/ACT_0.1.2_schemi-per-dominio.md) |
| 0.1.3 | Landing storage — UC Volume | 0.1 | 🔵 in-progress | 🏗️☁️ | [acts/ACT_0.1.3](acts/ACT_0.1.3_landing-uc-volume.md) |
| 0.1.4 | GitLab CI/CD (ex Key Vault) — no segreti Oracle | 0.1 | ✅ done | 🟢 | [acts/ACT_0.1.4](acts/ACT_0.1.4_gitlab-cicd-no-secret-oracle.md) |
| 0.1.5 | Compute serverless (policy rimossa, ACT_9007) | 0.1 | ✅ done | 🟢 | [acts/ACT_0.1.5](acts/ACT_0.1.5_cluster-policy-serverless.md) |
| 0.1.6 | Consegna `brownfield/` multi-repo | 0.1 | 🔵 in-progress | 🏗️ | [acts/ACT_0.1.6](acts/ACT_0.1.6_consegna-brownfield-multi-repo.md) |
| 0.1.7 | Grants least-privilege | 0.1 | 🔵 in-progress | 🏗️ | [acts/ACT_0.1.7](acts/ACT_0.1.7_grants-least-privilege.md) |
| 0.2.1 | Struttura repository GitLab | 0.2 | ✅ done | 🟢 | [acts/ACT_0.2.1](acts/ACT_0.2.1_struttura-repo-gitlab.md) |
| 0.2.2 | Databricks Asset Bundles (dev) | 0.2 | ✅ done | 🟢 | [acts/ACT_0.2.2](acts/ACT_0.2.2_databricks-asset-bundles.md) |
| 0.2.3 | Pipeline GitLab CI — stage DEV | 0.2 | ✅ done | 🟢 | [acts/ACT_0.2.3](acts/ACT_0.2.3_pipeline-gitlab-ci-dev.md) |
| 0.2.4 | Pipeline GitLab CI — gate PROD (manual) | 0.2 | ✅ done | 🟢 | [acts/ACT_0.2.4](acts/ACT_0.2.4_gate-prod-manual-approval.md) |
| 0.2.5 | Libreria `logistica_utils` | 0.2 | ✅ done | 🟢 | [acts/ACT_0.2.5](acts/ACT_0.2.5_libreria-logistica-utils.md) |
| 0.3.1 | Test connettività JDBC Oracle | 0.3 | ❌ cancelled | 🟢 | [acts/ACT_0.3.1](acts/ACT_0.3.1_test-jdbc-oracle.md) |
| 0.3.2 | Benchmark JDBC / sizing | 0.3 | ❌ cancelled | 🟢 | [acts/ACT_0.3.2](acts/ACT_0.3.2_benchmark-jdbc-sizing.md) |
| 0.3.3 | Decision matrix ingestion per tabella | 0.3 | ✅ done | 🟢 | [acts/ACT_0.3.3](acts/ACT_0.3.3_decision-matrix-ingestion.md) |
| 0.3.4 | Template Bronze (CSV→Delta MERGE) | 0.3 | ✅ done | 🟢 | [acts/ACT_0.3.4](acts/ACT_0.3.4_template-bronze.md) |
| 0.3.5 | Template Silver (cleansing 1:1) | 0.3 | ✅ done | 🟢 | [acts/ACT_0.3.5](acts/ACT_0.3.5_template-silver.md) |
| 0.3.6 | Template Gold Fact | 0.3 | ✅ done | 🟢 | [acts/ACT_0.3.6](acts/ACT_0.3.6_template-gold-fact.md) |
| 0.3.7 | Logging & alerting standard | 0.3 | ✅ done | 🟢 | [acts/ACT_0.3.7](acts/ACT_0.3.7_logging-alerting-standard.md) |

### FASE 1 — Dimensioni
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 1.1.1 | DIM_CALENDARIO (2018–2030, festività IT) | 1.1 | ✅ done | 🟢 | [acts/ACT_1.1.1](acts/ACT_1.1.1_dim-calendario.md) |
| 1.1.2 | DIM_MESE/TRIMESTRE/ANNO | 1.1 | ✅ done | 🟢 | [acts/ACT_1.1.2](acts/ACT_1.1.2_dim-mese-trimestre-anno.md) |
| 1.1.3 | DIM_STRUTTURA_MERCEOLOGICA (5 livelli) | 1.1 | 🔵 in-progress | ☁️ | [acts/ACT_1.1.3](acts/ACT_1.1.3_dim-struttura-merceologica.md) |
| 1.1.4 | Test DQ Calendario | 1.1 | ✅ done | 🟢 | [acts/ACT_1.1.4](acts/ACT_1.1.4_test-dq-calendario.md) |
| 1.2.1 | Bronze anagrafiche (ART/FORN/PDV) | 1.2 | 🔵 in-progress | 🏗️ | [acts/ACT_1.2.1](acts/ACT_1.2.1_bronze-anagrafiche.md) |
| 1.2.2 | Silver DIM_ARTICOLO (dedup, SCD1) | 1.2 | ✅ done | 🟢 | [acts/ACT_1.2.2](acts/ACT_1.2.2_silver-dim-articolo.md) |
| 1.2.3 | Silver DIM_FORNITORE | 1.2 | ✅ done | 🟢 | [acts/ACT_1.2.3](acts/ACT_1.2.3_silver-dim-fornitore.md) |
| 1.2.4 | Silver DIM_PDV | 1.2 | ✅ done | 🟢 | [acts/ACT_1.2.4](acts/ACT_1.2.4_silver-dim-pdv.md) |
| 1.2.5 | Gold DIM_ARTICOLO (JOIN merceologica) | 1.2 | ✅ done | 🤝 OP-02 | [acts/ACT_1.2.5](acts/ACT_1.2.5_gold-dim-articolo.md) |
| 1.2.6 | Gold DIM_FORNITORE, DIM_PDV | 1.2 | ✅ done | 🤝 OP-02 | [acts/ACT_1.2.6](acts/ACT_1.2.6_gold-dim-fornitore-pdv.md) |
| 1.2.7 | Test DQ anagrafiche | 1.2 | ✅ done | 🟢 | [acts/ACT_1.2.7](acts/ACT_1.2.7_test-dq-anagrafiche.md) |
| 1.3.1 | Bronze siti/operatori/corrieri (TABGEN) | 1.3 | 🔵 in-progress | 🏗️ | [acts/ACT_1.3.1](acts/ACT_1.3.1_bronze-siti-operatori-corrieri.md) |
| 1.3.2 | Silver DIM_SITO_LOGISTICO (normalize_sito) | 1.3 | ✅ done | 🟢 | [acts/ACT_1.3.2](acts/ACT_1.3.2_silver-dim-sito-logistico.md) |
| 1.3.3 | Silver DIM_OPERATORE (recovery 3A/4A) | 1.3 | ✅ done | 🟢 | [acts/ACT_1.3.3](acts/ACT_1.3.3_silver-dim-operatore.md) |
| 1.3.4 | Silver DIM_CORRIERE | 1.3 | ✅ done | 🟢 | [acts/ACT_1.3.4](acts/ACT_1.3.4_silver-dim-corriere.md) |
| 1.3.5 | Silver DIM_TOPOGRAFIA_MAGAZZINO | 1.3 | ✅ done | 🟢 | [acts/ACT_1.3.5](acts/ACT_1.3.5_silver-dim-topografia.md) |
| 1.3.6 | Gold DIM logistiche | 1.3 | ✅ done | 🟢 | [acts/ACT_1.3.6](acts/ACT_1.3.6_gold-dim-logistiche.md) |
| 1.3.7 | Workflow `logistica_dim_refresh` | 1.3 | 🔵 in-progress | ☁️ | [acts/ACT_1.3.7](acts/ACT_1.3.7_workflow-dim-refresh.md) |

### FASE 2 — Wave A Carichi
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 2.1.1 | Analisi sorgenti carichi | 2.1 | ✅ done | 🟢 | [acts/ACT_2.1.1](acts/ACT_2.1.1_analisi-sorgenti-carichi.md) |
| 2.1.2 | bronze_sto_tes_carichi | 2.1 | ✅ done | 🟢 | [acts/ACT_2.1.2](acts/ACT_2.1.2_bronze-sto-tes-carichi.md) |
| 2.1.3 | bronze_sto_righe_carico | 2.1 | ✅ done | 🟢 | [acts/ACT_2.1.3](acts/ACT_2.1.3_bronze-sto-righe-carico.md) |
| 2.1.4 | bronze_pesate | 2.1 | ✅ done | 🟢 | [acts/ACT_2.1.4](acts/ACT_2.1.4_bronze-pesate.md) |
| 2.1.5 | bronze_traccia_ce178 | 2.1 | ✅ done | 🟢 | [acts/ACT_2.1.5](acts/ACT_2.1.5_bronze-traccia-ce178.md) |
| 2.1.6 | Backfill storico Carichi (22 db-link) | 2.1 | 🔵 in-progress | ☁️ | [acts/ACT_2.1.6](acts/ACT_2.1.6_backfill-storico-carichi.md) |
| 2.1.7 | Workflow `logistica_carichi` | 2.1 | 🔵 in-progress | ☁️ | [acts/ACT_2.1.7](acts/ACT_2.1.7_workflow-logistica-carichi.md) |
| 2.2.1 | Analisi trasformazioni CDT_SA → Spark | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.1](acts/ACT_2.2.1_analisi-trasformazioni-cdt-sa.md) |
| 2.2.2 | silver_carichi_testate | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.2](acts/ACT_2.2.2_silver-carichi-testate.md) |
| 2.2.3 | silver_carichi_dettagli | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.3](acts/ACT_2.2.3_silver-carichi-dettagli.md) |
| 2.2.4 | silver_pesate (DQ peso negativo) | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.4](acts/ACT_2.2.4_silver-pesate.md) |
| 2.2.5 | silver_traccia_ce178 | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.5](acts/ACT_2.2.5_silver-traccia-ce178.md) |
| 2.2.6 | Suite test DQ Silver Carichi | 2.2 | ✅ done | 🟢 | [acts/ACT_2.2.6](acts/ACT_2.2.6_suite-test-dq-silver-carichi.md) |
| 2.2.7 | Workflow — task Silver | 2.2 | 🔵 in-progress | ☁️ | [acts/ACT_2.2.7](acts/ACT_2.2.7_workflow-task-silver.md) |
| 2.3.1 | Analisi SP_LOAD_F_CARICO | 2.3 | ✅ done | 🟢 | [acts/ACT_2.3.1](acts/ACT_2.3.1_analisi-sp-load-f-carico.md) |
| 2.3.2 | gold_f_carico | 2.3 | ✅ done | 🟢 | [acts/ACT_2.3.2](acts/ACT_2.3.2_gold-f-carico.md) |
| 2.3.3 | Late-Arriving Dimensions handler | 2.3 | ✅ done | 🟢 | [acts/ACT_2.3.3](acts/ACT_2.3.3_late-arriving-dimensions-handler.md) |
| 2.3.4 | Quadratura Gold vs Oracle | 2.3 | 🔵 in-progress | ☁️ | [acts/ACT_2.3.4](acts/ACT_2.3.4_quadratura-gold-vs-oracle.md) |
| 2.3.5 | Workflow Bronze→Silver→Gold→DQ | 2.3 | 🔵 in-progress | ☁️ | [acts/ACT_2.3.5](acts/ACT_2.3.5_workflow-bronze-silver-gold-dq.md) |
| 2.4.1 | Vista kpi_lead_time_fornitore | 2.4 | ✅ done | 🟢 | [acts/ACT_2.4.1](acts/ACT_2.4.1_kpi-lead-time-fornitore.md) |
| 2.4.2 | Vista kpi_qualita_ricevimento | 2.4 | ✅ done | 🟢 | [acts/ACT_2.4.2](acts/ACT_2.4.2_kpi-qualita-ricevimento.md) |
| 2.4.3 | Validazione funzionale con BA | 2.4 | ⏸️ on-hold | ☁️🤝 | [acts/ACT_2.4.3](acts/ACT_2.4.3_validazione-funzionale-ba.md) |
| 2.4.4 | Documentazione area Carichi | 2.4 | ✅ done | 🟢 | [acts/ACT_2.4.4](acts/ACT_2.4.4_documentazione-area-carichi.md) |

### FASE 3 — Wave B Giacenze
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 3.1.1 | Analisi snapshot giacenze | 3.1 | ✅ done | 🟢 | [acts/ACT_3.1.1](acts/ACT_3.1.1_analisi-snapshot-giacenze.md) |
| 3.1.2 | bronze_catena (+ esterni) | 3.1 | ✅ done | 🟢 | [acts/ACT_3.1.2](acts/ACT_3.1.2_bronze-catena.md) |
| 3.1.3 | bronze_t_stock | 3.1 | ✅ done | 🟢 | [acts/ACT_3.1.3](acts/ACT_3.1.3_bronze-t-stock.md) |
| 3.1.4 | bronze_struttura_mag | 3.1 | ✅ done | 🟢 | [acts/ACT_3.1.4](acts/ACT_3.1.4_bronze-struttura-mag.md) |
| 3.1.5 | Backfill storico giacenze | 3.1 | 🔵 in-progress | ☁️🏗️ | [acts/ACT_3.1.5](acts/ACT_3.1.5_backfill-storico-giacenze.md) |
| 3.1.6 | Workflow Bronze Giacenze | 3.1 | 🔵 in-progress | ☁️ | [acts/ACT_3.1.6](acts/ACT_3.1.6_workflow-bronze-giacenze.md) |
| 3.2.1 | Analisi SP_STOCK_* | 3.2 | ✅ done | 🟢 | [acts/ACT_3.2.1](acts/ACT_3.2.1_analisi-sp-stock.md) |
| 3.2.2 | silver_catena_unificata | 3.2 | ✅ done | 🟢 | [acts/ACT_3.2.2](acts/ACT_3.2.2_silver-catena-unificata.md) |
| 3.2.3 | silver_struttura_mag_clean | 3.2 | ✅ done | 🟢 | [acts/ACT_3.2.3](acts/ACT_3.2.3_silver-struttura-mag-clean.md) |
| 3.2.4 | silver_t_stock | 3.2 | ✅ done | 🟢 | [acts/ACT_3.2.4](acts/ACT_3.2.4_silver-t-stock.md) |
| 3.2.5 | DQ Silver Giacenze | 3.2 | ✅ done | 🟢 | [acts/ACT_3.2.5](acts/ACT_3.2.5_dq-silver-giacenze.md) |
| 3.3.1 | Analisi SP_LOAD_F_GIACENZE | 3.3 | ✅ done | 🟢 | [acts/ACT_3.3.1](acts/ACT_3.3.1_analisi-sp-load-f-giacenze.md) |
| 3.3.2 | gold_f_giacenze_daily | 3.3 | ✅ done | 🟢 | [acts/ACT_3.3.2](acts/ACT_3.3.2_gold-f-giacenze-daily.md) |
| 3.3.3 | gold_dm_giacenze_monthly | 3.3 | ✅ done | 🟢 | [acts/ACT_3.3.3](acts/ACT_3.3.3_gold-dm-giacenze-monthly.md) |
| 3.3.4 | Vista kpi_saturazione_magazzino | 3.3 | ✅ done | 🟢 | [acts/ACT_3.3.4](acts/ACT_3.3.4_kpi-saturazione-magazzino.md) |
| 3.3.5 | Vista kpi_aging_articoli | 3.3 | ✅ done | 🟢 | [acts/ACT_3.3.5](acts/ACT_3.3.5_kpi-aging-articoli.md) |
| 3.3.6 | Quadratura vs Oracle | 3.3 | 🔵 in-progress | ☁️ | [acts/ACT_3.3.6](acts/ACT_3.3.6_quadratura-giacenze-oracle.md) |
| 3.4.1 | Workflow `logistica_giacenze` | 3.4 | 🔵 in-progress | ☁️ | [acts/ACT_3.4.1](acts/ACT_3.4.1_workflow-giacenze.md) |
| 3.4.2 | Validazione funzionale giacenze BA | 3.4 | ⬜ proposed | ☁️🤝 | [acts/ACT_3.4.2](acts/ACT_3.4.2_validazione-ba-giacenze.md) |
| 3.4.3 | Documentazione area Giacenze | 3.4 | ✅ done | 🟢 | [acts/ACT_3.4.3](acts/ACT_3.4.3_doc-giacenze.md) |

### FASE 4 — Wave C Prep Spedizioni
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 4.1.1 | Analisi sorgenti Prep Spedizioni | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.1](acts/ACT_4.1.1_analisi-sorgenti-prep-sped.md) |
| 4.1.2 | bronze_storico_liste | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.2](acts/ACT_4.1.2_bronze-storico-liste.md) |
| 4.1.3 | bronze_storico_bolle_testate | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.3](acts/ACT_4.1.3_bronze-storico-bolle-testate.md) |
| 4.1.4 | bronze_storico_bolle_righe | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.4](acts/ACT_4.1.4_bronze-storico-bolle-righe.md) |
| 4.1.5 | bronze_storico_riepiloghi | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.5](acts/ACT_4.1.5_bronze-storico-riepiloghi.md) |
| 4.1.6 | bronze_cartellino + backfill | 4.1 | 🔵 in-progress | 🏗️ | [acts/ACT_4.1.6](acts/ACT_4.1.6_bronze-cartellino-backfill.md) |
| 4.1.7 | Workflow Bronze Prep Spedizioni | 4.1 | ✅ done | 🟢 | [acts/ACT_4.1.7](acts/ACT_4.1.7_workflow-bronze-prep-sped.md) |
| 4.2.1 | Analisi SP_AGG_ANAG_PREP_SPED 3A/4A | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.1](acts/ACT_4.2.1_analisi-sp-agg-anag-prep-sped.md) |
| 4.2.2 | silver_storico_liste_clean | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.2](acts/ACT_4.2.2_silver-storico-liste-clean.md) |
| 4.2.3 | silver_storico_bolle_clean | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.3](acts/ACT_4.2.3_silver-storico-bolle-clean.md) |
| 4.2.4 | silver_storico_liste_uniche | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.4](acts/ACT_4.2.4_silver-storico-liste-uniche.md) |
| 4.2.5 | silver_storico_bolle_uniche | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.5](acts/ACT_4.2.5_silver-storico-bolle-uniche.md) |
| 4.2.6 | silver_catena_unificata | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.6](acts/ACT_4.2.6_silver-catena-unificata.md) |
| 4.2.7 | DQ Silver Prep Spedizioni | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.7](acts/ACT_4.2.7_dq-silver-prep-sped.md) |
| 4.2.8 | Watermark OP-35 pilota | 4.2 | ✅ done | 🟢 | [acts/ACT_4.2.8](acts/ACT_4.2.8_watermark-op35-pilota.md) |
| 4.3.1 | Analisi SP_LOAD_F_PREP_PROD_OPER | 4.3 | ✅ done | 🟢 | [acts/ACT_4.3.1](acts/ACT_4.3.1_analisi-sp-load-f-prep-prod-oper.md) |
| 4.3.2 | Regola 30 min attrezzaggio | 4.3 | ✅ done | 🟢 | [acts/ACT_4.3.2](acts/ACT_4.3.2_regola-30min-attrezzaggio.md) |
| 4.3.3 | silver_prep_prep_sped | 4.3 | ✅ done | 🟢 | [acts/ACT_4.3.3](acts/ACT_4.3.3_silver-prep-prep-sped.md) |
| 4.3.4 | gold_f_prep_sped (0.0% orphan) | 4.3 | ✅ done | 🟢 | [acts/ACT_4.3.4](acts/ACT_4.3.4_gold-f-prep-sped.md) |
| 4.3.5 | gold_dm_turno_prep_sito | 4.3 | ✅ done | 🟢 | [acts/ACT_4.3.5](acts/ACT_4.3.5_gold-dm-turno-prep-sito.md) |
| 4.3.6 | Quadratura vs Oracle | 4.3 | 🔵 in-progress | ☁️ | [acts/ACT_4.3.6](acts/ACT_4.3.6_quadratura-vs-oracle.md) |
| 4.4.1 | Vista kpi_produttivita_operatore | 4.4 | ✅ done | 🟢 | [acts/ACT_4.4.1](acts/ACT_4.4.1_kpi-produttivita-operatore.md) |
| 4.4.2 | Vista kpi_efficienza_sito_prep | 4.4 | ✅ done | 🟢 | [acts/ACT_4.4.2](acts/ACT_4.4.2_kpi-efficienza-sito-prep.md) |
| 4.4.3 | Workflow `logistica_prep_sped` | 4.4 | 🔵 in-progress | ☁️ | [acts/ACT_4.4.3](acts/ACT_4.4.3_workflow-logistica-prep-sped.md) |
| 4.4.4 | Validazione funzionale con BA | 4.4 | ⬜ proposed | ☁️🤝 | [acts/ACT_4.4.4](acts/ACT_4.4.4_validazione-funzionale-ba.md) |
| 4.5.1 | Operatori non in DIM_OPERATORE (sentinel) | 4.5 | ✅ done | 🟢 | [acts/ACT_4.5.1](acts/ACT_4.5.1_operatori-non-in-dim-operatore.md) |
| 4.5.2 | Bolle annullate | 4.5 | ✅ done | 🟢 | [acts/ACT_4.5.2](acts/ACT_4.5.2_bolle-annullate.md) |
| 4.5.3 | Turni a cavallo di mezzanotte | 4.5 | ✅ done | 🟢 | [acts/ACT_4.5.3](acts/ACT_4.5.3_turni-cavallo-mezzanotte.md) |
| 4.5.4 | Stress test idempotenza | 4.5 | ⬜ proposed | ☁️🏗️ | [acts/ACT_4.5.4](acts/ACT_4.5.4_stress-test-idempotenza.md) |

### FASE 5 — Wave D Trasporti
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 5.1.1 | Analisi sorgenti trasporti | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.1](acts/ACT_5.1.1_analisi-sorgenti-trasporti.md) |
| 5.1.2 | bronze_spedizioni | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.2](acts/ACT_5.1.2_bronze-spedizioni.md) |
| 5.1.3 | bronze_t_trasp_mtv | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.3](acts/ACT_5.1.3_bronze-t-trasp-mtv.md) |
| 5.1.4 | bronze_t_pdv | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.4](acts/ACT_5.1.4_bronze-t-pdv.md) |
| 5.1.5 | bronze_t_vettori | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.5](acts/ACT_5.1.5_bronze-t-vettori.md) |
| 5.1.6 | bronze_automezzi | 5.1 | ✅ done | 🟢 | [acts/ACT_5.1.6](acts/ACT_5.1.6_bronze-automezzi.md) |
| 5.1.7 | Backfill + Workflow Bronze Trasporti | 5.1 | 🔵 in-progress | ☁️ | [acts/ACT_5.1.7](acts/ACT_5.1.7_backfill-workflow-bronze-trasporti.md) |
| 5.2.1 | Analisi T_ORDINI, T_TRASP_* | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.1](acts/ACT_5.2.1_analisi-t-ordini-t-trasp.md) |
| 5.2.2 | silver_prep_trasporto | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.2](acts/ACT_5.2.2_silver-prep-trasporto.md) |
| 5.2.3 | silver_prep_ordini | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.3](acts/ACT_5.2.3_silver-prep-ordini.md) |
| 5.2.4 | silver_spedizioni_clean | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.4](acts/ACT_5.2.4_silver-spedizioni-clean.md) |
| 5.2.5 | Costo trasporto a fasce peso | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.5](acts/ACT_5.2.5_costo-trasporto-fasce-peso.md) |
| 5.2.6 | DQ Silver Trasporti | 5.2 | ✅ done | 🟢 | [acts/ACT_5.2.6](acts/ACT_5.2.6_dq-silver-trasporti.md) |
| 5.3.1 | gold_f_ordini | 5.3 | ✅ done | 🟢 | [acts/ACT_5.3.1](acts/ACT_5.3.1_gold-f-ordini.md) |
| 5.3.2 | gold_f_trasporto | 5.3 | ✅ done | 🟢 | [acts/ACT_5.3.2](acts/ACT_5.3.2_gold-f-trasporto.md) |
| 5.3.3 | Gestione Swap | 5.3 | ✅ done | 🟢 | [acts/ACT_5.3.3](acts/ACT_5.3.3_gestione-swap.md) |
| 5.3.4 | Quadratura vs Oracle | 5.3 | 🔵 in-progress | ☁️ | [acts/ACT_5.3.4](acts/ACT_5.3.4_quadratura-vs-oracle.md) |
| 5.4.1 | Vista kpi_fill_rate | 5.4 | ✅ done | 🟢 | [acts/ACT_5.4.1](acts/ACT_5.4.1_vista-kpi-fill-rate.md) |
| 5.4.2 | Vista kpi_costo_trasporto | 5.4 | ✅ done | 🟢 | [acts/ACT_5.4.2](acts/ACT_5.4.2_vista-kpi-costo-trasporto.md) |
| 5.4.3 | Vista kpi_resa_corrieri | 5.4 | ✅ done | 🟢 | [acts/ACT_5.4.3](acts/ACT_5.4.3_vista-kpi-resa-corrieri.md) |
| 5.4.4 | Workflow `logistica_trasporti` | 5.4 | 🔵 in-progress | ☁️ | [acts/ACT_5.4.4](acts/ACT_5.4.4_workflow-logistica-trasporti.md) |
| 5.4.5 | Validazione funzionale trasporti BA | 5.4 | ⬜ proposed | ☁️🤝 | [acts/ACT_5.4.5](acts/ACT_5.4.5_validazione-funzionale-trasporti-ba.md) |

### FASE 6 — Wave E CE178 & Carrellisti
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 6.1.1 | Analisi flusso CE178 (ciclo vita lotto) | 6.1 | ✅ done | 🟢 | [acts/ACT_6.1.1](acts/ACT_6.1.1_analisi-flusso-ce178.md) |
| 6.1.2 | Bronze `bronze_traccia_ce178` | 6.1 | ✅ done | 🟢 | [acts/ACT_6.1.2](acts/ACT_6.1.2_bronze-traccia-ce178.md) |
| 6.1.3 | Silver `silver_tracciabilita_lotto` | 6.1 | ✅ done | 🟢 | [acts/ACT_6.1.3](acts/ACT_6.1.3_silver-tracciabilita-lotto.md) |
| 6.1.4 | Gold `gold_f_tracciabilita_lotti` | 6.1 | ✅ done | 🟢 | [acts/ACT_6.1.4](acts/ACT_6.1.4_gold-f-tracciabilita-lotti.md) |
| 6.1.5 | Vista conformità CE178 | 6.1 | ✅ done | 🟢 | [acts/ACT_6.1.5](acts/ACT_6.1.5_vista-conformita-ce178.md) |
| 6.2.1 | Analisi sorgenti carrellisti | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.1](acts/ACT_6.2.1_analisi-sorgenti-carrellisti.md) |
| 6.2.2 | Bronze `bronze_dettaglio_carr` + `imbfmovim` | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.2](acts/ACT_6.2.2_bronze-dettaglio-carr-imbfmovim.md) |
| 6.2.3 | Silver `silver_missione_carrellista` | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.3](acts/ACT_6.2.3_silver-missione-carrellista.md) |
| 6.2.4 | Silver `silver_sessione_carrellista` | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.4](acts/ACT_6.2.4_silver-sessione-carrellista.md) |
| 6.2.5 | Gold `gold_f_movimentazione_carrellisti` | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.5](acts/ACT_6.2.5_gold-f-movimentazione-carrellisti.md) |
| 6.2.6 | Vista KPI carrellisti | 6.2 | ✅ done | 🟢 | [acts/ACT_6.2.6](acts/ACT_6.2.6_vista-kpi-carrellisti.md) |
| 6.3.1 | Orchestrazione Wave E (in carichi/prep_sped) | 6.3 | 🔵 in-progress | ☁️ | [acts/ACT_6.3.1](acts/ACT_6.3.1_workflow-logistica-wave-e.md) |
| 6.3.2 | Validazione funzionale CE178 e carrellisti | 6.3 | ⬜ proposed | ☁️ | [acts/ACT_6.3.2](acts/ACT_6.3.2_validazione-ce178-carrellisti.md) |
| 6.3.3 | Documentazione Wave E | 6.3 | ✅ done | 🟢 | [acts/ACT_6.3.3](acts/ACT_6.3.3_documentazione-wave-e.md) |

### FASE 7 — Aggregati & MSTR
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 7.1.1 | Analisi aggregati Oracle CDT_DW (A_*) | 7.1 | ✅ done | 🟢 | [acts/ACT_7.1.1](acts/ACT_7.1.1_analisi-aggregati-oracle-cdt-dw.md) |
| 7.1.2 | DataMart `gold_dm_inbound_mensile` | 7.1 | ✅ done | 🟢 | [acts/ACT_7.1.2](acts/ACT_7.1.2_gold-dm-inbound-mensile.md) |
| 7.1.3 | DataMart `gold_dm_stock_mensile` | 7.1 | ✅ done | 🟢 | [acts/ACT_7.1.3](acts/ACT_7.1.3_gold-dm-stock-mensile.md) |
| 7.1.4 | DataMart `gold_dm_outbound_mensile` | 7.1 | ✅ done | 🟢 | [acts/ACT_7.1.4](acts/ACT_7.1.4_gold-dm-outbound-mensile.md) |
| 7.1.5 | DataMart `gold_dm_produttivita_mensile` | 7.1 | ✅ done | 🟢 | [acts/ACT_7.1.5](acts/ACT_7.1.5_gold-dm-produttivita-mensile.md) |
| 7.1.6 | Workflow `logistica_datamart` | 7.1 | 🔵 in-progress | ☁️ | [acts/ACT_7.1.6](acts/ACT_7.1.6_workflow-logistica-datamart.md) |
| 7.2.1 | Connettore MicroStrategy → SQL Warehouse | 7.2 | 🔵 in-progress | ☁️ | [acts/ACT_7.2.1](acts/ACT_7.2.1_connettore-microstrategy-sql-warehouse.md) |
| 7.2.2 | Ottimizzazione Gold (OPTIMIZE+ZORDER) | 7.2 | ✅ done | 🟢 | [acts/ACT_7.2.2](acts/ACT_7.2.2_ottimizzazione-gold-optimize-zorder.md) |
| 7.2.3 | 10 SQL KPI views (chiavi naturali v2.0) | 7.2 | ✅ done | 🟢 | [acts/ACT_7.2.3](acts/ACT_7.2.3_kpi-views-chiavi-naturali.md) |
| 7.2.4 | Tuning SQL Warehouse | 7.2 | 🔵 in-progress | ☁️ | [acts/ACT_7.2.4](acts/ACT_7.2.4_tuning-sql-warehouse.md) |
| 7.2.5 | Prototipo dashboard Logistica | 7.2 | 🔵 in-progress | ☁️ | [acts/ACT_7.2.5](acts/ACT_7.2.5_prototipo-dashboard-logistica.md) |
| 7.3.1 | Validazione KPI con BA/Key User | 7.3 | ⬜ proposed | ☁️🤝 | [acts/ACT_7.3.1](acts/ACT_7.3.1_validazione-kpi-con-ba.md) |
| 7.3.2 | Sign-off KPI business | 7.3 | ⬜ proposed | ☁️🤝 | [acts/ACT_7.3.2](acts/ACT_7.3.2_sign-off-kpi-business.md) |
| 7.3.3 | Performance baseline E2E | 7.3 | 🔵 in-progress | ☁️ | [acts/ACT_7.3.3](acts/ACT_7.3.3_performance-baseline-e2e.md) |
| 7.3.4 | Pipeline Mapping SSOT | 7.3 | ✅ done | 🟢 | [acts/ACT_7.3.4](acts/ACT_7.3.4_pipeline-mapping-ssot.md) |

### FASE 8 — Shadow mode & Cut-over
| ACT | Titolo | Sprint | Stato | Blocco | File |
|-----|--------|--------|-------|--------|------|
| 8.1.1 | Provisioning Workspace PROD + ADLS | 8.1 | ⬜ proposed | 🏗️ | [acts/ACT_8.1.1](acts/ACT_8.1.1_provisioning-prod-workspace-adls.md) |
| 8.1.2 | Deploy PROD (terraform + DAB) | 8.1 | ⬜ proposed | 🏗️ | [acts/ACT_8.1.2](acts/ACT_8.1.2_deploy-prod-terraform-dab.md) |
| 8.1.3 | Attivazione workflow PROD + backfill | 8.1 | ⬜ proposed | 🏗️ | [acts/ACT_8.1.3](acts/ACT_8.1.3_attivazione-workflow-prod-backfill.md) |
| 8.1.4 | Quadratura automatica giornaliera | 8.1 | 🔵 in-progress | ☁️ | [acts/ACT_8.1.4](acts/ACT_8.1.4_quadratura-automatica-oracle-databricks.md) |
| 8.1.5 | Runbook operativo PROD | 8.1 | 🔵 in-progress | 🟢 | [acts/ACT_8.1.5](acts/ACT_8.1.5_runbook-operativo-prod.md) |
| 8.2.1 | Monitoraggio quadrature giornaliero | 8.2 | ⬜ proposed | ☁️ | [acts/ACT_8.2.1](acts/ACT_8.2.1_monitoraggio-quadrature-giornaliero.md) |
| 8.2.2 | Risoluzione anomalie (fix+redeploy) | 8.2 | ⬜ proposed | ☁️ | [acts/ACT_8.2.2](acts/ACT_8.2.2_risoluzione-anomalie-fix-redeploy.md) |
| 8.2.3 | Stress test finestra batch | 8.2 | ⬜ proposed | ☁️ | [acts/ACT_8.2.3](acts/ACT_8.2.3_stress-test-finestra-batch.md) |
| 8.2.4 | Report finale Shadow Mode (sign-off) | 8.2 | 🔵 in-progress | ☁️ | [acts/ACT_8.2.4](acts/ACT_8.2.4_report-finale-shadow-mode.md) |
| 8.3.1 | Rollback Plan approvato | 8.3 | 🔵 in-progress | ☁️ | [acts/ACT_8.3.1](acts/ACT_8.3.1_rollback-plan.md) |
| 8.3.2 | Cut-Over Plan dettagliato | 8.3 | 🔵 in-progress | ☁️ | [acts/ACT_8.3.2](acts/ACT_8.3.2_cutover-plan.md) |
| 8.3.3 | Comunicazione utenti finali | 8.3 | 🔵 in-progress | ☁️ | [acts/ACT_8.3.3](acts/ACT_8.3.3_comunicazione-utenti-finali.md) |
| 8.3.4 | Verifica permessi PROD (MicroStrategy) | 8.3 | ⬜ proposed | 🏗️ | [acts/ACT_8.3.4](acts/ACT_8.3.4_verifica-permessi-prod-microstrategy.md) |
| 8.4.1 | Esecuzione Cut-Over | 8.4 | ⬜ proposed | ☁️ | [acts/ACT_8.4.1](acts/ACT_8.4.1_esecuzione-cutover.md) |
| 8.4.2 | Verifica post-cut-over D+0/D+1 | 8.4 | ⬜ proposed | ☁️ | [acts/ACT_8.4.2](acts/ACT_8.4.2_verifica-post-cutover.md) |
| 8.4.3 | Supporto utenti D+1→D+5 | 8.4 | ⬜ proposed | ☁️ | [acts/ACT_8.4.3](acts/ACT_8.4.3_supporto-utenti-post-live.md) |
| 8.4.4 | Spegnimento flusso Oracle ODI | 8.4 | ⬜ proposed | ☁️ | [acts/ACT_8.4.4](acts/ACT_8.4.4_spegnimento-odi-oracle.md) |
| 8.4.5 | Retrospettiva + documentazione finale | 8.4 | 🔵 in-progress | 🟢 | [acts/ACT_8.4.5](acts/ACT_8.4.5_retrospettiva-doc-finale.md) |

_(Sezioni FASE 0–8 popolate — Fase 2 completata.)_
_(sezioni da popolare in Fase 2)_

---

## 1-bis. Gate di chiusura fase (cloud) — Definition of Done

> Le attività sono in gran parte **done offline**. Una fase è **chiusa davvero** solo quando il suo pacchetto
> è (1) deployato in Azure Databricks **TEST**, (2) **schedulato e stabile** (≥ N run senza errori/rilanci
> manuali), (3) **DQ verdi**, (4) **dati certificati** vs CDT_DW. Criterio completo in
> [`acts/README.md`](acts/README.md). Ogni `GATE-N` è l'**ultima attività** della sua fase; `GATE-PROD` è il
> go-live in produzione (capstone). **Una fase resta "done offline" finché la sua GATE non è done.**

| ACT | Gate | Fase | Stato | Blocco | File |
|-----|------|------|-------|--------|------|
| GATE-1 | Deploy+run+cert cloud | FASE 1 Dimensioni | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-1](acts/ACT_GATE-1_deploy-run-cert-cloud-fase-1.md) |
| GATE-2 | Deploy+run+cert cloud | FASE 2 Carichi | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-2](acts/ACT_GATE-2_deploy-run-cert-cloud-fase-2.md) |
| GATE-3 | Deploy+run+cert cloud | FASE 3 Giacenze | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-3](acts/ACT_GATE-3_deploy-run-cert-cloud-fase-3.md) |
| GATE-4 | Deploy+run+cert cloud | FASE 4 Prep Sped | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-4](acts/ACT_GATE-4_deploy-run-cert-cloud-fase-4.md) |
| GATE-5 | Deploy+run+cert cloud | FASE 5 Trasporti | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-5](acts/ACT_GATE-5_deploy-run-cert-cloud-fase-5.md) |
| GATE-6 | Deploy+run+cert cloud | FASE 6 Wave E | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-6](acts/ACT_GATE-6_deploy-run-cert-cloud-fase-6.md) |
| GATE-7 | Deploy+run+cert cloud | FASE 7 Aggregati/MSTR | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-7](acts/ACT_GATE-7_deploy-run-cert-cloud-fase-7.md) |
| GATE-PROD | Go-live PRODUZIONE (capstone → 8.x) | fine progetto | ⬜ proposed | 🏗️☁️ | [acts/ACT_GATE-PROD](acts/ACT_GATE-PROD_deploy-produzione-go-live.md) |

> Nota: **FASE 0** (infra) ha come gate il `terraform apply` stesso (ACT 0.1.x); **FASE 8** *è* la fase di
> deploy/shadow/cut-over → non hanno una `GATE-N` separata.

---

## 2. ACT fuori-sprint — Backlog
> Sviluppo tecnico offline non presente nel piano sprint. Le sezioni backlog infra-apply (I-), deploy (D-),
> validazioni (V-), quadrature (Q-), cut-over (C-), MicroStrategy (M-) e dipendenze esterne (E-) sono già
> coperte 1:1 dalle ACT sprint di FASE 0/2-8 → **non duplicate** qui. Le micro-righe sono clusterizzate per
> attività coerente (una ACT per tema, codice = rappresentativo).

| ACT | Titolo | Origine | Stato | Blocco | File |
|-----|--------|---------|-------|--------|------|
| OP-32 | LAD resolver generico | backlog L-01..04 / OP-32 | ✅ done | 🤝 (residuo OP-02) | [acts/ACT_OP-32](acts/ACT_OP-32_lad-resolver-generico.md) |
| OP-35 | Watermark rollout su _clean | backlog W-01..06 / OP-35 | ✅ done | 🏗️ (W-05/06) | [acts/ACT_OP-35](acts/ACT_OP-35_watermark-rollout.md) |
| G-01 | Supporto Parquet in Bronze | backlog G-01 | ✅ done | 🟢 | [acts/ACT_G-01](acts/ACT_G-01_parquet-bronze.md) |
| G-02 | Framework DQ condiviso | backlog G-02 / OP-21 | ⏸️ on-hold | 🤝 | [acts/ACT_G-02](acts/ACT_G-02_dq-framework-condiviso.md) |
| DBR-01 | Databricks-readiness (DBR-01..07) | backlog DBR-01..07 | 🔵 in-progress | ☁️🏗️ | [acts/ACT_DBR-01](acts/ACT_DBR-01_databricks-readiness.md) |
| ST-01 | Flusso stock mancante | backlog ST-01/02 | ⏸️ on-hold | 🟠 | [acts/ACT_ST-01](acts/ACT_ST-01_flusso-stock-mancante.md) |
| DQ-01 | Analisi chiave bolle uniche (DQ S7) | backlog DQ-01..03 | ✅ done | 🟢 | [acts/ACT_DQ-01](acts/ACT_DQ-01_chiave-bolle-uniche.md) |
| RS-01 | Rimozione rami secchi (8 notebook) | backlog RS-01..08 | ✅ done | 🟢 | [acts/ACT_RS-01](acts/ACT_RS-01_rimozione-rami-secchi.md) |
| MNT-01 | Manutenzione disco Docker/warehouse | backlog MNT-01/02 | 🔵 ricorrente | 🟢 | [acts/ACT_MNT-01](acts/ACT_MNT-01_manutenzione-disco-docker.md) |

---

## 3. ACT fuori-sprint — Open Points
> Gli OP restano governati dal registro SSOT [`05_open_points.md`](05_open_points.md). Qui si promuovono a
> ACT **solo** gli OP che sono **lavoro attivo pendente** non già coperto da un'altra ACT. Gli OP **risolti**
> vivono in ADR/spec di layer; gli OP di pura attesa (Reply/sorgente) restano nel registro (vedi mappa sotto).

| ACT | Titolo | OP | Stato | Blocco | File |
|-----|--------|-----|-------|--------|------|
| OP-02 | Lookup master Retail (nomi + permessi) | OP-02 (+01/04/05) | ⏸️ on-hold | 🤝 | [acts/ACT_OP-02](acts/ACT_OP-02_retail-master-lookups.md) |
| OP-08 | Conferme sorgente su ingestion | OP-08/09/10/11/31 | ⏸️ on-hold | 🟠 | [acts/ACT_OP-08](acts/ACT_OP-08_conferme-sorgente-ingestion.md) |
| OP-25 | Processo go-live + servizi piattaforma | OP-18/20/22/23/24/25 | ⏸️ on-hold | 🤝 | [acts/ACT_OP-25](acts/ACT_OP-25_processo-go-live-e-piattaforma.md) |

**Mappa degli altri OP (nessuna ACT dedicata — vedi registro):**
| OP | Dove è tracciato |
|----|------------------|
| OP-19 (serverless) | ADR-0009 · [acts/ACT_0.1.5](acts/ACT_0.1.5_cluster-policy-serverless.md) |
| OP-21 (DQ framework) | [acts/ACT_G-02](acts/ACT_G-02_dq-framework-condiviso.md) |
| OP-28 (orphan 0.0%) | [[op28-self-healing-operatori]] · spec Silver dim_operatore |
| OP-30 (incrementalità) | ADR-0010 |
| OP-32 (LAD) | [acts/ACT_OP-32](acts/ACT_OP-32_lad-resolver-generico.md) |
| OP-33/34/36 (grain/pattern#2/runner) | ADR-0010 · `05_open_points.md` |
| OP-35 (watermark) | [acts/ACT_OP-35](acts/ACT_OP-35_watermark-rollout.md) |
| OP-CAR-1 (VAL_COSTO_CARICO) | [acts/ACT_ST-01](acts/ACT_ST-01_flusso-stock-mancante.md) |
| OP-CAR-3/4/5, OP-PSP-1/2, OP-MOV-1 | `07_certifica_gold_vs_cdtdw.md` (certificazione) → Fase 4 |
| OP-03/07 | `05_open_points.md` (stand-by / residuo landing) |

---

## 4. ACT emergenti (9000+)
> Attività nate in corso d'opera (bug, DQ, nuovi sviluppi) fuori dal piano sprint. Progressivo da 9000.
> Rimandano ai doc SSOT di dettaglio (07 certifica, 14 release kit) senza duplicarne il contenuto.

| ACT | Titolo | Nata da | Stato | File |
|-----|--------|---------|-------|------|
| 9000 | Certificazione strutturale Gold vs CDT_DW (A0-A9) | ri-certifica fact | 🔵 in-progress (dati cloud-gated) | [acts/ACT_9000](acts/ACT_9000_certificazione-gold-vs-cdtdw.md) |
| 9001 | Rebuild F_CARICO a grain etichetta (WL_CARICO) | allineamento ODI | ✅ done | [acts/ACT_9001](acts/ACT_9001_rebuild-f-carico-grain-etichetta.md) |
| 9002 | Ammanco QTA_ORD_FORN in pezzi (OP-CAR-3) | certifica carico | ✅ done | [acts/ACT_9002](acts/ACT_9002_ammanco-qta-ord-forn-pezzi.md) |
| 9003 | F_MOVIMENTAZIONE — NUM_PLT (OP-MOV-1) | certifica movimentazione | ✅ done | [acts/ACT_9003](acts/ACT_9003_f-movimentazione-num-plt.md) |
| 9004 | Release kit go-live a fasi (KIT-01..08) | prep rilascio | ✅ done | [acts/ACT_9004](acts/ACT_9004_release-kit-go-live-fasi.md) |
| 9005 | Re-run di validazione + regressione (mirato, 21/21 OK) | validazione post-modifiche | ✅ done | [acts/ACT_9005](acts/ACT_9005_big-rerun-22-siti.md) |
| 9006 | Fix quadratura tombstone pyarrow (`_delta_log`) | CERT-01 / OP-CAR-4A | ✅ done | [acts/ACT_9006](acts/ACT_9006_fix-quadratura-tombstone-pyarrow.md) |
| 9007 | Allineare workflow + Terraform a serverless (ADR-0009) | cross-check doc-vs-codice | ✅ done (validaz. ☁️) | [acts/ACT_9007](acts/ACT_9007_allineamento-serverless-workflow-yml.md) |
| 9008 | Cleanup orchestrazione Wave E (yml placeholder rimosso) | cross-check doc-vs-codice | ✅ done | [acts/ACT_9008](acts/ACT_9008_cleanup-orchestrazione-wave-e.md) |
| 9009 | Estendere `quadratura_fact.py` (GIACENZE/TRASPORTO/TURNO/TRACC) | cross-check doc-vs-codice | ✅ done | [acts/ACT_9009](acts/ACT_9009_estendere-quadratura-fact-config.md) |
| 9010 | Task DQ standalone nei workflow (`dq_gate` + registry) | cross-check doc-vs-codice | ✅ done | [acts/ACT_9010](acts/ACT_9010_task-dq-standalone-nei-workflow.md) |
| 9011 | Split monorepo → 4 repo GitLab (+ Package Registry) | accesso subgroup GitLab | ⬜ proposed | [acts/ACT_9011](acts/ACT_9011_split-monorepo-4-repo-gitlab.md) |
| 9012 | Trasporto landing SFTP vs Blob (AzCopy/API) + send_to_landing pluggable | thread mail SFTP | ⬜ proposed | [acts/ACT_9012](acts/ACT_9012_trasporto-landing-sftp-vs-blob.md) |
| 9013 | Attribuzione costi serverless (usage/budget policy, ex custom_tags) | correzione serverless 9007 | ⬜ proposed | [acts/ACT_9013](acts/ACT_9013_tagging-costi-serverless-budget-policy.md) |
| 9014 | Riallineare workflow ai notebook reali (DAG derivato, 103 task) | audit durante ACT_9010 | ✅ done | [acts/ACT_9014](acts/ACT_9014_riallineare-workflow-notebook.md) |
| 9015 | Verifica integrità baseline Gold + rebuild storico movimentazione (17 date) | follow-up ACT_9005 | ✅ done | [acts/ACT_9015](acts/ACT_9015_verifica-integrita-baseline-gold.md) |
| 9016 | Guardrail pytest eseguibili in locale (classpath Delta + fixture Decimal + FQN) | follow-up ACT_9015 | ✅ done | [acts/ACT_9016](acts/ACT_9016_guardrail-pytest-eseguibili-locale.md) |
| 9017 | Script split monorepo → multi-repo (tooling di transizione, mono-direzionale) | domanda utente in ACT_9011 | 🔵 in-progress | [acts/ACT_9017](acts/ACT_9017_script-split-monorepo-transizione.md) |

---

## 5. ADR — Decisioni architetturali
> Popolato in Fase 1 (seeding retroattivo) e poi in continuo.

| ADR | Titolo | Status | Data | File |
|-----|--------|--------|------|------|
| 0001 | Catalog controllo = config_dev (D1) | accepted (retro) | 2026-07-02 | [adr/0001](adr/0001_config_dev_control_catalog.md) |
| 0002 | Lookup master in bronze.condiviso (D2) | accepted (retro) | 2026-07-02 | [adr/0002](adr/0002_bronze_condiviso_lu.md) |
| 0003 | Landing UC Volume managed (D3) | accepted (retro) | 2026-07-02 | [adr/0003](adr/0003_uc_volume_landing.md) |
| 0004 | Naming ambienti _dev/_prod/_stage (D4) | accepted | 2026-07-03 | [adr/0004](adr/0004_naming_ambienti_prod_stage.md) |
| 0005 | No segreti Oracle: export landing (D5) | accepted (retro) | 2026-07-02 | [adr/0005](adr/0005_no_secret_oracle_export_landing.md) |
| 0006 | Grain F_CARICO = etichetta + peso anagrafica | accepted | 2026-07-02 | [adr/0006](adr/0006_grain_etichetta_f_carico.md) |
| 0007 | Standard 2-notebook (curated/gold) | accepted | 2026-06 | [adr/0007](adr/0007_standard_2_notebook.md) |
| 0008 | Chiavi naturali validate in Gold | accepted | 2026-06 | [adr/0008](adr/0008_chiavi_naturali_gold.md) |
| 0009 | Job cluster serverless | accepted | 2026-07-03 | [adr/0009](adr/0009_job_cluster_serverless.md) |
| 0010 | Incrementale 3 pilastri (watermark/pattern#2/pruning) | accepted | 2026-06 | [adr/0010](adr/0010_incrementale_watermark_pattern2_pruning.md) |
| 0011 | LAD generico via _COD_NAT | accepted | 2026-06-20 | [adr/0011](adr/0011_lad_via_cod_nat.md) |
| 0012 | Ammanco in pezzi (unità omogenea) | accepted | 2026-07-05 | [adr/0012](adr/0012_ammanco_in_pezzi.md) |
| 0013 | F_TRASPORTO grana MTV | accepted | 2026-07-05 | [adr/0013](adr/0013_scope_trasporti_mtv.md) |
| 0014 | DQ & alerting interni | accepted | 2026-07-05 | [adr/0014](adr/0014_dq_alerting_interni.md) |
| 0015 | Tuning cloud non trasferibile dal locale | accepted | 2026-07-05 | [adr/0015](adr/0015_tuning_cloud_non_trasferibile.md) |
| 0016 | Codice GitLab multi-repo | accepted | 2026-07 | [adr/0016](adr/0016_multi_repo_gitlab.md) |
| 0017 | Go-live a fasi (no big-bang) | accepted | 2026-07-05 | [adr/0017](adr/0017_rilascio_a_fasi.md) |
| 0018 | Perimetro decisionale Reply | accepted | 2026-07-05 | [adr/0018](adr/0018_reply_scope_governance.md) |
| 0019 | Orchestrazione: DAG derivato dal codice | accepted | 2026-08-04 | [adr/0019](adr/0019_orchestrazione_dag_derivato.md) |
| 0020 | Lezioni operative: tracciamento cumulativo e scala di maturità | accepted | 2026-08-21 | [adr/0020](adr/0020_lezioni_operative.md) |

---

## Manutenzione
- Alla chiusura di una ACT: aggiornare la sua riga qui + il **file sprint** corrispondente
  (`sprint_agile/sprint_N.N.md`, vista SAL) + i doc globali impattati (`04` piano, `01` architettura,
  `02` pipeline, `05` open points, `07` certificazione, `milestones/fase_N`…). L'attività si svolge
  sull'**ACT** (SSOT del dettaglio); lo **stato** si riflette poi sullo sprint.
- Nuova attività emergente → nuova riga in §4 (codice 9000+) + file `acts/ACT_9000+_….md`.
- Nuova decisione → nuova riga in §5 + file `adr/NNNN_….md`.
- **Chiusura di fase**: una fase si marca chiusa (done reale) solo quando la sua `GATE-N` (§1-bis) è `done`
  — deploy in cloud TEST + run schedulato stabile + DQ verdi + dati certificati. Fino ad allora le sue ACT
  sono "done offline". Go-live PROD → `GATE-PROD`.
