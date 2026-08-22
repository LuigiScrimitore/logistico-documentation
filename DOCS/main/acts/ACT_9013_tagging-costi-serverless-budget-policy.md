# ACT_9013 · Attribuzione costi su serverless — usage/budget policy (non `custom_tags`)

**Status**: proposed
**Type**: infra   **Origin**: emerged (correzione serverless [[ACT_9007]], 2026-08-04)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (governance costi)
**Gg (stima)**: 0.5 (nostra parte) + attesa piattaforma   **Blocco**: 🤝 Reply/Technology (policy a livello account)
**Created**: 2026-08-04   **Closed**: —
**Dipende da**: [[ACT_9007]] (rimozione job cluster), H1 checklist infra   **Blocca**: reportistica costi per area logistica
**ADR collegate**: ADR-0009 (serverless), ADR-0004 (naming/costi)   **OP collegati**: H1 (tagging costi Databricks)

## Contesto e motivazione
Con il passaggio ai job **serverless** ([[ACT_9007]]) sono spariti i `custom_tags` del job cluster, che erano
il modo con cui i workflow marcavano `domain: logistica`, `area: <area>`, `project: logistico_20`. Su
serverless il compute è gestito da Databricks: **i tag di billing si applicano tramite le _serverless
usage/budget policy_ a livello di account** (feature in Public Preview), non nella definizione del job.
Questo era già stato intuito in **H1** della checklist infra ("serverless budget policy a livello di account
per applicare i tag ai job") dopo la call del 2026-07-03 sul tema costi (Silvio/Marcello).

Restano validi i **tag a livello job** (`tags:` nei `workflows/*.yml`), utili per organizzare/filtrare i job
nella UI, ma **non** sufficienti per l'attribuzione della spesa serverless.

## Obiettivo
Spesa serverless dell'area logistica attribuibile (min. `business_unit=logistica`), tramite serverless
usage/budget policy assegnata ai nostri job, e verificabile dalla system table di billing.

## Analisi tecnica
- **Cosa NON funziona più**: `new_cluster.custom_tags` (non esiste compute da taggare).
- **Cosa resta**: `tags:` a livello job nei 7 workflow (già presenti: `domain`/`area`/`project`) → utili per
  filtro/organizzazione, non per il billing.
- **Cosa serve**: una **serverless usage (budget) policy** creata a livello di **account** con i tag standard
  concordati; poi assegnata ai job/utenti dell'area. **Nota**: i job esistenti **non** vengono taggati
  retroattivamente — vanno riassociati alla policy.
- **Chi**: la creazione è governance di piattaforma → **Reply/Technology** (H1). Il naming dei tag va
  concordato con loro (min. `business_unit=logistica`, coerente con ADR-0004).
- **Verifica costi**: query sulla *billable usage system table* filtrando per i tag della policy.
- **Nostra parte**: (a) confermare i tag standard, (b) assegnare la policy ai job al primo deploy, (c) tenere
  i `tags:` job-level allineati. Vedi anche `lib/logistica_utils/cost_tags.py` (KIT-05) — **da rivedere**: se
  implementava tag su cluster, va riallineato al modello serverless (**da verificare**).

## Sviluppo (diario)
- 2026-08-04 · emersa dalla correzione serverless: rimossi i `custom_tags` dai 7 workflow.

## Verifica
Policy assegnata ai job logistici; nella system table di billing la spesa serverless risulta filtrabile per
i tag concordati (almeno `business_unit=logistica`).

## Esito
— (in attesa policy di account; nostra parte al primo deploy)

## Follow-up
Integrare al gate deploy ([[ACT_GATE-1]] e [[ACT_8.1.2]]); chiude H1 della checklist infra.
