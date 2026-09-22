---
data: 2026-09-21
titolo: "Release GitLab workflows v0.1.7 (fix .cache LL-029) — verifica CI dev cliente"
autore: Francesco Foconi
push_monorepo: "doc-pass runbook16 + worklog (PR dedicata)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "workflows v0.1.7 (github @d419072) — push su main per verifica CI dev"
act: []
adr: []
lesson: [LL-030, LL-029]
op: [OP-INF-3]
---

## Contesto
Chiuso l'incidente duplicati ([[LL-030]]): baseline Databricks **pulito (0 job)** confermato dall'infra,
root_path **stabile**, naming standard `[dev <identità>]` mantenuto. **Freeze GitLab revocato**
(push concordato: pusha Francesco, uno solo → niente pipeline concorrenti). Si promuove `workflows`
su GitLab per **verificare che la CI cliente giri correttamente** e **confermare l'assenza di duplicazione**.

## Cosa
- **workflows v0.1.7** (github @d419072): unica novità rispetto a v0.1.6 = fix `.cache()` serverless
  nel prep_sped incrementale ([[LL-029]]).
- Promote con `promote_to_gitlab.py --repo logistico-workflows --version v0.1.7` (snapshot da GitHub,
  commit `release v0.1.7` + tag nel working-copy GitLab). Push su `main` → CI `validate` + `deploy_dev -t dev`.
- `lib` (v1.0.5) e `infrastructure` (v0.1.6) **invariati** → non ripubblicati. `documentation` non va su GitLab.

## CI GitLab (repo workflows) — cosa scatena il push
- Auth = **Managed Identity** (`ARM_USE_MSI`), **identità unica** → un solo set `[dev <mi>] logistica_*`.
- `deploy_dev` su `CI_COMMIT_BRANCH == main`; `deploy_prod` solo su **tag** + step **manuale** → un push su
  `main` **non** tocca prod.

## Verifica anti-duplicazione (metodo)
1. GitLab: pipeline `validate` + `deploy_dev` **verdi**.
2. Databricks (infra): `jobs list` → **esattamente 7** `[dev <mi>] logistica_*`, uno per nome.
3. **Test definitivo**: ri-lanciare il deploy → restano **7 job con gli stessi job_id** (update in-place).
   7→7 = nessuna duplicazione; 7→14 = problema.
4. Terraform infra: apply passa senza `duplicate job name detected`.

## Prossimi passi
- Dopo push: eseguire la verifica sopra con l'infra.
- Se OK: chiudere la parte "flusso CI stabilito" ([[OP-INF-3]]).
- Ri-split + push `documentation` su GitHub per allineare i doc (questo worklog + runbook16).
