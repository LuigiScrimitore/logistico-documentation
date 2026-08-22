---
id: LL-009
titolo: Due host git con ruoli diversi vogliono una direzione sola (e release per snapshot)
sintomi:
  - "lo stesso progetto vive su due remote (es. GitHub e GitLab) con ruoli diversi"
  - "non è chiaro quale host sia la verità: modifiche divergenti tra i due remote"
  - "la storia di sviluppo (branch, WIP) è finita sul repo consegnato al cliente"
  - "una modifica fatta sul repo cliente non si ritrova a monte"
tag: [git, multi-repo, migrazione, governance, rilascio]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9011, ACT_9017, ADR-0016]
---

## Sintomo
Lo stesso codice deve stare su **due host** con ruoli diversi — es. GitHub = sviluppo (tutte le evolutive),
GitLab cliente = rilascio (solo release stabili). Senza una regola esplicita nascono i sintomi: modifiche
divergenti sui due remote, dubbio su quale sia la verità, storia di sviluppo che tracima sul repo del cliente.

## Strada sbagliata
Tenere i due host **in mirror bidirezionale** o pushare liberamente su entrambi. Sembra comodo ("così sono
sempre allineati"), ma crea il **doppio source-of-truth**: due history che divergono e nessuno sa quale vince.
Il merge inverso (dal cliente verso di noi) è la trappola: prima o poi qualcuno committa di là e il flusso si
rompe.

## Regola
**Una direzione sola, e release per snapshot pulito.**
- Il flusso è **mono-direzionale**: monorepo → GitHub (SoT sviluppo) → GitLab cliente (rilascio). Mai inverso.
- Sul cliente arrivano **solo release testate/stabili**, come **snapshot puliti taggati** (`vX.Y.Z`), non la
  storia di sviluppo: init pulito, un commit di release per volta.
- Ciò che non deve uscire dal proprio perimetro (es. la documentazione interna) **non si pusha** sull'host
  esterno — è una regola, non una cortesia.
Procedura concreta e script in `16_runbook_multirepo_github_gitlab.md` + `scripts/promote_to_gitlab.py`;
decisione in [ADR-0016](../adr/0016_multi_repo_gitlab.md).

## Perché
La direzione unica elimina la domanda "chi ha ragione?": la verità è a monte, il resto è derivato. Lo snapshot
di release (invece del push della history) tiene il repo esterno **leggibile come sequenza di rilasci** e non
espone il rumore dello sviluppo; ed è coerente con l'init pulito deciso in ADR-0016. È lo stesso principio di
[[LL-010]] (proiezione deterministica, niente stati impliciti) applicato al *quando* invece che al *cosa*.

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · scelto il modello A (snapshot di release) su B (dual-remote con push della
  history) proprio per non portare la storia di sviluppo sul GitLab cliente.
