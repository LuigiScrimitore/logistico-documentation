---
data: 2026-09-29
titolo: Reply conferma provisioning AzCopy + trigger A (open point ssh)
autore: Luigi Scrimitore
push_monorepo: 3d1a58a
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa è stato fatto
- **Reply (Eddy) ha confermato** e procede col provisioning AzCopy. Inviata la nostra risposta con le conferme operative + due richieste aggiuntive (retention, utenze operatore).
- Registrate le decisioni nei doc.

## Novità
- **Provisioning concordato**: container `logisticolanding` (no nuovo RG/SA); **SAS** limitato al container (R/W/C/A/List, scad. **31/03/2027**, canale sicuro); **Access Connector + identità dedicati** read-only; **READ FILES** a `Group-Engineering-dev` + SP `id-dev-dataplatform-workload-00`.
- **Retention**: lifecycle **220 gg** (DEV; poi 30 dopo migrazione PROD). **2 utenze operatore** (Luigi, Francesco Foconi) `Storage Blob Data Contributor` sul container.
- **Trigger invio = Opzione A** (OSCommand ODI → `ssh` → AzCopy su `odisrvcno3`), per tenere il lineage in ODI. ⚠️ **OPEN POINT**: verifica `ssh` RHEL6 → Ubuntu 26.04 (fallback: marker+watcher).

## Doc aggiornati
05 (OP-INF-4), 12 (§F.2 + stato-mail), ACT_9012 (follow-up).

## Stato dopo il push / prossimi passi
In **attesa esecuzione** provisioning da Reply (container/SAS/Access Connector/utenze/lifecycle). Poi: SAS sul relay → test upload → attivazione; verifica trigger A (ssh 1/2→3); industrializzazione estrazione ODI.
