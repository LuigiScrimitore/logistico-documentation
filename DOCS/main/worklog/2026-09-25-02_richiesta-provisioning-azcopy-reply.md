---
data: 2026-09-25
titolo: Richiesta provisioning AzCopy inviata a Reply
autore: Luigi Scrimitore
push_monorepo: dcf4d24
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa è stato fatto
- Inviata a Reply/Eddy la **richiesta formale di provisioning** lato Azure per chiudere il flusso AzCopy: **container `logisticolanding` + SAS** (Read/Write/Create/Add/List) e **Access Connector + External Location** per la lettura da Databricks (`landing_mode=external`).
- Registrato l'invio nei doc.

## Novità
- On-prem **pronto** (relay `odisrvcno3`); ora la palla è **tutta lato Reply** (i due gate esterni).
- Nessuna nuova decisione: conferma SAS come auth iniziale, SP come evoluzione futura.

## Doc aggiornati
12 (§F.2 + stato-mail #3), 05 (OP-INF-4 status), ACT_9012 (follow-up).

## Stato dopo il push / prossimi passi
In **attesa risposta Reply**. Alla consegna: SAS in `/opt/landing/secrets/sas` → test `sudo -u svc_landing /opt/landing/bin/upload_landing.sh` → `enable --now landing-upload.timer`; poi flip Terraform `landing_mode=external` a valle dell'External Location. Lato nostro resta l'industrializzazione dell'estrazione ODI.
