# ACT_0.1.3 · Landing storage su UC Volume managed

**Status**: in-progress
**Type**: infra
**Origin**: sprint 0.1
**Sprint**: 0.1 — Unity Catalog & Storage Foundation
**Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali
**Gg (stima)**: 1
**Blocco**: 🏗️ infra (utenza Azure per `terraform apply`) · ☁️ dipende da risposta SFTP (Tech Reply)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_0.1.1 (catalog referenziati)   **Blocca**: ingestion bronze (tutti i `bronze_*`)
**ADR collegate**: ADR-0003 (UC Volume managed), ADR-0005 (export su landing)   **OP collegati**: OP-07 (path landing), C6 (checklist)

## Contesto e motivazione
I file estratti dai siti Logistix (CSV/Parquet) devono atterrare in una landing leggibile dai notebook
Bronze governati da Unity Catalog. La decisione D3 (ADR-0003) ha scelto un **UC Volume managed** invece di
External Location + Storage Credential, per semplicità e minor superficie IAM. Senza la landing pronta,
nessun `bronze_*` può eseguire.

## Obiettivo
Volume UC **managed** `landing_dev` creato e accessibile: `landing_mode="volume"`, path
`/Volumes/landing_dev/logistica/files`. Fatto = i notebook bronze leggono i file dal Volume via path UC.

## Analisi tecnica
- Terraform brownfield (`infra/terraform/brownfield/main.tf`) definisce il Volume managed; nessuna
  External Location ADLS.
- ⚠️ **Punto aperto C6 / OP-07**: il push SFTP arriva su un container dedicato (`logisticolanding`). Se il
  push resta **esterno** al perimetro UC, il Volume dovrà essere **external** (non managed) per leggerlo,
  oppure il push deve scrivere dentro il Volume managed. Da riconciliare con la risposta SFTP di Tech Reply
  (`landing_mode` → `external` vs `volume`).
- Convenzione path per sito/data (OP-07) ancora pending → coordina con `scripts/sftp/send_to_sftp.py` (KIT-01).

## Sviluppo (diario)
- 2026-07-02 · D3 confermato: Volume managed (no external location).
- 2026-07-03 · codice Terraform pronto; esecuzione bloccata su utenza Azure.

## Verifica
`terraform apply` crea il Volume; test di lettura di un file di prova dal path UC da un notebook bronze;
un `bronze_*` legge la landing senza errori di accesso.

## Esito
— (in attesa di accesso Azure)

## Follow-up
- Riconciliare `landing_mode` (managed vs external) alla risposta SFTP → eventuale ACT emergente 9000+.
