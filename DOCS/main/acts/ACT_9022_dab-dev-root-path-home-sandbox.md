# ACT_9022 · DAB dev root_path nella home utente (self-deploy sandbox)

**Status**: done   **Type**: infra   **Origin**: emerged
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 0 — Piattaforma & Setup   **Closed**: 2026-09-02
**ADR collegate**: — (ADR dev/qa/prod in definizione dal team)   **OP collegati**: —

## Contesto
Il target `dev` del bundle (`databricks.yml`, mode:development) aveva `root_path` su una cartella **condivisa**
(`/Workspace/data-platform/etl/logistica/dev/<user>`). Le sandbox personali non hanno permessi su quella
cartella → `databricks bundle validate/deploy -t dev` falliva con **403 PERMISSION_DENIED** su `mkdirs`.

## Obiettivo
Le sandbox personali deployano senza grant esterni; la cartella condivisa resta a CI/Managed Identity.

## Esito
`databricks.yml` target `dev`: `root_path` → `/Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}`
(default DAB per mode:development). **PR #1** mergiato (`670098c`), opzione B concordata col team. Validato E2E:
`Validation OK!`, deploy 7 job `[dev <user>]`, run `dim_refresh`+`carichi` verdi. Target `prod` invariato.
Il modello **dev=home / qa=condiviso-CI / prod** sarà formalizzato in un **ADR dedicato** dal team.

## Lezioni
- [[LL-023]] — DAB mode:development: root_path in home per le sandbox, non in cartella condivisa.
