# Lezioni operative — indice

> ⚠️ **File generato.** Non modificare a mano: rigenerare con
> `python scripts/lessons/lessons_index.py`. Convenzioni in [README](README.md),
> decisione in [ADR-0020](../adr/0020_lezioni_operative.md).

**18 lezioni.** Stadio: 🟡 lezione · 🔵 regola documentata · 🟢 guardrail automatico

## Cerca per sintomo

Parti da qui: il sintomo e' come il problema si presenta, non il nome dell'attivita'.

| Sintomo | Lezione |
|---|---|
| `Binary file (standard input) matches su un log di testo` | [LL-003](LL-003_docker-exec-troncato-lock-derby.md) |
| `bundle validate passa ma bundle deploy fallisce alla creazione dei job (400)` | [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md) |
| `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` | [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) |
| `colonne bronze popolate con i valori di un'altra colonna` | [LL-008](LL-008_csv-bronze-schema-per-nome.md) |
| `compact vdisk completato ma il file resta della stessa dimensione` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `conteggi corretti ma contenuti spostati di una posizione` | [LL-008](LL-008_csv-bronze-schema-per-nome.md) |
| `databricks bundle validate non vede il job / dopo il deploy il job non c'è` | [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) |
| `docker system df: RECLAIMABLE 0B ma il disco C: è pieno` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `Error: No value for required variable (ma la variabile CI esiste)` | [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) |
| `errori tipo '<tool> has no command named sh/-c' all'avvio del job` | [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) |
| `fstrim: 0 B (0 bytes) trimmed` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `il build fallisce con 'unexpected EOF while looking for matching quote' nel sed della versione` | [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) |
| `il DAG del workflow non riflette le dipendenze reali di lettura/scrittura` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `il job GitLab non esegue lo script: parte l'entrypoint dell'immagine` | [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) |
| `il job YAML ha name:/schedule:/tasks: a livello top-level (nessun resources:)` | [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) |
| `il processo sembra bloccato ma non lo è` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `il rilancio di un notebook fallisce subito dopo un tentativo interrotto` | [LL-003](LL-003_docker-exec-troncato-lock-derby.md) |
| `il runner ha un tag (es. azure-runner) e i job del .gitlab-ci.yml non ne hanno` | [LL-011](LL-011_pipeline-stuck-runner-taggato.md) |
| `il vacuum gira da 20+ minuti senza variazione dello spazio libero` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `INVALID_PARAMETER_VALUE: refers to an undefined job parameter 'X` | [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md) |
| `l'identità legge le risorse (data source) ma non può crearle` | [LL-018](LL-018_auth-ok-non-significa-autorizzato.md) |
| `l'upload/chiamata verso l'host aziendale (GitLab/Nexus/Databricks) fallisce in TLS` | [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) |
| `la copia manuale dei repo si porta dietro __pycache__/artefatti di build` | [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) |
| `la landing conserva un solo snapshot per una tabella giornaliera` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
| `la pipeline gira sul tag v1.0.2 ma il wheel pubblicato è 1.0.0` | [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) |
| `la pipeline resta Pending con l'etichetta 'stuck` | [LL-011](LL-011_pipeline-stuck-runner-taggato.md) |
| `la seconda release fallisce il publish per versione duplicata (409)` | [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) |
| `la storia di sviluppo (branch, WIP) è finita sul repo consegnato al cliente` | [LL-009](LL-009_due-host-git-una-direzione.md) |
| `lo split copre solo alcune cartelle e il resto sparisce senza avviso` | [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) |
| `lo stesso job scarica bene da PyPI/Docker Hub ma fallisce sul solo host interno` | [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) |
| `lo stesso progetto vive su due remote (es. GitHub e GitLab) con ruoli diversi` | [LL-009](LL-009_due-host-git-una-direzione.md) |
| `nel log si vedono solo messaggi JVM di Delta, nessun avanzamento Python` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `nel Package Registry il pacchetto ha una versione diversa dal tag che l'ha pubblicato` | [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) |
| `nessun duplicato sulla chiave ma i totali non tornano` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `non è chiaro quale host sia la verità: modifiche divergenti tra i due remote` | [LL-009](LL-009_due-host-git-una-direzione.md) |
| `notebook presenti nel repo ma non orchestrati da alcun job` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `notebook_path in un workflow punta a un notebook inesistente` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `partizione con colonna di partizione NULL e DWH_UPDATED_AT vecchio` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `PERMISSION_DENIED / does not have <privilegio> su un catalog/schema Unity Catalog` | [LL-018](LL-018_auth-ok-non-significa-autorizzato.md) |
| `quadratura KO su tutte le chiavi sito×giorno` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `quadratura: una colonna di delta è esattamente 100,0% su ogni sito e ogni data` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `Settings > CI/CD > Runners mostra un runner attivo (pallino verde) ma i job non partono` | [LL-011](LL-011_pipeline-stuck-runner-taggato.md) |
| `silver ha una sola data mentre il fact gold ne ha diverse` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
| `terraform chiede interattivamente una var che hai impostato come variabile CI` | [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) |
| `Terraform has no command named \"sh\". Did you mean \"push\"?` | [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) |
| `terraform init/plan passano ma apply fallisce con 'User does not have CREATE SCHEMA` | [LL-018](LL-018_auth-ok-non-significa-autorizzato.md) |
| `un .env o un dato reale è finito in un repo condiviso/consegnato` | [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) |
| `un file del monorepo non compare in nessun repo derivato dopo lo split` | [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) |
| `un file in include: non produce alcuna risorsa nel bundle` | [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) |
| `un task usa {{job.parameters.X}} ma il job non dichiara X in parameters` | [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md) |
| `una misura aggregata è inspiegabilmente gonfiata rispetto alla sorgente` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `una misura di business è NULL su tutte le righe del fact` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `una modifica fatta sul repo cliente non si ritrova a monte` | [LL-009](LL-009_due-host-git-una-direzione.md) |
| `una partizione storica non ha più sorgente a monte in nessun livello` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
| `una variabile CI/CD sembra ignorata solo in alcune pipeline` | [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) |
| `Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient` | [LL-003](LL-003_docker-exec-troncato-lock-derby.md) |
| `valori numerici finiti in una colonna di testo (o viceversa) senza errore` | [LL-008](LL-008_csv-bronze-schema-per-nome.md) |

