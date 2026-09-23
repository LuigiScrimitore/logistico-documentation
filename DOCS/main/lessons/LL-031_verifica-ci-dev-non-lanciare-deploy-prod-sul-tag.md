---
id: LL-031
titolo: Verifica CI dev — usare la pipeline `main` (deploy_dev auto), NON eseguire il gate `deploy_prod` sul tag
sintomi:
  - "sulla pipeline del tag l'unica azione manuale è deploy_prod → cliccandola parte `bundle deploy -t prod`"
  - "creati 7 job logistica_* (canonici, senza prefisso) sotto /Workspace/.../prod/ non voluti"
  - "bundle destroy -t prod da utente personale: no such directory .../prod/state / permission error"
tag: [gitlab, ci, databricks, dab, deploy, prod, schedule, acl]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-21
origine: [incidente-deploy-prod-involontario, LL-030]
---

## Sintomo
Per verificare la CI dev si pusha `workflows` su GitLab con `--tags`. Il **tag** crea una pipeline con
`validate` + **`deploy_prod`** (manuale). Su quella pipeline l'**unica azione manuale disponibile è
`deploy_prod`**: cliccandola parte `databricks bundle deploy -t prod` → crea **7 job `logistica_*`**
(canonici, `mode:production`) sotto `/Workspace/data-platform/etl/logistica/prod/`. Non voluti per una
verifica dev.

## Perche' (non ovvio)
- Il **deploy DEV avviene da solo** sulla pipeline del branch **`main`** (`deploy_dev -t dev`): per
  verificare il dev **non serve lanciare nulla a mano**.
- La pipeline del **tag** serve alla release PROD: `deploy_prod` e' un **gate manuale** ([[ADR-0017]]) e
  va **lasciato non eseguito** (stato "Blocked"), come nelle release precedenti.
- Cliccarlo "perche' era l'unica opzione della pipeline del tag" e' l'errore: quella pipeline non era
  quella da guardare per il dev.

## Regola
- **Verifica CI dev = pipeline `main`** (deploy_dev automatico). Non toccare la pipeline del tag.
- **Per una verifica dev, push SOLO `main`** (`git push origin main`, **senza** `--tags`): cosi' non si
  crea la pipeline col bottone `deploy_prod`. Il tag/versione si spinge solo quando si fa davvero la
  release prod.
- **`mode: production` NON mette in pausa gli schedule**: job prod creati per errore possono **partire
  da soli** e fallire (catalogo/landing prod vuoti) → vanno rimossi.
- **Cleanup prod = solo MI/CI o admin**: `databricks bundle destroy -t prod` da un **utente personale**
  fallisce (`no such directory .../prod/state`, permission) perche' il path prod condiviso e' della MI.
  Serve chi ha i permessi su `/Workspace/data-platform/etl/logistica/prod/`.

## Conferme e contraddizioni
- 2026-09-21 · Incidente: su pipeline tag `v0.1.7` cliccato `deploy_prod` involontariamente → 7 job
  prod creati (`logistica_giacenze/_dim_refresh/_landing_ingestion/_trasporti/_aggregati/_carichi/_prep_sped`).
  `destroy -t prod` tentato da `flabffoconi` → **permission denied** sul path prod → richiesto intervento
  MI/admin. Vale insieme a [[LL-030]] (duplicati CI) e alla nota naming: in DEV i nomi hanno il prefisso
  `[dev …]` (standard di piattaforma), in PROD sono canonici `logistica_*` (corretto per `mode:production`).
