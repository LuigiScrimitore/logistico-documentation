---
data: 2026-09-02
titolo: DQ finding carichi = watermark; fix partitionOverwriteMode (serverless) + prep massa critica
autore: Luigi Scrimitore
push_monorepo: 11e1b11
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0025]
lesson: [LL-020, LL-021]
op: []
---

## Cosa e' stato fatto
- **DQ finding di ieri diagnosticato**: `dq_gate` bloccava su `table_exists(F_CARICO)`. Root cause = **watermark
  incrementale**: `config_dev.etl.watermark` a 2026-09-01 (dal test lgcx); ri-seed dello **stesso run_date** ->
  `_bronze_load_date` identico -> filtro `> watermark` scarta tutto -> silver 6/4 righe (LGCX vecchie) -> F_CARICO
  vuoto. **Non e' qualita' dato**. Reset watermark -> silver reprocessa full (5897/546).
- **partitionOverwriteMode**: rimosso `spark.conf.set` (vietato su serverless Spark Connect) e iniettata
  `.option("partitionOverwriteMode","dynamic")` sul writer Delta nei **14 notebook**.
- **Prep massa critica**: aree trasporti/giacenze/prep_sped/aggregati con `%pip` + `dependencies: []`.
- **dq_gate**: messaggio corretto `config_<env>.etl.dq_results` (era `logistica_etl`). Gate messo in **standby**
  (i processi funzionali sono da rivedere).

## Novita'
- **Gate reale della campagna = copertura del SEED**: ogni flusso vuole le sue sorgenti in landing. Seedati solo
  **logistix+stat+cdtdw**; mancano **cnd** (giacenze t_stock, prep_sped), **cdt_estr** (trasporti/prep_sped), **track**
  (trasporti vettori/spedizioni — NON nei `--systems` dell'extractor, da chiarire) e alcune tabelle logistix (es. `imbfmovim`).
- `gold_f_carico` resta bloccato su `LU_CORRIERE` (viene da track/trasporti). Deciso: **niente masking** di tabelle
  assenti (tabella mancante = setup, non valore mancante) -> si costruiscono le tabelle, non si aggancia -1.

## Doc aggiornati
- Solo codice (14 nb partitionOverwriteMode + 4 workflow prep + dq_gate). Candidati LESSON: partitionOverwriteMode/
  RDD/cella-indentata (serverless), watermark+re-seed stesso run_date.

## Stato dopo il push / prossimi passi
- Carichi: catena bronze->silver->gold provata; F_CARICO si popola col reprocess ma serve `LU_CORRIERE` (trasporti).
- **Prossimo: SEED COMPLETO** (`-Systems logistix,stat,cnd,cdt_estr` + tabelle logistix mancanti; `track` da capire),
  poi run area-per-area a gold fixando i bug (partitionOverwriteMode gia' fatto; attesi altri come per carichi).
  `databricks.yml` root_path->home resta locale. Provisioning wheel = interim `%pip` ([[ADR-0025]]).
