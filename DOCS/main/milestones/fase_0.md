# Milestone — FASE 0: Fondamenta Infrastrutturali

> **Documento di chiusura di fase — deliverable di progetto per il cliente.**
> Contiene il quadro tecnico e funzionale della Fase 0: perimetro, architettura, decisioni, stato, punti aperti/risolti, decisioni out-of-scope e sviluppi futuri.
> Sostituisce il precedente `fasi/F0_infrastruttura.md` (archiviato). Stato di dettaglio degli sprint: [`../sprint_agile/`](../sprint_agile/) (0.1, 0.2, 0.3).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 IN CORSO (Sprint 0.1 attivo; 0.2/0.3 ✅)

---

## 1. Executive summary (funzionale)

La Fase 0 predispone le **fondamenta infrastrutturali** su cui gira l'intera pipeline Logistico 2.0: gli spazi dati su Unity Catalog (Databricks brownfield), la zona di atterraggio dei file (landing), il compute, la libreria condivisa, la CI/CD e i template di sviluppo.

Il principio guida è **integrarsi nel Databricks/DWH aziendale esistente senza romperlo**: non creiamo un workspace nuovo, ma i nostri schemi accanto a quelli esistenti. L'ingestion avviene in **push (SFTP)** dai sistemi sorgente, eliminando ogni connettività Oracle diretta.

Alla data, gli sprint 0.2 (CI/CD & DAB) e 0.3 (template & connettività) sono **completi**; lo sprint 0.1 (Unity Catalog & Storage) ha il **codice pronto** ma l'esecuzione è bloccata su prerequisiti di piattaforma lato cliente (utenza Azure, subgroup GitLab, credenziali SFTP).

---

## 2. Perimetro e obiettivi

| Obiettivo | Esito |
|-----------|-------|
| Spazi dati Unity Catalog per dominio logistico | ✅ codice pronto (overlay brownfield) |
| Zona di landing per i file in push | ✅ definita (UC Volume / container SFTP dedicato) |
| Compute per i job | ✅ job cluster serverless |
| Libreria condivisa `logistica_utils` | ✅ 6 moduli, 64 test |
| CI/CD e Databricks Asset Bundles | ✅ pipeline + `databricks.yml` |
| Template notebook (Bronze/Silver/Gold) | ✅ 3 template + logging standard |

---

## 3. Architettura e deliverable tecnici

### 3.1 Unity Catalog (brownfield)
Catalog esistenti **referenziati** (non creati): `bronze_dev`, `silver_dev`, `gold_dev`, `config_dev` (D1), `landing_dev`. Schemi creati dall'overlay `infra/terraform/brownfield/`:
`bronze.logistica`, `bronze.condiviso` (D2), `silver.logistica`, `silver.logistica_curated`, `gold.logistica`, `gold.logistica_dm`, `config.logistica_etl`, `landing.logistica` + Volume `files`.

### 3.2 Ingestion
**Push SFTP** dai sorgenti (Logistix + cdt_dw) → landing. Nessuna connettività Oracle / VNet / Key Vault credenziali sorgente su Databricks. Struttura `<source>-landing/<tabella>/YYYY/MM/DD/`, formato CSV (Parquet pronto lato codice), SLA disponibilità 04:00.

### 3.3 Compute
Job **serverless**: nessuna VM da gestire, avvio col job e terminazione al completamento; Photon e
autoscaling automatici. Implementazione (corretta il 2026-08-04, ACT_9007): i job **non dichiarano compute**
nei `workflows/*.yml` e le dipendenze (wheel `logistica_utils`) passano da un blocco `environments` +
`environment_key`. **Nessuna cluster policy**: non è applicabile al serverless. Vedi ADR-0009.

### 3.4 Libreria & template
`lib/logistica_utils/` (secret_helper, logging, delta, dq, utils, storage) — wheel per i job. Template `template_bronze/silver/gold_fact.py`. Astrazione path `storage.py` (`is_databricks()`, `get_landing_root()`).

