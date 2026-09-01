---
id: LL-019
titolo: Applicare un tfplan salvato in CI richiede lo STESSO lock/provider del plan e uno stato non cambiato
sintomi:
  - "Error: Inconsistent dependency lock file — The given plan file was created with a different set of external dependency selections"
  - "Error: Saved plan is stale — the state was changed by another operation after the plan was created"
  - "l'apply in CI fallisce mentre lo stesso codice applicato a mano funziona"
tag: [gitlab, ci-cd, terraform, tfplan, lockfile, state]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-09-01
origine: [ACT_0.1.6]
---

## Sintomo
Il job `apply` (gate manuale) consuma un `tfplan` salvato dal job `plan` e fallisce con **due** errori insieme:
`Inconsistent dependency lock file` e `Saved plan is stale`.

## Strada sbagliata
Ri-cliccare l'`apply` sulla **stessa pipeline vecchia**, o rigenerare solo il piano: gli errori restano.

## Regola
Un `tfplan` salvato è applicabile **solo** nel contesto in cui è stato creato. In CI (plan e apply = job/workspace
separati) servono **due** condizioni:
1. **Stesso set di provider/lock.** Il job `apply` rifà `terraform init`: se `.terraform.lock.hcl` non è né
   committato né veicolato, ri-risolve i provider in modo indipendente → *inconsistent lock*. **Fix:** passare
   dal `plan` all'`apply` come artifact **`tfplan` + `.terraform.lock.hcl` + `.terraform/`** (`needs:[plan]`) e
   fare `init -lockfile=readonly`. (Il lock è gitignorato → va come artifact, non da git. In alternativa:
   committarlo generandolo per `-platform=linux_amd64`.)
2. **Stato invariato tra plan e apply.** Se lo stato cambia dopo il plan (un'altra sessione/operazione sullo
   stesso backend, o un plan successivo) il piano è **stale** *by design*. **Fix:** ri-lanciare l'**intera
   pipeline** (plan+apply nello stesso run) contro lo stato corrente; non applicare piani vecchi; nessuna
   operazione concorrente sullo stesso `key` di state.

Corollario: **pinnare l'immagine Terraform** (non `latest`): plan e apply devono girare con la stessa versione
del core, altrimenti il piano è incompatibile.

## Perché
`terraform apply <saved-plan>` verifica sia le *dependency selections* embeddate nel piano sia il *serial/lineage*
dello stato: entrambe le protezioni scattano se il piano non nasce dallo stesso contesto. È lo stesso spirito di
[[LL-018]] (authN≠authZ) e [[LL-016]]: l'ambiente CI va reso **esplicito e deterministico**, non dato per scontato.

## Conferme e contraddizioni
- 2026-09-01 · luigi.scrimitore · `logistico-infrastructure`: dopo lo sblocco del grant ([[OP-INF-1]]), l'`apply`
  è fallito con *inconsistent lock* + *stale plan* (piano applicato non coerente con stato/provider correnti; lock
  non veicolato al job apply). Fix nel generatore `split_to_multirepo.py`: artifact `tfplan`+lock+`.terraform` +
  `init -lockfile=readonly`; procedura: ri-lanciare la pipeline intera.
