---
data: 2026-09-25
titolo: Relay AzCopy odisrvcno3 pronto (staging+NFS+AzCopy)
autore: Luigi Scrimitore
push_monorepo: d32acf3
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0023]
lesson: []
op: [OP-INF-4]
---

## Cosa è stato fatto
- Provisionato e configurato il **relay Linux `odisrvcno3`** (Ubuntu 26.04.1 LTS, glibc 2.43, 8 vCPU/30 GiB, `10.8.1.158`) come **storage + sender** della landing.
- **Fase 1**: LV `landing` 500G su `/data/landing`; utenza `svc_landing` (uid 999/gid 983). **Fase 2**: **AzCopy 10.32.7**. **Fase 3**: NFS export verso agenti ODI `10.8.1.211`/`10.8.1.212` — giro **ODI → NFS → staging validato** (file owner `svc_landing`).
- Depositati gli artefatti sender (uploader + unit systemd) e **versionati** in `scripts/relay_azcopy/` (+ runbook README + `exports.example`).

## Novità
- **OP-INF-4** aggiornato: **scelta finale = relay Linux `odisrvcno3`** (supera l'ipotesi Windows). Variante 2 (estrazione sugli agenti ODI RHEL6 → NFS → relay AzCopy).
- **Storage via endpoint pubblico** (DNS → IP `20.x`, TLS/CA ok): **nessun Private Endpoint** → cade la complessità PE/DNS che temevamo.
- Trasporto = **AzCopy standard** ([[ADR-0023]]).

## Doc aggiornati
05 (OP-INF-4). Nuovi: `scripts/relay_azcopy/` (upload_landing.sh, landing-upload.service/.timer, exports.example, README).

## Stato dopo il push / prossimi passi
Server relay **pronto end-to-end tranne il SAS**. Gate esterni (Reply): **container `logisticolanding` + SAS** (upload reale) e **Access Connector + External Location** (lettura Databricks). Poi: attivare il timer + industrializzare l'estrazione ODI + retention/cleanup staging.
