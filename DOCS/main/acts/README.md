# acts/ · Documenti delle attività (ACT) — Logistico 2.0

Ogni attività di progetto ha qui il suo file **ACT**, che ne è la **Single Source of Truth**:
chi lo prende in mano deve trovarci **tutto e solo** ciò che serve (contesto, obiettivo, come
farla, come verificarla), senza dover leggere altri file.

> Indice di tutte le ACT (e ADR) → [`../15_backlog_master.md`](../15_backlog_master.md).
> Decisioni architetturali → [`../adr/`](../adr/). Ciclo di vita e processo → questo README.

---

## Convenzione di naming

`ACT_<codice>_<slug>.md` — dove `<codice>` dipende dall'origine dell'attività:

| Origine | Codice | Esempio file |
|---------|--------|--------------|
| **Sprint** (`sprint_agile/`) | codice sprint `N.N.N` | `ACT_5.3.1_gold-f-ordini.md` |
| **Backlog** non-sprint | codice backlog (`I-01`, `D-01`, `V-01`, `Q-01`, `G-01`, `RS01`…) | `ACT_Q-01_quadratura-f-carico.md` |
| **Open point** non-sprint | `OP-NN` | `ACT_OP-CAR-1_val-costo-carico.md` |
| **Emergente** (nato in corso d'opera: bug, DQ, nuovo sviluppo…) | progressivo **da 9000** | `ACT_9000_fix-bom-notebook.md` |
| **Gate di fase** (deploy+run+cert in cloud, chiude una fase) | `GATE-N` (per FASE N) · `GATE-PROD` (go-live) | `ACT_GATE-2_deploy-run-cert-cloud-fase-2.md` |

`<slug>`: breve, kebab-case, italiano o inglese. **Append-only**: un codice non si riusa mai
(neanche se l'attività è cancellata). Gli emergenti proseguono 9000, 9001, 9002, …

---

## Profondità a due livelli

Per non appesantire attività già chiuse, due formati:

- **ACT "record"** — per attività **✅ done**: compilare solo `Status/Type/Origin/Sprint/Closed`,
  `Contesto` (perché serviva, 1-3 righe), `Obiettivo` (1 riga) ed `Esito` (cosa consegnato + commit).
  Le altre sezioni si possono omettere. È un **registro storico** ma resta comprensibile da solo.
- **ACT "work-order"** — per attività **aperte / in corso / future**: template **completo**. Sono
  quelle che qualcuno prenderà in mano → serve tutto il contesto per lavorare in autonomia.

Quando un'attività passa da aperta a done, si può "sgonfiare" al formato record mantenendo l'Esito.

---

## Template completo (work-order)

```markdown
# ACT_<codice> · Titolo breve e imperativo

**Status**: proposed | in-progress | on-hold | done | cancelled | superseded by ACT_<codice>
**Type**: feature | fix | dq | doc | infra | analysis
**Origin**: sprint N.N | backlog <codice> | OP-NN | emerged
**Sprint**: N.N  ·  (oppure) **fuori-sprint**: backlog | open-point | emergente
**Fase / Wave**: FASE N — Wave X (es. FASE 2 — Wave A Carichi)
**Gg (stima)**: —
**Blocco**: nessuno | cloud/PROD | infra (Azure/GitLab) | Reply (anagrafiche/OP-02) | altro
**Created**: YYYY-MM-DD   **Closed**: —   **Owner**: (opzionale)
**Dipende da**: ACT_… / —      **Blocca**: ACT_… / —
**ADR collegate**: ADR-NNNN / —      **OP collegati**: OP-NN / —

## Contesto e motivazione
Perché serve? Cosa risolve? Su cosa impatta?

## Obiettivo
Cosa deve essere vero alla fine. Criterio di "fatto" verificabile.

## Analisi tecnica
Come si fa. Componenti impattati, decisioni chiave, alternative se rilevanti.
Sorgenti/tabelle/notebook coinvolti. Riferimenti al codice esistente.

## Sviluppo (diario)
- YYYY-MM-DD · nota

## Verifica
Come confermiamo che è fatta (acceptance/smoke-test, quadratura, DQ…).

## Esito
Cosa è stato consegnato. Commit di riferimento.

## Lezioni
Scoperte **trasferibili** emerse durante l'attività, estratte in `DOCS/main/lessons/` (ADR-0020).
Se non ce ne sono, scriverlo esplicitamente: il silenzio non si distingue dalla dimenticanza.
- LL-NNN — titolo  ·  (oppure) nessuna lezione trasferibile

## Follow-up
Nuove ACT emerse (con codice 9000+). ADR emerse. Nessuna se non applicabile.
```

## Template compatto (record — attività già done)

```markdown
# ACT_<codice> · Titolo

**Status**: done   **Type**: …   **Origin**: sprint N.N | backlog … | OP-NN
**Sprint**: N.N   **Fase / Wave**: …   **Closed**: YYYY-MM-DD
**ADR collegate**: —   **OP collegati**: —

## Contesto
Perché serviva (1-3 righe). Rimandi a ADR/sprint/altre ACT se utile.

## Obiettivo
1 riga.

## Esito
Cosa consegnato + commit/riferimenti.
```

---

## Definition of Done di fase (done offline → done reale in cloud)

Gran parte delle attività è **completata offline** (codice validato in locale). Una fase **non è chiusa**
finché il suo pacchetto non è in cloud e certificato. Criterio unico, valido per tutte le fasi:

> **Una fase è chiusa (done reale) solo quando:**
> 1. **Deploy** — il pacchetto della fase è deployato in **Azure Databricks TEST** (dev) via DAB;
> 2. **Run schedulato stabile** — i workflow girano **a schedule** per ≥ N run consecutivi **senza errori né
>    rilanci manuali** (N proposto = 5; soglia da confermare, OP-24);
> 3. **Qualità** — DQ verdi ad ogni run (orphan-rate 0.0%, Silver/Gold 0 FAIL);
> 4. **Dati certificati** — quadratura vs CDT_DW entro soglia (1%) per i fact della fase, o divergenze
>    **deliberate e documentate**.
> 5. **Lezioni capitalizzate** — le scoperte trasferibili della fase sono in `DOCS/main/lessons/`, e
>    quelle nate da un **difetto sui dati** sono diventate un check DQ o un test, non solo prosa
>    (ADR-0020, scala di maturità vincolante).

Questo criterio **non** si ripete in ogni ACT: è tracciato una volta da una **ACT gate** per fase
(`ACT_GATE-N`), che è l'**ultima attività** di quella fase. Il go-live in **produzione** dell'intero
pacchetto è il capstone `ACT_GATE-PROD` (rimanda alle ACT 8.x). Finché la `GATE-N` non è `done`, la fase
resta "done offline" anche se tutte le sue attività di sviluppo lo sono.

---

## Ciclo di vita

`proposed` → `in-progress` → `done` (o `on-hold` / `cancelled` / `superseded`).

**L'attività si svolge sull'ACT** (è la sua SSOT). **Al completamento di una ACT** si aggiornano, nell'ordine:
1. il file ACT (`Status=done`, `Closed`, `Esito`, `Follow-up`);
2. il **backlog master** (`../15_backlog_master.md`);
3. il **file sprint corrispondente** in `../sprint_agile/sprint_N.N.md` (vista **SAL/portfolio**: tabella
   attività, %/stato di fase, note di sprint) — se l'attività appartiene a uno sprint;
4. i **documenti globali** impattati (piano `04`, architettura `01`, pipeline `02`, open points `05`,
   certificazione `07`, milestone `milestones/fase_N`, ecc.);
5. eventuali **ADR** se è emersa una decisione architetturale; eventuali **ACT 9000+** se sono emerse
   nuove attività.
6. al **push su `main`**, la **voce worklog** del push ([`../worklog/`](../worklog/), [[ADR-0024]]): scaffold con
   `python scripts/worklog/new_entry.py --slug <slug> --title "<titolo>"`, si completa in 8-12 righe, poi
   `python scripts/worklog/worklog_index.py`. È il layer di **comunicazione al team** ("cosa è cambiato con
   questo push, dove siamo").

> **Sprint vs ACT**: i file in `sprint_agile/` restano la **vista SAL** (avanzamento settimanale, stato di
> fase); l'ACT è la **SSOT del dettaglio** della singola attività. Il dettaglio operativo si aggiorna
> sull'ACT, lo **stato** si riflette poi sullo sprint.

---

## Regola d'oro

Il file ACT è **la SSOT** per quell'attività. Se due ACT condividono informazioni, si **duplicano**
in entrambi i file — nessuna "attesa di lettura incrociata". Chi lavora su un tema legge e aggiorna
**solo** il file di quel tema.
