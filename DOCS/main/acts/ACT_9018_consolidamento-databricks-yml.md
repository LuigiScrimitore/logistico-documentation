# ACT_9018 · Consolidamento dei due `databricks.yml` in logistico-workflows

**Status**: proposed
**Type**: infra / DAB   **Origin**: emerged (split multi-repo, [[ACT_9011]] / [[ACT_9017]])
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 0 — Fondamenta   **Gg (stima)**: 0,5–1
**Blocco**: 🟡 richiede una decisione (modello di deploy) — meglio con input del team
**Created**: 2026-08-22   **Closed**: —
**Dipende da**: [[ACT_9011]] (split), DBR-05 (wheel su Package Registry)   **Blocca**: CI di `logistico-workflows`
**ADR collegate**: ADR-0016 (multi-repo), ADR-0009 (serverless), ADR-0017 (rilascio a fasi)   **OP collegati**: DBR-05

## Contesto e motivazione
Nel monorepo esistono **due `databricks.yml`** che lo split porta entrambi in `logistico-workflows`. Non sono
due frammenti dello stesso bundle: sono **due bundle paralleli** con nomi diversi.

| | `databricks.yml` (root) | `infra/databricks_bundle/databricks.yml` |
|---|---|---|
| `bundle.name` | `logistica_20` | `logistico2-0` |
| Job inclusi | `include: workflows/*.yml` — **7 job reali per area** (DAG allineato ai notebook, [[ACT_9014]]) | `include: resources/*.job.yml` — **wave KIT-06** (solo `logistica_wave_a`, "TEMPLATE di riferimento") |
| Variabili | complete (env, landing_base_path, retail_master_schema, email_alert; default D2/D3) | minime (env, notifications_email) |
| Cost tag | — | `presets.tags` (business_unit/project/env/managed_by — KIT-05) |
| Wheel | `artifacts` → **build da `lib/`** | — |
| Path | relativi al repo | `sync: ../../notebooks`, `../../lib` (rotti nel layout multi-repo) |
| Host | `${DATABRICKS_HOST}` (CI-friendly) | `https://<WORKSPACE_*_URL>` (placeholder) |

## Le decisioni (non è un merge meccanico)
1. **Modello di deploy** — le **7 pipeline per-area** (`workflows/*.yml`) *oppure* le **wave KIT-06**
   (`resources/*.job.yml`)? Sono due unità di rilascio diverse. È una scelta architatturale → **serve un ADR**
   (vedi sotto). Le due cose potrebbero coesistere (wave = raggruppamento di rilascio sopra le pipeline), ma va
   deciso, non ereditato per caso dal merge.
2. **Wheel dal Package Registry, non da `lib/`** — nel multi-repo `lib` è un repo separato: il blocco
   `artifacts` che builda da `lib/` non è più valido. Il wheel va dichiarato come **dipendenza pinnata** dal
   GitLab Package Registry (DBR-05). Questo è già coperto da ADR-0016/DBR-05 → **nessun ADR nuovo**, solo
   implementazione.
3. **Path e sync** — rimuovere i `../../` (validi solo nel monorepo); in `logistico-workflows` `notebooks/` è
   alla root e `lib/` **non c'è** (arriva come wheel).
4. **Merge del resto** — tenere le variabili ricche del root + i `presets.tags` (cost tag) del bundle + host
   via `${DATABRICKS_HOST}`; un solo `bundle.name`.

## Valutazione ADR
- **Sì, un ADR** per il **punto 1** (modello di deploy: per-area vs wave): è una scelta con alternative e
  conseguenze durature su CI, gate PROD e granularità di rilascio. Da scrivere **quando la decisione è presa**
  (idealmente con il team). Titolo previsto: *ADR-00xx · Modello di deploy DAB (pipeline per-area vs wave)*.
- **No ADR** per i punti 2–4: già coperti (ADR-0016/DBR-05) o meccanici.

## Dove si esegue
Il consolidamento va fatto nel **monorepo** (SoT in transizione), poi rigenerato in `logistico-workflows` con
`split_to_multirepo.py`. Aggiornare di conseguenza la mappatura in [[ACT_9017]] (oggi i due file vengono
affiancati con un warning).

## Esito
— (parcheggiato: attende la decisione sul modello di deploy).

## Follow-up
- Scrivere l'ADR del modello di deploy, poi consolidare in un unico `databricks.yml`.
- Agganciare il wheel dal Package Registry (DBR-05) e pinnarne la versione.
