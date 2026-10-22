---
data: 2026-10-21
titolo: "Release completa: fix join testata (ACT_9033) + sistema quadratura (ACT_9032) su dev via CI"
autore: Francesco Foconi
push_monorepo: "main @eb61205"
push_documentation: "GitHub single-repo aggiornato"
push_gitlab: "workflows v0.1.18 (deploy_dev success), lib v1.0.7 (sync) - push solo main, no tag (LL-031)"
act: [ACT_9033, ACT_9032]
adr: []
lesson: [LL-039]
op: [Q-01]
---

## Fatto (ciclo di release completo)
- **Monorepo** GitHub main @eb61205 (fix silver_prep v2.1.0, notebook quadratura, extract radice/variante, doc).
- **4 single-repo GitHub** rigenerati e pushati (lib 2c46caa, workflows bd1a266, infrastructure 90522d3,
  documentation 707901c).
- **GitLab** (push solo main, no tag — [[LL-031]]):
  - `logistico-workflows` **v0.1.18** → pipeline CI **6421**: `validate` + `deploy_dev` = **success**.
  - `logistico-lib` **v1.0.7** (sync sorgente; wheel sul Volume gia' aggiornato, nessun re-publish su main).
  - `infrastructure`: non modificata → nessun rilascio.

## Effetto
La fix join testata ([[ACT_9033]]) e il notebook di quadratura ([[ACT_9032]]) sono ora **deployati sui job dev
(MI)**: le prossime run schedulate producono F_CARICO a copertura ~98% vs CDT_DW (non piu' ~80%).

## Note
- `wheel` lib invariato dalla release vettore → nessuna azione (i notebook usano il Volume gia' aggiornato).
- Follow-up aperti: residuo ~2% (join MSI), opzione B merge-key per fedelta' per-ordine ([[ACT_9033]]), e il
  completamento del sistema di quadratura per il SAL ([[ACT_9032]]: estrazione schedulata + dashboard).
