---
data: 2026-08-28
titolo: Allineamento doc post multi-repo deploy (auth secret -> MSI)
autore: luigi.scrimitore
push_monorepo: cc2505d
push_documentation: 6cf7161
push_gitlab: "—"
act: []
adr: []
lesson: []
op: [OP-INF-1]
---

## Cosa è stato fatto
- Allineati 9 doc principali allo stato post-deploy dei 3 repo su GitLab: auth CI da secret -> **Managed Identity**; split multi-repo + CI in DEV da "da fare/pilot" -> **eseguito**.
- (Stesso giorno, push separato `0c1a9be`) consolidata la presentazione SAL + tracciato l'assessment.

## Novità
- Info emersa: **OP-INF-1** (grant `CREATE SCHEMA` alla MI) è l'unico blocco per l'`apply` infra.

## Doc aggiornati
01, 03, 04, 05, 10, 11, 12, 14, 16.

## Stato dopo il push / prossimi passi
Doc allineati al deploy. Prossimo: formalizzare l'auth MSI come ADR (-> ADR-0022).
