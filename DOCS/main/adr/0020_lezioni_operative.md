# ADR-0020 — Lezioni operative: tracciamento cumulativo e scala di maturità

**Status**: accepted (2026-08-21)

**Contesto**:

Le attività di questi giorni hanno prodotto scoperte trasferibili che oggi sono **sepolte dentro gli ACT**:
il criterio "delta costante vs delta correlato al conteggio" è in `ACT_9015`, la trappola del `fstrim` che
riporta 0 B è in `ACT_MNT-01`, il fatto che un `docker exec` troncato lasci vivo il processo che tiene il lock
Derby è ancora in `ACT_9015`.

Il problema non è che non siano documentate: è che sono **indicizzate per attività, mentre chi ne ha bisogno
cerca per sintomo**. Un collega che domani vede `fstrim: 0 B` non ha alcun modo di risalire a quella riga —
dovrebbe già sapere quale ACT aprire. La conoscenza esiste e non è raggiungibile: equivale a non averla.

Tre vincoli aggiuntivi che scartano le soluzioni ovvie:

1. **Merge.** Un `LESSONS.md` unico è una macchina da conflitti git: più persone che accodano nello stesso
   giorno collidono sistematicamente. Le esperienze del team devono potersi sovrapporre senza attrito.
2. **Layer condiviso.** Le memorie personali degli assistenti (`~/.claude/.../memory/`) sono **per-persona**:
   ciò che sta lì al team non arriva. Il layer condiviso è e resta il repo.
3. **Decadimento.** Una sezione alimentata per buona volontà è vuota dopo tre sprint.

Precedente interno che orienta la decisione: il disallineamento dei workflow ([[ADR-0019]]) non è diventato una
nota da ricordare, è diventato `tests/test_workflows_alignment.py` — 30 test che nessuno deve ricordarsi di
leggere. Quella è la forma finale di una lezione, quando è raggiungibile.

**Alternative considerate**:

- **Un unico `LESSONS.md` in coda al repo** — semplice ma genera conflitti a ogni contributo parallelo e cresce
  fino a non essere più letto. Scartata sul vincolo 1.
- **Wiki / Confluence esterno** — comodo da scrivere, ma esce dal repo: si disallinea dal codice, non è
  versionato con esso e non è caricabile come contesto dagli assistenti del team. Scartata.
- **Solo memorie personali degli assistenti** — già in uso e utile, ma non condivisibile (vincolo 2).
  Resta come layer individuale, non sostituisce nulla.
- **Lasciare le lezioni negli ACT e affidarsi alla ricerca full-text** — è lo stato attuale: funziona solo se
  conosci già il termine esatto usato da chi ha scritto. Scartata.

**Decisione**:

**Le lezioni operative diventano un artefatto autonomo, indicizzato per sintomo, con una scala di maturità
obbligatoria per i difetti sui dati.**

1. **Un file per lezione** in `DOCS/main/lessons/`, con frontmatter (`id`, `sintomi`, `tag`, `autore`, `data`,
   `origine`, `stadio`). File separati = merge senza conflitti.
2. **Indice generato, non scritto**: `scripts/lessons/lessons_index.py` ricostruisce `lessons/INDEX.md` dal
   frontmatter. Si rigenera, non si edita — così nemmeno l'indice genera conflitti. Stessa logica del DAG
   derivato dal codice ([[ADR-0019]]).
3. **Indicizzazione per sintomo**: il campo `sintomi` contiene le stringhe con cui il problema **si presenta**
   (messaggi d'errore, valori anomali), non il nome dell'attività.
4. **Scala di maturità**: `lezione` → `regola documentata` → `guardrail automatico`.
   **Vincolante** per le lezioni nate da un difetto sui dati: non si chiude l'attività finché la lezione non è
   un check DQ o un test. **Facoltativa** per le lezioni operative di ambiente (Docker, WSL, tooling), dove
   l'automazione non è sensata e la prosa è la forma corretta.
5. **Alimentazione obbligatoria**: il template ACT acquisisce una sezione "Lezioni" e la Definition of Done la
   voce *"lezioni estratte in `lessons/`, oppure dichiarato esplicitamente che non ce ne sono"*.
6. **Sovrapposizione, non sovrascrittura**: chi trova una conferma o una contraddizione **non riscrive** il file
   di un altro, aggiunge un blocco `## Conferme e contraddizioni` con data, autore e contesto. Il consolidamento
   (fusione dei duplicati, promozione delle ricorrenti) avviene a fine wave insieme al SAL degli sprint.
7. **Consumo**: ogni work-order di ACT linka in apertura le lezioni pertinenti, come già fa con ADR e OP.
   Secondo aggancio previsto ma **non ancora attivo**: un `CLAUDE.md` di repo che punti a `lessons/INDEX.md`,
   così ogni sessione assistita del team carichi l'indice come contesto. Oggi quel file **non esiste** e la sua
   introduzione va decisa a parte, perché influisce su tutte le sessioni del team → follow-up.

**Conseguenze**:

- *Positive*: la conoscenza diventa raggiungibile dal sintomo, cioè nel momento in cui serve. I contributi di
  più persone si accumulano senza attrito di merge. La scala di maturità impedisce l'accumulo di prosa che
  nessuno rilegge, e trasforma i difetti trovati in controlli che non richiedono memoria umana.
- *Negative*: gli ACT che nascono da difetti sui dati si allungano, perché la chiusura richiede anche il check
  automatico. È il costo accettato: un difetto che passa i controlli — come `F_CARICO` con 13/13 check DQ verdi
  e due misure di business interamente NULL (OP-CAR-6) — costa molto di più quando lo si scopre in produzione.
- *Rischio residuo*: il consolidamento periodico è l'unico passo che resta manuale e quindi il primo a saltare.
  Va agganciato a un evento già esistente (il SAL di fine wave), non a un promemoria a sé stante.
- La directory nasce **popolata** con le lezioni già maturate (migrazione da ACT_MNT-01, ACT_9005, ACT_9014,
  ACT_9015 e dalle memorie personali di valore condiviso): una cartella vuota non viene adottata.

**Riferimenti**:
- [[ADR-0019]] — orchestrazione: DAG derivato dal codice (precedente della logica "genera, non mantenere")
- `DOCS/main/lessons/README.md` — convenzioni, template, uso del generatore
- `DOCS/main/acts/README.md` — sezione "Lezioni" nel template e nella Definition of Done
- `DOCS/main/05_open_points.md` — OP-CAR-6 (caso che motiva la scala vincolante sui difetti dati)
