# adr/ · Architecture Decision Records — Logistico 2.0

> **Append-only.** Ogni decisione strutturale/funzionale non banale ha una sua ADR con
> **contesto**, **alternative**, **scelta**, **conseguenze**. Se una decisione cambia, si scrive
> una **nuova** ADR che *supersedes* la precedente — non si riscrive quella vecchia.

> Indice di tutte le ADR (e ACT) → [`../15_backlog_master.md`](../15_backlog_master.md).
> Le attività che implementano una decisione stanno in [`../acts/`](../acts/) e la referenziano.

## Come funziona

- Ogni ADR è un file `NNNN_slug.md` in questa cartella, numerazione progressiva a **4 cifre**.
- Formato: contesto → alternative → decisione → conseguenze → stato.
- **Status**: `proposta` | `accepted` | `accepted (retroactive)` | `superseded by NNNN` | `deprecated`.
- **Retroattive**: molte decisioni del progetto sono già state prese e implementate ma non fissate
  come ADR (es. D1-D5 catalog, grain etichetta F_CARICO, OP-CAR-3, ammanco in pezzi, scope MTV
  trasporti, DQ interno, tuning-cloud-non-trasferibile). Si scrivono **retroattivamente** per fissare
  il *perché*: stesso formato, status `accepted (retroactive)`, con sezione "Riferimenti"
  (commit/file/OP/ACT) al posto del solo "Commit / link".
- **Collegamento con le ACT**: se una ADR nasce da un'attività, la ACT la cita in "ADR collegate" e
  la ADR cita la ACT nei "Riferimenti". Le decisioni sui **flussi/modellazione** sono interne al team;
  Reply entra solo su anagrafiche/setup/standard condivisi.

## Livello di dettaglio (driver)

Il **test** per capire se una ADR è abbastanza dettagliata: *"leggendo solo questa ADR, un membro del
team comprende il **problema** e la **decisione architetturale** che ne consegue, senza dover
approfondire altrove?"* Se restano zone grigie, aggiungere contesto. In particolare:
- il **Contesto** deve spiegare il problema, i vincoli e *perché conta* (non dare per scontato il dominio);
- le **Alternative** vanno con pro/contro reali (perché le altre sono state scartate);
- le **Conseguenze** includono impatti concreti (MSTR/quadratura/costi/manutenzione/futuro);
- i **Riferimenti** rimandano a **sezioni specifiche dei doc architetturali** (`01_architettura.md`,
  `02_pipeline_mapping.md`, `10_piano_migrazione_databricks.md`, `07_certifica_gold_vs_cdtdw.md`,
  `14_release_kit.md`) oltre a commit/file/OP/ACT.

## Template

```markdown
# ADR-NNNN · Titolo breve

**Status**: accepted (YYYY-MM-DD)  ·  (oppure) accepted (retroactive) / superseded by NNNN
**Contesto**:
    Quale problema/decisione? Che vincoli abbiamo?
**Alternative considerate**:
    1. Opzione A — pro/contro
    2. Opzione B — pro/contro
**Decisione**:
    Cosa abbiamo scelto e perché.
**Conseguenze**:
    Cosa cambia (positivo/negativo). Cosa comporta per il futuro. Impatti su MSTR/quadratura/costi.
**Riferimenti**: commit `abc1234` · file/notebook · OP-NN · ACT_<codice>
```

## Elenco ADR

| # | Titolo | Status | Data |
|---|--------|--------|------|
| [0001](0001_config_dev_control_catalog.md) | Catalog di controllo = `config_dev` (D1) | accepted (retroactive) | 2026-07-02 |
| [0002](0002_bronze_condiviso_lu.md) | Lookup master `LU_*` in `bronze.condiviso` (D2) | accepted (retroactive) | 2026-07-02 |
| [0003](0003_uc_volume_landing.md) | Landing su UC Volume managed (D3) | accepted (retroactive) | 2026-07-02 |
| [0004](0004_naming_ambienti_prod_stage.md) | Naming ambienti `_dev`/`_prod`/`_stage` (D4) | accepted | 2026-07-03 |
| [0005](0005_no_secret_oracle_export_landing.md) | No segreti Oracle: export su landing (D5) | accepted (retroactive) | 2026-07-02 |
| [0006](0006_grain_etichetta_f_carico.md) | Grain F_CARICO = etichetta, peso da anagrafica | accepted | 2026-07-02 |
| [0007](0007_standard_2_notebook.md) | Standard 2-notebook (curated vs gold) | accepted | 2026-06 |
| [0008](0008_chiavi_naturali_gold.md) | Gold usa chiavi naturali validate | accepted | 2026-06 |
| [0009](0009_job_cluster_serverless.md) | Compute = job cluster serverless | accepted | 2026-07-03 |
| [0010](0010_incrementale_watermark_pattern2_pruning.md) | Incrementale a 3 pilastri (watermark+pattern#2+pruning) | accepted | 2026-06 |
| [0011](0011_lad_via_cod_nat.md) | LAD generico via `<dim>_COD_NAT` | accepted | 2026-06-20 |
| [0012](0012_ammanco_in_pezzi.md) | Ammanco in pezzi (unità omogenea) | accepted | 2026-07-05 |
| [0013](0013_scope_trasporti_mtv.md) | F_TRASPORTO grana MTV (tratta/bolla future) | accepted | 2026-07-05 |
| [0014](0014_dq_alerting_interni.md) | DQ & alerting interni (non attendere cliente) | accepted | 2026-07-05 |
| [0015](0015_tuning_cloud_non_trasferibile.md) | Tuning locale non trasferibile al cloud | accepted | 2026-07-05 |
| [0016](0016_multi_repo_gitlab.md) | Codice GitLab multi-repo | accepted | 2026-07 |
| [0017](0017_rilascio_a_fasi.md) | Go-live a fasi (no big-bang) per DAG | accepted | 2026-07-05 |
| [0018](0018_reply_scope_governance.md) | Perimetro decisionale Reply (solo anagrafiche/setup/standard) | accepted | 2026-07-05 |
| [0019](0019_orchestrazione_dag_derivato.md) | Orchestrazione: DAG derivato dal codice | accepted | 2026-08-04 |
| [0020](0020_lezioni_operative.md) | Lezioni operative: tracciamento cumulativo + maturità | accepted | 2026-08-21 |
| [0021](0021_modello_deploy_dab_pipeline_per_area.md) | Modello deploy DAB = pipeline per-area | accepted | 2026-08-22 |
| [0022](0022_auth_ci_managed_identity.md) | Auth CI/CD via Managed Identity (no secret) | accepted | 2026-08-27 |