## Tutte le lezioni

| ID | Titolo | Stadio | Tag | Origine | Data |
|---|---|---|---|---|---|
| [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) | Il compact del vhdx recupera solo ciò che il TRIM ha scartato | 🔵 regola | `docker`, `wsl`, `disco`, `ambiente-locale` | ACT_MNT-01 | 2026-08-21 |
| [LL-002](LL-002_vacuum-per-database-unbuffered.md) | VACUUM del warehouse per-database e con output unbuffered | 🔵 regola | `delta`, `vacuum`, `spark`, `ambiente-locale`, `docker` | ACT_MNT-01, ACT_9005 | 2026-08-21 |
| [LL-003](LL-003_docker-exec-troncato-lock-derby.md) | Un docker exec troncato lascia vivo il processo, che tiene il lock del metastore | 🔵 regola | `docker`, `spark`, `derby`, `metastore`, `ambiente-locale`, `logging` | ACT_9015 | 2026-08-21 |
| [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) | Il dynamic partition overwrite non tocca le partizioni che il flusso non produce più | 🟡 lezione ⚠️ da automatizzare | `delta`, `partizionamento`, `idempotenza`, `gold`, `dati` | ACT_9005, ACT_9015 | 2026-08-21 |
| [LL-005](LL-005_delta-costante-accusa-colonna.md) | Un delta costante accusa una colonna, un delta correlato al conteggio accusa la copertura | 🟢 guardrail | `quadratura`, `dq`, `gold`, `dati`, `diagnostica` | ACT_9015 | 2026-08-21 |
| [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) | La storia di un fact snapshot non è backfillabile — verificarlo prima di rigenerare | 🟡 lezione ⚠️ da automatizzare | `snapshot`, `partizionamento`, `gold`, `backfill`, `dati` | ACT_9015 | 2026-08-21 |
| [LL-007](LL-007_dag-derivato-dal-codice.md) | Un DAG mantenuto a mano divergerà dal codice — derivarlo e presidiarlo con un test | 🟢 guardrail | `orchestrazione`, `workflow`, `databricks`, `guardrail`, `manutenibilita` | ACT_9014, ADR-0019 | 2026-08-21 |
| [LL-008](LL-008_csv-bronze-schema-per-nome.md) | Sui CSV di landing lo schema si applica per nome, mai per posizione | 🔵 regola ⚠️ da automatizzare | `bronze`, `csv`, `landing`, `schema`, `dati` | memoria di progetto bronze-csv-schema-by-name | 2026-08-21 |
| [LL-009](LL-009_due-host-git-una-direzione.md) | Due host git con ruoli diversi vogliono una direzione sola (e release per snapshot) | 🔵 regola | `git`, `multi-repo`, `migrazione`, `governance`, `rilascio` | ACT_9011, ACT_9017, ADR-0016 | 2026-08-22 |
| [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) | Uno split/proiezione parte dai file tracciati e segnala i non mappati — mai drop silenziosi | 🔵 regola ⚠️ da automatizzare | `git`, `multi-repo`, `migrazione`, `tooling`, `sicurezza` | ACT_9017, ADR-0016 | 2026-08-22 |
| [LL-011](LL-011_pipeline-stuck-runner-taggato.md) | Pipeline "stuck" con un runner attivo presente → è il tag, non il runner | 🔵 regola | `gitlab`, `ci-cd`, `runner`, `ambiente-cliente` | ACT_9017 | 2026-08-22 |
| [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) | CERTIFICATE_VERIFY_FAILED in un job container verso un host aziendale → manca la CA interna nel container | 🔵 regola ⚠️ da automatizzare | `ci-cd`, `tls`, `certificati`, `container`, `ambiente-cliente` | ACT_9017 | 2026-08-22 |
| [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) | La versione del pacchetto viene da setup.py, non dal tag git — vanno sincronizzati | 🔵 regola ⚠️ da automatizzare | `ci-cd`, `packaging`, `python`, `wheel`, `release` | ACT_9017 | 2026-08-22 |
| [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) | Immagine CI con ENTRYPOINT non-shell (terraform, kaniko…) → resettare entrypoint in GitLab | 🔵 regola ⚠️ da automatizzare | `gitlab`, `ci-cd`, `docker`, `terraform` | ACT_0.1.6, ACT_9017 | 2026-08-22 |
| [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) | I file inclusi da un Databricks Asset Bundle devono essere `resources:`, non un job "nudo | 🔵 regola | `databricks`, `dab`, `ci-cd`, `orchestrazione` | ACT_9018, ADR-0021 | 2026-08-22 |
| [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) | Una variabile CI "Protected" è assente sui ref non protetti — il job non la vede | 🔵 regola | `gitlab`, `ci-cd`, `variabili`, `terraform` | ACT_0.1.6 | 2026-08-27 |
| [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md) | I riferimenti `{{job.parameters.X}}` vanno dichiarati nel job — validate non lo verifica, jobs/create sì | 🟢 guardrail | `databricks`, `dab`, `ci-cd`, `orchestrazione` | ACT_9018 | 2026-08-27 |
| [LL-018](LL-018_auth-ok-non-significa-autorizzato.md) | Autenticazione riuscita ≠ autorizzato — con MSI/SP i grant sul data-plane sono separati | 🔵 regola | `azure`, `databricks`, `unity-catalog`, `terraform`, `permessi`, `ambiente-cliente` | ACT_0.1.6 | 2026-08-27 |

