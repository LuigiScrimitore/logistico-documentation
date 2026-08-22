# Lezioni operative — indice

> ⚠️ **File generato.** Non modificare a mano: rigenerare con
> `python scripts/lessons/lessons_index.py`. Convenzioni in [README](README.md),
> decisione in [ADR-0020](../adr/0020_lezioni_operative.md).

**8 lezioni.** Stadio: 🟡 lezione · 🔵 regola documentata · 🟢 guardrail automatico

## Cerca per sintomo

Parti da qui: il sintomo e' come il problema si presenta, non il nome dell'attivita'.

| Sintomo | Lezione |
|---|---|
| `Binary file (standard input) matches su un log di testo` | [LL-003](LL-003_docker-exec-troncato-lock-derby.md) |
| `colonne bronze popolate con i valori di un'altra colonna` | [LL-008](LL-008_csv-bronze-schema-per-nome.md) |
| `compact vdisk completato ma il file resta della stessa dimensione` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `conteggi corretti ma contenuti spostati di una posizione` | [LL-008](LL-008_csv-bronze-schema-per-nome.md) |
| `docker system df: RECLAIMABLE 0B ma il disco C: è pieno` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `fstrim: 0 B (0 bytes) trimmed` | [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) |
| `il DAG del workflow non riflette le dipendenze reali di lettura/scrittura` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `il processo sembra bloccato ma non lo è` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `il rilancio di un notebook fallisce subito dopo un tentativo interrotto` | [LL-003](LL-003_docker-exec-troncato-lock-derby.md) |
| `il vacuum gira da 20+ minuti senza variazione dello spazio libero` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `la landing conserva un solo snapshot per una tabella giornaliera` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
| `nel log si vedono solo messaggi JVM di Delta, nessun avanzamento Python` | [LL-002](LL-002_vacuum-per-database-unbuffered.md) |
| `nessun duplicato sulla chiave ma i totali non tornano` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `notebook presenti nel repo ma non orchestrati da alcun job` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `notebook_path in un workflow punta a un notebook inesistente` | [LL-007](LL-007_dag-derivato-dal-codice.md) |
| `partizione con colonna di partizione NULL e DWH_UPDATED_AT vecchio` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `quadratura KO su tutte le chiavi sito×giorno` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `quadratura: una colonna di delta è esattamente 100,0% su ogni sito e ogni data` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `silver ha una sola data mentre il fact gold ne ha diverse` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
| `una misura aggregata è inspiegabilmente gonfiata rispetto alla sorgente` | [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) |
| `una misura di business è NULL su tutte le righe del fact` | [LL-005](LL-005_delta-costante-accusa-colonna.md) |
| `una partizione storica non ha più sorgente a monte in nessun livello` | [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) |
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

## Debito di automazione

Lezioni nate da difetti sui dati che **devono** diventare un check DQ o un test (ADR-0020, scala vincolante):

- [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) — Il dynamic partition overwrite non tocca le partizioni che il flusso non produce più
- [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) — La storia di un fact snapshot non è backfillabile — verificarlo prima di rigenerare
- [LL-008](LL-008_csv-bronze-schema-per-nome.md) — Sui CSV di landing lo schema si applica per nome, mai per posizione

## Per tag

- **`ambiente-locale`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) · [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`backfill`**: [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`bronze`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`csv`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`databricks`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`dati`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-005](LL-005_delta-costante-accusa-colonna.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md) · [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`delta`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md)
- **`derby`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`diagnostica`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`disco`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md)
- **`docker`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md) · [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`dq`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`gold`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-005](LL-005_delta-costante-accusa-colonna.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`guardrail`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`idempotenza`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md)
- **`landing`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`logging`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`manutenibilita`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`metastore`**: [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`orchestrazione`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`partizionamento`**: [LL-004](LL-004_partizioni-stale-dynamic-overwrite.md) · [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`quadratura`**: [LL-005](LL-005_delta-costante-accusa-colonna.md)
- **`schema`**: [LL-008](LL-008_csv-bronze-schema-per-nome.md)
- **`snapshot`**: [LL-006](LL-006_fact-snapshot-storia-non-backfillabile.md)
- **`spark`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md) · [LL-003](LL-003_docker-exec-troncato-lock-derby.md)
- **`vacuum`**: [LL-002](LL-002_vacuum-per-database-unbuffered.md)
- **`workflow`**: [LL-007](LL-007_dag-derivato-dal-codice.md)
- **`wsl`**: [LL-001](LL-001_compact-vhdx-dipende-dal-trim.md)