### 3.5 CI/CD & Git
Databricks Asset Bundles (`databricks.yml`) + GitLab CI (`.gitlab-ci.yml`). Git: **multi-repo** in subgroup `logistico` (`logistico-infrastructure`/`-workflows`/`-lib`).

---

## 4. Sprint della fase

| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 0.1 | Unity Catalog & Storage Foundation | 🔵 IN CORSO | [sprint_0.1](../sprint_agile/sprint_0.1.md) |
| 0.2 | GitLab CI/CD & Databricks Asset Bundles | ✅ | [sprint_0.2](../sprint_agile/sprint_0.2.md) |
| 0.3 | Connettività Sorgenti & Template Notebook | ✅ | [sprint_0.3](../sprint_agile/sprint_0.3.md) |

---

## 5. Decisioni prese (D1-D5 + compute/Git)

| ID | Decisione | Esito |
|----|-----------|-------|
| D1 | Catalog di controllo | `config_dev` + schema `logistica_etl` |
| D2 | Anagrafiche cdt_dw | Schema proprio `bronze_dev.condiviso` (isolamento; aggancio futuro a Gold Retail) |
| D3 | Landing storage | UC Volume in `landing_dev` (riconciliazione managed/external in corso) |
| D4 | Ambiente prod/stage | `_prod` / `_stage`; solo DEV configurato ora; catalog senza suffisso da eliminare |
| D5 | Lettura DWH legacy per quadratura | Export su landing (no JDBC diretto) |
| — | Compute | Job cluster serverless |
| — | Git | Multi-repo in subgroup `logistico` |

---

## 6. Punti risolti
- **OP-19** — cluster: risolto con job cluster serverless.
- **0.1.4** (Key Vault) — soppresso: nessun segreto Oracle su Azure, auth via GitLab CI/CD.
- **DBR-01/02/03** — storage abstraction, helper condiviso anagrafiche, riconciliazione `_CATALOG_MAP`.

## 7. Punti aperti
- **Prerequisiti piattaforma** (non decisioni): utenza Azure, subgroup GitLab + runner, credenziali SFTP. Vedi [`../12_checklist_infra_setup.md`](../12_checklist_infra_setup.md).
- **C6** — riconciliazione `landing_mode` managed vs external (dipende da risposta SFTP Tech Reply).
- **OP-18** — Service Principal unico data platform (⏸️ Technology).
- **Modello costi/chargeback** tra aree (retail vs logistica) — in discussione con infra (tag/budget policy vs RG/catalog dedicati).

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- **Catalog dedicati per la logistica** (`bronze_logistica_dev`…): valutati e **scartati** — deviano dallo standard di piattaforma, raddoppiano ambienti/grant, senza benefici reali (compute separato via tag, non via catalog). Riconsiderabili solo se imposti da governance/finance.
- **Separazione accessi per area**: scartata volutamente — la logistica deve vedere/intervenire sul retail, quindi gruppo UC condiviso `Engineering-dev`.
- **Connessione diretta Oracle da Databricks**: fuori scope (D5 = export su landing); rivalutabile in futuro.
- **Cifratura colonne**: non applicabile (dati operativi logistici, no PII).

## 9. Sviluppi futuri
- Aggancio anagrafiche master al **Gold Retail** quando disponibili (OP-02) → ripuntare `retail_master_schema`.
- Backend Spark-native per la quadratura su Databricks (DBR-04).
- Attivazione ambiente PROD/stage (D4) quando il progetto sarà pronto al rilascio.
- Eventuale passaggio landing a formato **Parquet** (codice già pronto).

---

## 10. Riferimenti
- Handoff DevOps: [`../11_devops_handoff_databricks.md`](../11_devops_handoff_databricks.md)
- Checklist infra + mail cliente: [`../12_checklist_infra_setup.md`](../12_checklist_infra_setup.md)
- Piano migrazione + decisioni: [`../10_piano_migrazione_databricks.md`](../10_piano_migrazione_databricks.md)
- Open points: [`../05_open_points.md`](../05_open_points.md)
- Codice: `infra/terraform/brownfield/`, `lib/logistica_utils/`
