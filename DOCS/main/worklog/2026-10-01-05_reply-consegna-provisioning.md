---
data: 2026-10-01
titolo: Reply consegna il provisioning (container + SAS + UC); avvio collaudo
autore: Luigi Scrimitore
push_monorepo: fa2972a
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa e' stato fatto
- **Reply (Eddy) ha consegnato il provisioning** dello storage di landing:
  - Container **`logisticolanding`** (privato) con **lifecycle 220 gg** (last-modified); retention altri container preservata.
  - **SAS** R/W/C/A/List, **HTTPS-only**, scad. **31/03/2027**, via **stored access policy** `logistico-azcopy-20270331`
    (file `logistico-azcopy-access.json`). **NB: il SAS non ha `Delete`** → cancellare/spostare = utenze Contributor.
  - UC read-only per Databricks: Access Connector **`ac-dev-logistico-00`**, Storage Credential **`logisticolanding_dev_ro`**,
    External Location **`logisticolanding_dev`**; READ FILES a `Group-Engineering-dev` + SP `id-dev-dataplatform-workload-00`
    (appId `54d17490-ef40-4a5d-969a-dad1ccf7ada6`). Contributor sul container a Erika Lo Iacono/Luigi Scrimitore/Francesco Foconi.
- **Messo in sicurezza il segreto**: `.gitignore` → `*azcopy-access*.json` + `*.sas`. Il file del SAS resta **untracked**
  (non entra nel repo); va posato solo su `odisrvcno3`.

## Novita'
- `Blocco` OP-INF-4 / ACT_OP-INF-4 passa da "🤝 Reply (SAS)" a **nessuno**: ora è lavoro nostro (collaudo + migrazione).
- Nomi oggetti UC registrati nei doc (riuso per la migrazione storico e il flip `landing_mode=external`).

## Doc aggiornati
- `05_open_points.md` (OP-INF-4: blocco "provisioning consegnato", dettagli oggetti), `acts/ACT_OP-INF-4` (diario +
  Status/Blocco), `.gitignore`.

## Stato dopo il push / prossimi passi
- **Collaudo dal relay in corso**: su `odisrvcno3` posa SAS in `secrets/dev/logistico.sas` (600) + `conf/dev/logistico.conf`
  + `staging/dev/logistico` + **ri-deploy `upload_landing.sh` dal repo** → `upload_landing.sh dev logistico` deve chiudere
  `exit=0` (verifica con `azcopy list`). Poi: trigger E2E da ODI, **migrazione storico Volume→logisticolanding** +
  ricreazione external Volume stesso nome, industrializzazione estrazione ODI.
