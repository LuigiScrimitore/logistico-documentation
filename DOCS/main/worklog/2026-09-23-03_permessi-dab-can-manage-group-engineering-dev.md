---
data: 2026-09-23
titolo: "Permessi job DAB: CAN_MANAGE Group-Engineering-dev nel databricks.yml (target dev) — LL-032"
autore: Francesco Foconi
push_monorepo: "PR dedicata (databricks.yml + LL-032 + worklog)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "da rilasciare (workflows) per applicare i permessi al deploy dev"
act: []
adr: []
lesson: [LL-032]
op: []
---

## Contesto
Verificato che i 7 job dev (`[dev <mi>] logistica_*`) sono creati e **posseduti dalla Managed Identity**
via CI → noi (utenti personali) **non li vediamo** (ACL). L'admin ha confermato che sui job **DAB** non
può aggiungere grant a mano (il deploy li riallinea): la via corretta è dichiararli nel bundle ([[LL-032]]).

## Cosa
- `databricks.yml`, target **dev**: aggiunto blocco `permissions:` → `CAN_MANAGE` a `Group-Engineering-dev`.
  Vale per tutte le risorse del bundle; al prossimo `deploy_dev` il gruppo vedrà/gestirà i job dev.
- Doc: [[LL-032]] (permessi DAB nel bundle) + INDEX rigenerato.
- Nessun tocco a `root_path` (stabile, [[LL-030]]) né altri target.

## Prossimi passi
1. Merge PR monorepo.
2. Rilascio `workflows` su GitLab (push **solo `main`**, no tag — [[LL-031]]) → `deploy_dev` **applica i permessi**.
3. Verifica: `Group-Engineering-dev` (e quindi Foconi/Scrimitore) vede i job `[dev <mi>] logistica_*` e può lanciarli.

## Nota coordinamento
Cambia lo stesso file (`databricks.yml`) su cui Luigi lavorerà per il target **stage** ([[ACT_9028]]/[[ADR-0027]]):
sezioni diverse (permissions su dev vs nuovo target stage) → nessun conflitto atteso, ma da coordinare l'ordine dei merge.
