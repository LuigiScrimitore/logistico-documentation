---
id: LL-030
titolo: DAB dev-mode + CI — cambiare il root_path orfanizza i job della CI e crea duplicati che rompono Terraform
sintomi:
  - "Error: cannot read jobs: cannot read data jobs: duplicate job name detected: [dev <sp>] logistica_*"
  - "terraform data \"databricks_jobs\" \"all\" va in errore: due job con lo stesso nome esatto"
  - "dopo un cambio di root_path nel databricks.yml compaiono 2 copie per ogni job della CI"
tag: [databricks, dab, ci, terraform, duplicati, root_path, deploy]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-21
origine: [incidente-duplicati-ci, OP-INF-3]
---

## Sintomo
La pipeline Terraform dell'infra va in errore:
`duplicate job name detected: [dev id_dev_dataplatform_workload_00] logistica_landing_ingestion`
Il data source `data "databricks_jobs" "all"` costruisce una mappa **nome→id** di TUTTI i job del
workspace e fallisce se **due job hanno lo stesso nome esatto**.

## Perche' (non ovvio)
- I duplicati erano dei job della **service principal della CI** (`[dev <sp>] logistica_*`), **NON**
  delle sandbox personali: queste hanno nomi **unici** (`[dev flabffoconi]`, `[dev flablscrimitore]`)
  e **non collidono mai** tra loro. Deployare in tanti dalle sandbox **non** e' la causa.
- Causa reale: il **root_path** del target `dev` e' stato **cambiato** (commit del 2026-08-27 e
  2026-09-02, cfr. [[LL-023]]). In DAB lo **stato del bundle** vive sotto il root_path nel workspace.
  Cambiando il root_path, il deploy CI successivo (stessa SP) **non ritrova lo stato precedente** e
  **ricrea** i job invece di aggiornarli → 2 copie per ognuno dei 7 workflow.
- Con root_path **stabile** (stessa identita' → stesso path) i redeploy **aggiornano in-place**:
  nessun duplicato. Dal 2026-09-02 il path e' gia' stabile.

## Strada sbagliata
Ri-cambiare il root_path "per sistemare i duplicati" quando e' **gia' stabile**: e' proprio il
meccanismo che li genera → ri-orfanizza il set attuale e ne crea uno nuovo.

## Regola
- **Fix immediato** (serve admin / la SP): cancellare le **copie in eccesso** tenendone **una per
  nome**. Le sandbox personali non c'entrano e non vanno toccate per questo.
- **Root_path stabile per identita'**: gia' cosi' dal 2026-09-02, **non ri-cambiarlo**.
- **Naming = standard di piattaforma**: il prefisso `[dev <identità>]` (imposto da `mode: development`)
  è lo **standard dei nomi job della data platform** e va **MANTENUTO**. NON passare a `mode: production`
  / nomi senza prefisso: i nomi canonici sono **scartati**.
- **Prevenzione**: la causa era il **cambio di `root_path`**; ora è **stabile** (dal 2026-09-02) →
  **non ri-cambiarlo**. Con root_path stabile + un **redeploy pulito**, i deploy successivi aggiornano
  in-place → niente duplicati. **Nessun cambio di naming necessario.** (Se un domani servisse uno stato
  CI condiviso, si può fissare il `root_path` **mantenendo `mode: development`**, così i nomi restano
  lo standard `[dev …]`.)
- **Terraform**: `data "databricks_jobs" "all"` e' fragile — basta **un** nome duplicato ovunque nel
  workspace per bloccare l'apply. Valutare un lookup filtrato/mirato invece dell'enumerazione totale.

## Conferme e contraddizioni
- 2026-09-21 · Incidente risolto: l'infra ha ripulito i doppioni della SP; le sandbox personali
  (comprese le nostre) sono state rimosse a scopo pulizia (non erano la causa). Root_path già stabile
  → nessuna ricorrenza attesa **mantenendo il naming standard `[dev <identità>]`** (i nomi canonici
  senza prefisso sono scartati: standard di piattaforma). Vale insieme a [[LL-023]] (root_path in home
  per le sandbox) e ADR-0021/ADR-0022.
