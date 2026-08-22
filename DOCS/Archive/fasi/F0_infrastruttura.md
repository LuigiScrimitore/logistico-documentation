# FASE 0 — Infrastruttura & Piattaforma

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** — | **Stato:** 🔵 IN CORSO — Sprint 0.1 attivo (Terraform completo, apply pendente decisioni D1/D3/D5); 0.2/0.3 ✅

## 1. Obiettivo & scope
Predisporre la piattaforma su cui gira la pipeline: Unity Catalog, storage/landing, compute, libreria
condivisa, orchestrazione (DAB) e CI/CD. Target = **Databricks/DWW aziendale esistente** (brownfield):
non si crea un workspace nuovo, ci si **integra**.

## 2. Componenti
| Componente | Artefatto | Stato |
|---|---|---|
| Unity Catalog (schemi logistici nei catalog esistenti) | `infra/terraform/brownfield/` | codice pronto |
| Compute (cluster policy serverless) | `infra/terraform/brownfield/main.tf` | ✅ job cluster serverless (D 2026-07-03) |
| Libreria condivisa | `lib/logistica_utils/` (wheel via `lib/setup.py`) | ✅ |
| Astrazione path | `lib/logistica_utils/storage.py` | ✅ `is_databricks()`, `get_landing_root()` |
| Orchestrazione | `databricks.yml` + `workflows/*.yml` (8 job DAB) | brownfield risolto |
| CI/CD | `.gitlab-ci.yml` (validate→plan→deploy dev) | riusabile, adattare ai 3 repo del subgroup |
| Git | subgroup `logistico` multi-repo (infrastructure/workflows/lib) | `git_monorepo_import.sh` obsoleto |
| Preflight | `scripts/migration/preflight_databricks.sh` | ✅ |

## 3. Unity Catalog target (brownfield)
Catalog esistenti **referenziati** (non creati): `bronze_dev`, `silver_dev`, `gold_dev`, `config_dev`
(D1), `landing_dev`. Schemi creati dall'overlay:
`bronze.logistica`, `bronze.condiviso` (D2), `silver.logistica`, `silver.logistica_curated`,
`gold.logistica`, `gold.logistica_dm`, `config.logistica_etl` (watermark), `landing.logistica` + Volume `files` (D3).

## 4. Ingestion
**Push** dai sorgenti (Logistix + cdt_dw) su Volume/ADLS landing → **nessuna** connettività Oracle,
VNet, Key Vault credenziali sorgente su Databricks. Il modulo `modules/networking` **non si applica**.

## 5. Stato Sprint 0.1 — azioni per sbloccare il provisioning (agg. 2026-07-03)

Decisioni D1-D5 **chiuse**. Blocchi residui = prerequisiti di piattaforma (vedi `../12_checklist_infra_setup.md`).

| Attività | Stato | Azione |
|---|---|---|
| 0.1.1 Cataloghi UC (solo DEV) | 🔵 pronto | `terraform apply` brownfield (dipende da utenza Azure) |
| 0.1.2 Schemi dominio | 🔵 pronto | Eseguito dall'overlay |
| 0.1.3 Landing UC Volume | ✅ D3 confermato | Volume MANAGED `landing_dev`, no external location |
| 0.1.4 ~~Key Vault~~ | ✅ soppresso | No segreti Oracle (D5); auth via GitLab CI/CD |
| 0.1.5 Cluster Policy | ✅ serverless | `logistico-serverless-job-policy` |
| 0.1.6 Terraform state backend | ✅ compilato | `rg-dev-dataplatform-00` / `stdevdataplatformweu00` / `statefile` |
| 0.1.7 Grants least-privilege | 🟡 parziale | Writer `Engineering-dev` ✅; reader condizionale (gruppo non ancora creato) |

## 6. Decisioni — tutte chiuse
D1 (`config_dev`), D2 (`bronze_<env>.condiviso`), D3 (UC Volume), D4 (`_prod`/`_stage`), D5 (export su landing).
Compute serverless; Git multi-repo. Dettaglio in `../10_piano_migrazione_databricks.md` (checklist) e `../12_checklist_infra_setup.md`.
Prerequisiti residui (non decisioni): utenza Azure, subgroup GitLab, credenziali SFTP.

## 6. Data Quality & guardrail
- `terraform plan` fallisce se un catalog target manca (fail-safe brownfield).
- Non applicare `modules/unity_catalog` (greenfield) sul DWW.
- `terraform.tfvars` e token mai committati (gitignored).

## 7. Open points di fase
- **D1-D5** (migrazione) — ✅ chiuse, vedi `../05_open_points.md` sez. G.
- Prerequisiti piattaforma (utenza Azure, subgroup GitLab, SFTP) — `../12_checklist_infra_setup.md`.
- OP-18 (Service Principal unico data platform) — ⏸️ in attesa Technology. OP-19 (cluster serverless) — ✅ risolto.

## 8. Runbook operativo (DevOps)
Sequenza completa in `../11_devops_handoff_databricks.md` §4 (FASI A-D): preflight → terraform apply
overlay → build wheel → bundle deploy → creazione repo nel subgroup → push sorgenti → primo run.

## 9. Riferimenti
`../01_architettura.md`, `../10_piano_migrazione_databricks.md`, `../11_devops_handoff_databricks.md`,
`infra/terraform/brownfield/`, `scripts/migration/`.
