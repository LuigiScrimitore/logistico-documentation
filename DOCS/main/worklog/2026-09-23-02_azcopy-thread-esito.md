---
data: 2026-09-23
titolo: AzCopy: thread piattaforma concluso, decisioni (SAS + container)
autore: Luigi Scrimitore
push_monorepo: c743f99
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9012]
adr: [ADR-0023]
lesson: []
op: [OP-07]
---

## Cosa è stato fatto
- Recepito nel progetto l'esito del thread mail con la piattaforma (Reply/Conad) sul trasporto AzCopy. Architettura **confermata** (Silvio Torracchi: AzCopy nativo su blob, **niente SFTP** per il perimetro logistico; SFTP resta solo dove vincolante).
- Aggiornati ACT_9012 (esito), C5/C6 (doc 12) e OP-07 (doc 05) con le decisioni operative.

## Novità
- **Decisioni comunicate a Reply/Eddy**: container **`logisticolanding`** su SA esistente `stdevdataplatformweudata` (**solo template Blob, no RG**); **scrittura via SAS token** (Read/W/C/A/List; SP come evoluzione se fattibile da on-prem); **lettura via Access Connector + External Location**; **`landing_mode=external`**.
- **C6**: `landing_mode=external` **deciso** (era "da confermare") → 🟡 in provisioning.
- Costi stimati trascurabili (~€0,6–7/mese anche a 1 GB/giorno). Nessun ADR nuovo (resta [[ADR-0023]]).

## Doc aggiornati
12 (C5/C6/§F.2/stato-mail/tab G), ACT_9012 (esito), 05 (OP-07).

## Stato dopo il push / prossimi passi
Palla a **Reply** per il provisioning (container + SAS + Access Connector). Poi: `--send` reale + flip Terraform `landing_mode=external`. Ownership estrazione a monte (on-prem) ancora da confermare.
