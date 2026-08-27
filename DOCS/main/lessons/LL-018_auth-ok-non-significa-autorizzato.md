---
id: LL-018
titolo: Autenticazione riuscita ≠ autorizzato — con MSI/SP i grant sul data-plane sono separati
sintomi:
  - "terraform init/plan passano ma apply fallisce con 'User does not have CREATE SCHEMA'"
  - "l'identità legge le risorse (data source) ma non può crearle"
  - "PERMISSION_DENIED / does not have <privilegio> su un catalog/schema Unity Catalog"
tag: [azure, databricks, unity-catalog, terraform, permessi, ambiente-cliente]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-27
origine: [ACT_0.1.6]
---

## Sintomo
Con Managed Identity / service principal, `terraform init` e `plan` passano (l'identità **legge** i catalog via
data source), ma `apply` fallisce alla creazione:
`cannot create schema: User does not have CREATE SCHEMA on Catalog 'bronze_dev'` (su tutti i catalog).

## Strada sbagliata
Concludere "l'auth non funziona" o cercare il problema nelle credenziali. L'**autenticazione funziona**: la MI
si è autenticata e ha letto. Quello che manca è l'**autorizzazione** (i grant Unity Catalog), che è un piano
del tutto separato.

## Regola
Distinguere **authN** (chi sei) da **authZ** (cosa puoi fare). Su Unity Catalog i privilegi (`USE CATALOG`,
`CREATE SCHEMA`, `CREATE VOLUME`, `MODIFY`…) vanno **concessi esplicitamente** al principal (SP/MI), a parte
dall'auth. Prima di un `apply` che crea oggetti, verificare che l'identità abbia i grant di *create* sui target:
```sql
GRANT USE CATALOG, CREATE SCHEMA ON CATALOG <cat> TO `<application-id-della-MI>`;
```
Diagnosi rapida: se `plan`/read passano ma `create`/`apply` danno PERMISSION_DENIED, è authZ, non authN — la
richiesta va al team che governa i grant (qui: Reply/piattaforma), non toccando codice o credenziali.

## Perché
`plan` fa quasi solo letture (data source + refresh): basta `USE CATALOG`/read. `apply` **scrive**: servono i
privilegi di create. Un'identità appena creata (o una MI) spesso ha di default solo lettura. È la stessa
distinzione authN/authZ di ogni sistema: aver ottenuto un token non implica avere i permessi sull'oggetto.

## Conferme e contraddizioni
- 2026-08-27 · luigi.scrimitore · `logistico-infrastructure` apply DEV: MSI autenticata (0 risorse toccate),
  ma `CREATE SCHEMA` mancante su tutti i 5 catalog → richiesti i grant alla MI (SP `54d17490-…`) a Reply.
  Fallimento pulito (0 create) → stato invariato, si ri-applica dopo il grant.
