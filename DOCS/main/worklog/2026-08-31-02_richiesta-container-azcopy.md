---
data: 2026-08-31
titolo: Inviata richiesta accesso container AzCopy (§F.2)
autore: luigi.scrimitore
push_monorepo: a37424a
push_documentation: ee8aff9
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: []
---

## Cosa è stato fatto
- Registrato l'invio (2026-08-31) della richiesta accesso landing per AzCopy: **un container unico** su `stdevdataplatformweudata` + auth (SAS/SP/MI) + accesso lettura da UC + conferma `landing_mode` external.

## Novità
- §F.2 riformulata (era "credenziali SFTP"). Info emersa: Logistico = **prototipo** per AzCopy standard (dismissione SFTP a tendere); da verificare il client AzCopy sulle macchine Linux d'invio (versione datata).

## Doc aggiornati
12 (F.2 / stato mail / tab G), 05 (OP-07), ACT_9012.

## Stato dopo il push / prossimi passi
Richiesta **inviata, in attesa risposta** piattaforma. Poi sblocco `--send` reale + conferma **C6** (`landing_mode`).
