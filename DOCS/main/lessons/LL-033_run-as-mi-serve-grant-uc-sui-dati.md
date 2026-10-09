---
id: LL-033
titolo: I job DAB girano come la MI (run_as=owner) — la MI deve avere i grant UC sui dati, non basta il grant al gruppo utenti
sintomi:
  - "[UNAUTHORIZED_ACCESS] PERMISSION_DENIED: User does not have SELECT on Table 'bronze_dev.logistica.<t>'. SQLSTATE: 42501"
  - "i job deployati dalla CI/MI falliscono in run mentre gli stessi job [dev <utente>] giravano verdi"
tag: [databricks, unity-catalog, permessi, mi, service-principal, run-as, ci]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-23
origine: [run-11-22-cloud, LL-018, OP-INF-1]
---

## Sintomo
Lanciando i job `[dev id_dev_dataplatform_workload_00] logistica_*` (deployati dalla CI/MI), il primo task
fallisce con `PERMISSION_DENIED: User does not have SELECT on Table 'bronze_dev.logistica.<tabella>'`.
Gli **stessi** flussi, sui job `[dev flabffoconi]`, giravano **verdi**.

## Perche' (non ovvio)
- I job DAB hanno `run_as` **vuoto** → girano come il loro **owner/creator**, cioe' la **MI**
  (`id_dev_dataplatform_workload_00`), non come chi li lancia (CAN_MANAGE dà il diritto di **avviare**, non
  cambia l'identita' di esecuzione).
- I run verdi precedenti erano su job `[dev flabffoconi]` → giravano **come flabffoconi**, che ha i grant UC
  sui dati (via `Group-Engineering-dev`, OP-INF-1/2).
- La **MI** invece **non ha i grant UC** su `bronze_dev`/`silver_dev`/`gold_dev`/… → i suoi run falliscono.
  È authN ≠ authZ ([[LL-018]]): la MI puo' **deployare** (crea i job) ma non **leggere/scrivere** le tabelle.

## Regola
Se i job condivisi girano come la **MI** (modello dev via CI, [[ADR-0027]]), la MI deve avere i **grant UC
data-plane** sui cataloghi dev, non solo il gruppo utenti. Due modi:
1. **Grant diretti alla MI**: `USE CATALOG` + `USE SCHEMA` + `SELECT` + `MODIFY` (+ `CREATE` dove scrive)
   su `bronze_dev`, `silver_dev`, `gold_dev`, `config_dev` (schemi `logistica`/`condiviso`) e read sul Volume
   `landing_dev` — via Terraform (come OP-INF-1 per il gruppo). **Consigliato** (la MI è l'identita' runtime).
2. **Aggiungere la MI a `Group-Engineering-dev`** (se il gruppo ha gia' i grant): la MI eredita i permessi.
   Più semplice ma meno esplicito.
Alternativa sconsigliata: forzare `run_as` a un utente/gruppo nel `databricks.yml` (cambia il modello di
identita' runtime; un utente personale non è adatto ai run schedulati).

## Conferme e contraddizioni
- 2026-09-23 · run 11→22 sul cloud DEV (job MI): `landing_ingestion` KO su `SELECT bronze_dev.logistica.*`.
  `run_as={}` → owner = MI. Blocco: la MI non ha i grant UC. Richiesto intervento infra (grant alla MI o
  membership nel gruppo). Vale con [[LL-018]] (authN≠authZ) e OP-INF-1 (grant UC alla MI/gruppo).
