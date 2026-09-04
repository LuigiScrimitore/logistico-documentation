---
id: LL-023
titolo: DAB mode:development — il root_path va nella home utente, non in una cartella condivisa
sintomi:
  - "Error: unable to create directory at /Workspace/data-platform/.../<user>/files"
  - "403 PERMISSION_DENIED ... does not have View permissions on <id>"
  - "databricks bundle validate/deploy -t dev fallisce su POST /api/2.0/workspace/mkdirs"
tag: [databricks, dab, sandbox, permessi, ci-cd, ambiente-cliente]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-02
origine: [ACT_9022]
---

## Sintomo
`databricks bundle validate -t dev` (o `deploy`) da una sandbox personale fallisce con **403
PERMISSION_DENIED** su `mkdirs`: l'utente non ha i permessi per creare la propria sottocartella sotto il
`root_path` del bundle, perché punta a una **cartella condivisa** (es. `/Workspace/data-platform/etl/...`).

## Strada sbagliata
Per il target `dev` (mode:development) fissare un `root_path` condiviso con `${workspace.current_user.userName}`
in coda, pensando che basti a isolare per utente. Isola il **path finale**, ma il DAB deve comunque creare/scrivere
nella cartella **parent condivisa** — e lì la sandbox non ha permessi. Chiedere un grant workspace al team per
ogni utente è possibile (CAN_MANAGE sulla cartella) ma è attrito ricorrente.

## Regola
Per `mode: development` lasciare il **default DAB**: `root_path` nella home utente.
```yaml
targets:
  dev:
    mode: development
    workspace:
      root_path: /Workspace/Users/${workspace.current_user.userName}/.bundle/${bundle.name}/${bundle.target}
```
Le sandbox deployano nella propria home (permessi garantiti); la cartella condivisa resta riservata a
**CI/Managed Identity**. Il target `prod` (mode:production) resta su path fisso condiviso.

## Perché
In `mode: development` il DAB isola già per utente e la home è lo spazio dove l'utente ha sempre CAN_MANAGE.
Un root_path condiviso ha senso solo per un'identità con permessi sulla cartella (la CI/MI), non per N sandbox
personali. È la direzione dev=home / qa=condiviso-CI / prod (ADR dev/qa/prod in definizione dal team).

## Conferme e contraddizioni
- 2026-09-02 · Francesco Foconi · con root_path condiviso: 403 su `mkdirs`. Con root_path in home: `Validation OK!`,
  deploy 7 job `[dev <user>]`, run `dim_refresh`+`carichi` verdi E2E.
