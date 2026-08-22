# ADR-0003 · Landing su UC Volume **managed** (no External Location)

**Status**: accepted (retroactive) (2026-07-02)

**Contesto**:
I dati sorgente (file CSV/Parquet estratti dai siti Logistix, depositati via SFTP — vedi ADR-0005)
devono atterrare in una **landing zone** leggibile dai notebook Bronze governati da Unity Catalog. UC
offre due modi per accedere a storage esterno: (a) **External Location** appoggiata a una **Storage
Credential** (identità gestita/Service Principal con RBAC sul container ADLS), oppure (b) un **Volume
managed**, storage il cui ciclo di vita e accesso sono governati direttamente da UC. La scelta impatta
setup IAM, superficie di sicurezza e semplicità operativa del primo rilascio.

**Alternative considerate**:
1. **Storage Credential + External Location** su ADLS — massima flessibilità e controllo diretto sul
   container, ma richiede provisioning IAM aggiuntivo (SP, ruoli, external location) e gestione di una
   credenziale; più superficie da configurare e mantenere.
2. **UC Volume managed** (`landing_dev`) — storage gestito da UC: accesso governato dai grant UC, niente
   external location né credenziale separata; setup minimo.

**Decisione**:
Decisione **D3**: la landing è un **UC Volume managed** `landing_dev` (poi `landing_prod`), senza
Storage Credential né External Location. I notebook Bronze leggono i file dal Volume via path UC.

**Conseguenze**:
+ Setup più semplice e sicuro: l'accesso è governato dai grant UC, meno superficie IAM da gestire/auditare.
+ Coerente con D5 (nessun segreto nel workspace) e con l'obiettivo "primo rilascio senza attriti infra".
− Minore controllo diretto sul container ADLS sottostante (storage gestito da UC) — accettabile per una
  landing effimera/di transito; non è dato di business persistente.
− Vincolo: la struttura path della landing (per sito/data) è convenzione applicativa (OP-07), non
  imposta dallo storage.

**Riferimenti**:
- Sezione storage/landing: `10_piano_migrazione_databricks.md` (UC, Volume) e `01_architettura.md` (medallion, ingestion).
- Terraform: `infra/terraform/brownfield/` (Volume `landing_dev`). Backlog I-03. Memory `project-d1-d5-decisions`.
- Collegate: ADR-0005 (export/SFTP), OP-07 (convenzione path landing, pending).
