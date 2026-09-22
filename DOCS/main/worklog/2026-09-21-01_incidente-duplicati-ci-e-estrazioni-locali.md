---
data: 2026-09-21
titolo: "Incidente job duplicati CI (LL-030) + merge fix LL-029 su main (PR #10) + estrazioni locali 10→21"
autore: Francesco Foconi
push_monorepo: "PR #10 (main @95651b2) + doc-pass (LL-030, OP-INF-3, worklog)"
push_documentation: "n/d"
push_gitlab: "— (freeze attivo)"
act: []
adr: []
lesson: [LL-030, LL-029]
op: [OP-INF-3]
---

## Cosa e' stato fatto

### 1) Incidente job duplicati Databricks (segnalato dall'infra) → [[LL-030]]
- **Sintomo**: Terraform infra in errore, `duplicate job name detected: [dev id_dev_dataplatform_workload_00] logistica_*` (il `data "databricks_jobs" "all"` va in conflitto con due job stesso nome).
- **Diagnosi** (confermata da git): i duplicati sono della **service principal della CI**, non delle sandbox personali (queste hanno nomi unici e non collidono). Causa reale = **cambio storico del `root_path`** (commit 2026-08-27 e 2026-09-02, [[LL-023]]): lo stato del bundle si e' spostato → il deploy CI successivo ha **ricreato** i job invece di aggiornarli → 2 copie per i 7 workflow.
- **Fix immediato**: l'infra ha ripulito i doppioni (una istanza per nome); noi abbiamo rimosso le sandbox personali (`bundle destroy --target dev`) a scopo pulizia (non erano la causa). Root_path **gia' stabile** dal 2026-09-02 → nessuna ricorrenza attesa.
- **Prevenzione** ([[OP-INF-3]] aggiornato): il naming `[dev <identità>]` è lo **standard di piattaforma** e va **mantenuto** (nomi canonici/`mode:production` **scartati**). La stabilità è già garantita da **root_path stabile** (non ri-cambiarlo) + **redeploy pulito** → deploy successivi in-place, niente duplicati. Da chiarire con Luigi l'auth CI (SP unica vs per-utente).

### 2) Fix LL-029 (.cache serverless) portata su GitHub `main`
- La fix `.cache()` ([[LL-029]]) era solo in locale: committata su branch `fix/ll-029-serverless-cache`, **PR #10 mergiata su `main`** (`95651b2`). Ora `main` e' il piu' aggiornato lato codice; Luigi puo' allinearsi via pull.

### 3) Estrazioni locali giornaliere 10→21 (dataset dev, NO cloud)
- Seed **solo locale** (`-KeepStage -NoCopy -NoArchive`, `--ignore-odi-flag`): giorno 10 (`landing_day10_bak`); 11→20 in `landing_local_1119` (11 full + 12→19 TX con **riferimenti replicati dal 11**, ottimizzazione cdtdw una-volta); 20 e 21 **full** ("normalmente"). Nessun push sul Volume.
- Non e' l'ingestion di produzione (quella sara' il job Databricks/AzCopy dal landing reale): e' il **simulatore** per tenere fresco il dataset locale.

## Doc aggiornati
- `lessons/LL-030_...md` (nuova) + INDEX rigenerato.
- `05_open_points.md`: **OP-INF-3** esteso con l'incidente + direzione `dev_ci` + freeze GitLab.
- Questo worklog + INDEX.

## Stato / prossimi passi — INDICAZIONI TEAM
1. **Merge PR #10 fatto** → Luigi puo' pullare `main` (prende la fix `.cache()`).
2. **Redeploy pulito** dei job DEV (lato CI/SP) quando si stabilisce il flusso — ora nascerebbero gia' con la fix.
3. **Naming = standard** `[dev <identità>]` mantenuto; stabilità = root_path stabile + redeploy pulito (no `dev_ci`/nomi canonici). Resta da chiarire con Luigi l'auth CI (SP unica vs per-utente).
4. **Freeze push GitLab** attivo finche' il flusso CI non e' stabilito.
