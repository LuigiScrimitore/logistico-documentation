---
data: 2026-09-30
titolo: Risposta finale a Reply + chiarita landing interim (Volume managed, non SFTP)
autore: Luigi Scrimitore
push_monorepo: 44f88bb
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa è stato fatto
- **Inviata la risposta finale a Reply**: conferme (SAS solo `odisrvcno3`; READ FILES a `Group-Engineering-dev` + SP `id-dev-dataplatform-workload-00`; Access Connector dedicato read-only) + **retention 220gg** + **3 utenze operatore** (Erika Lo Iacono, Luigi Scrimitore, Francesco Foconi) Contributor su `logisticolanding`.
- Corretta la mail evitando due errori (chiedere di "chiudere" `unity-catalog-storage` / "spegnere SFTP").

## Novità
- **Chiarita la landing interim**: NON è SFTP → è il **Volume UC managed `landing_dev.logistica.files`** (backing Databricks `dbstoragecr5644pksnxyw`/`unity-catalog-storage`), alimentato via `databricks fs cp`; i job (`landing_ingestion`, `carichi`) leggono via **`landing_base_path`**.
- **Migrazione storico** = interna **Volume → `logisticolanding`** (via Databricks) → **nessun grant extra Reply**; la richiesta "read sorgente SFTP" **decade**.
- **Cutover pulito**: ricreare `landing_dev.logistica.files` come **Volume external** stesso nome → `landing_base_path` invariato, **zero change ai job**.

## Doc aggiornati
05 (OP-INF-4), 12 (stato-mail), ACT_9012.

## Stato dopo il push / prossimi passi
Provisioning **in esecuzione** lato Reply (container/SAS/Access Connector/3 utenze/lifecycle). Aperti lato nostro: **verifica trigger A (ssh 1/2→3)**, **migrazione storico + external Volume**, industrializzazione estrazione ODI. Alla consegna del SAS: attivazione relay + test upload.
