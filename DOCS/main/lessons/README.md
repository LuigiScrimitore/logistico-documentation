# Lezioni operative — convenzioni

Registro cumulativo delle scoperte trasferibili del team. Formalizzato in [ADR-0020](../adr/0020_lezioni_operative.md).

## A cosa serve (e a cosa no)

| Artefatto | Risponde a |
|---|---|
| **ACT** | *cosa ho fatto* — attività, esito, numeri |
| **ADR** | *cosa ho deciso* — scelta architetturale e alternative |
| **OP** | *cosa resta aperto* — punto da chiarire o decidere |
| **LESSON** | *cosa ho imparato che vale anche fuori da qui* |

Una lezione entra qui se supera questa prova: **un collega che incontra il sintomo domani, senza sapere nulla
della mia attività, trova questo file?** Se la risposta è no, sta nel posto sbagliato.

Non sono lezioni: il racconto di un'attività (→ ACT), una decisione di progetto (→ ADR), un dubbio irrisolto
(→ OP), la documentazione di una procedura completa (→ `DOCS/guide_dev/`).

## Naming e frontmatter

`LL-<NNN>_<slug-kebab-case>.md` — numerazione progressiva, mai riusata.

```yaml
---
id: LL-001
titolo: Il compact del vhdx recupera solo ciò che il TRIM ha scartato
sintomi:                      # come il problema SI PRESENTA: messaggi, valori anomali
  - "fstrim: 0 B (0 bytes) trimmed"
  - "compact vdisk completato ma il file resta della stessa dimensione"
tag: [docker, wsl, disco, ambiente-locale]
stadio: regola-documentata    # lezione | regola-documentata | guardrail-automatico
automatizzabile: false        # true -> lo stadio DEVE arrivare a guardrail-automatico
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_MNT-01]         # dove è stata pagata
---
```

**Il campo `sintomi` è quello che conta.** Va scritto con le stringhe con cui il problema si manifesta, non con
il nome dell'attività: chi cerca parte dall'errore che ha davanti. Copiare i messaggi letterali.

## Struttura del corpo

```markdown
## Sintomo
Cosa vedi. Messaggi ed evidenze letterali.

## Strada sbagliata
Il percorso che qualcuno ha già fatto a vuoto, e perché sembrava giusto.
Questa sezione è il vero risparmio di tempo: si salta un errore già pagato.

## Regola
Cosa fare, in forma azionabile. Comandi se pertinenti.

## Perché
Il meccanismo. Senza questo la regola diventa cargo cult e non si sa quando non vale.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · caso in cui la regola non è valsa: ...
```

## Scala di maturità

`lezione` → `regola-documentata` → `guardrail-automatico`

Una lezione automatizzabile **deve** diventare un test o un check DQ: la prosa è il ripiego per ciò che non si
sa ancora automatizzare. Quando diventa guardrail, il file resta come traccia del *perché* quel controllo
esiste, con il link al test.

- **Vincolante** per le lezioni nate da un difetto sui dati (`automatizzabile: true`): l'attività non si chiude
  prima del check.
- **Facoltativa** per le lezioni operative di ambiente (Docker, WSL, tooling), dove automatizzare non ha senso.

Precedente: il disallineamento dei workflow non è rimasto una nota, è diventato
`tests/test_workflows_alignment.py` ([ADR-0019](../adr/0019_orchestrazione_dag_derivato.md)).

## Indice

`INDEX.md` è **generato**, non scritto a mano:

```bash
python scripts/lessons/lessons_index.py            # rigenera
python scripts/lessons/lessons_index.py --check    # exit 1 se stale (per CI/pre-commit)
```

Si rigenera dopo ogni aggiunta — così non produce conflitti git. Non modificarlo a mano: le modifiche
verrebbero sovrascritte.

⚠️ **Non lanciarlo con `docker exec logistico-spark`**: in quel container `/workspace/code` è montato
**read-only** e lo script fallisce con `OSError: [Errno 30] Read-only file system`. Eseguirlo dall'host, oppure
con un mount scrivibile:

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v /c/PROGETTI/LOGISTICO:/repo logistico-spark:1.0 \
  python /repo/scripts/lessons/lessons_index.py
```

Nessuna dipendenza esterna (il frontmatter è letto da un parser minimo interno), quindi gira anche senza
`pyyaml`.

## Contributi in parallelo

Un file per lezione: due persone che imparano cose diverse toccano file diversi e git non rileva conflitti.

Se trovi una **conferma o una contraddizione** a una lezione altrui, non riscrivere il suo file: aggiungi una
riga in `## Conferme e contraddizioni` con data, autore e contesto. Una regola smentita da un caso nuovo è
informazione preziosa, non un errore da cancellare.

Il **consolidamento** (fusione dei duplicati, promozione delle ricorrenti a guardrail o a `guide_dev/`) avviene
a fine wave, insieme al SAL degli sprint.