## Debito di automazione

Lezioni nate da difetti sui dati che **devono** diventare un check DQ o un test (ADR-0020, scala vincolante):

- [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) — Il dynamic partition overwrite non tocca le partizioni che il flusso non produce più
- [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) — La storia di un fact snapshot non è backfillabile — verificarlo prima di rigenerare
- [LL-008](LL-008_csv-bronze-schema-per-nome.md) — Sui CSV di landing lo schema si applica per nome, mai per posizione
- [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md) — Uno split/proiezione parte dai file tracciati e segnala i non mappati — mai drop silenziosi
- [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) — CERTIFICATE_VERIFY_FAILED in un job container verso un host aziendale → manca la CA interna nel container
- [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) — La versione del pacchetto viene da setup.py, non dal tag git — vanno sincronizzati
- [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) — Immagine CI con ENTRYPOINT non-shell (terraform, kaniko…) → resettare entrypoint in GitLab

## Per tag

- **`ambiente-cliente`**: [LL-011](LL-011_pipeline-stuck-runner-taggato.md) · [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) · [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`ambiente-locale`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) · [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`azure`**: [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`backfill`**: [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`bronze`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`certificati`**: [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md)
- **`ci-cd`**: [LL-011](LL-011_pipeline-stuck-runner-taggato.md) · [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md) · [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md) · [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) · [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) · [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) · [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md)
- **`container`**: [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md)
- **`csv`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`dab`**: [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) · [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md)
- **`databricks`**: [LL-007](LL-007_dag-derivato-dal-codice.md) · [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) · [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md) · [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`dati`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-005](LL-005_delta-costante-accusa-colonna.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) · [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`delta`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md)
- **`derby`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`diagnostica`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`disco`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md)
- **`docker`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) · [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md) · [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md)
- **`dq`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`git`**: [LL-009](LL-009_due-host-git-una-direzione.md) · [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md)
- **`gitlab`**: [LL-011](LL-011_pipeline-stuck-runner-taggato.md) · [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) · [LL-016](LL-016_gitlab-protected-var-ref-protetto.md)
- **`gold`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-005](LL-005_delta-costante-accusa-colonna.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`governance`**: [LL-009](LL-009_due-host-git-una-direzione.md)
- **`guardrail`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`idempotenza`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md)
- **`landing`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`logging`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`manutenibilita`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`metastore`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`migrazione`**: [LL-009](LL-009_due-host-git-una-direzione.md) · [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md)
- **`multi-repo`**: [LL-009](LL-009_due-host-git-una-direzione.md) · [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md)
- **`orchestrazione`**: [LL-007](LL-007_dag-derivato-dal-codice.md) · [LL-015](LL-015_dab-file-inclusi-resources-jobs.md) · [LL-017](LL-017_dab-job-parameters-referenziati-non-dichiarati.md)
- **`packaging`**: [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md)
- **`partizionamento`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`permessi`**: [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`python`**: [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md)
- **`quadratura`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`release`**: [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md)
- **`rilascio`**: [LL-009](LL-009_due-host-git-una-direzione.md)
- **`runner`**: [LL-011](LL-011_pipeline-stuck-runner-taggato.md)
- **`schema`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`sicurezza`**: [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md)
- **`snapshot`**: [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`spark`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`terraform`**: [LL-014](LL-014_gitlab-ci-image-entrypoint-non-shell.md) · [LL-016](LL-016_gitlab-protected-var-ref-protetto.md) · [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`tls`**: [LL-012](LL-012_certificate-verify-failed-ca-aziendale-container.md)
- **`tooling`**: [LL-010](LL-010_split-da-file-tracciati-niente-drop-silenziosi.md)
- **`unity-catalog`**: [LL-018](LL-018_auth-ok-non-significa-autorizzato.md)
- **`vacuum`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md)
- **`variabili`**: [LL-016](LL-016_gitlab-protected-var-ref-protetto.md)
- **`wheel`**: [LL-013](LL-013_versione-wheel-dal-tag-non-da-setup.md)
- **`workflow`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`wsl`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md)

