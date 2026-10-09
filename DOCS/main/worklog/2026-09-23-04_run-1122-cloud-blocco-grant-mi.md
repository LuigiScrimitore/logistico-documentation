---
data: 2026-09-23
titolo: "Run 11→22 cloud DEV bloccato: la MI (run_as) non ha i grant UC sui dati (LL-033)"
autore: Francesco Foconi
push_monorepo: "PR doc (LL-033 + worklog)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: []
adr: []
lesson: [LL-033]
op: []
---

## Contesto
Portate tutte le estrazioni locali (11→22) sulla landing cloud (Volume ora ha 01→22). Obiettivo: girare il
flusso standard landing→bronze→silver→gold per i giorni 11→22 sui job DEV (ora visibili grazie a [[LL-032]]).

## Cosa è successo
- Permesso di **avvio** ok (CAN_MANAGE via Group-Engineering-dev): `run-now` restituisce run_id.
- Ma `landing_ingestion(2026-09-11)` **KO**: `PERMISSION_DENIED: User does not have SELECT on
  bronze_dev.logistica.apvpunto_vendita` (e a cascata sulle altre bronze).
- Causa ([[LL-033]]): i job hanno `run_as={}` → girano come la **MI** (owner `id_dev_dataplatform_workload_00`),
  che **non ha i grant UC sui dati**. I run verdi precedenti erano sui job `[dev flabffoconi]` (giravano come
  flabffoconi, che i grant li ha via gruppo). Batch **fermato** (tutti i giorni fallirebbero uguale).

## Blocco / azione richiesta (infra)
Grant UC alla **MI** sui cataloghi dev (`USE`/`SELECT`/`MODIFY`/`CREATE` su bronze_dev/silver_dev/gold_dev/
config_dev + read Volume landing_dev), **oppure** aggiungere la MI a `Group-Engineering-dev`. Via Terraform
(come OP-INF-1 per il gruppo). Finché non c'è, i job dev condivisi (run come MI) non eseguono.

## Prossimi passi
1. Infra: grant alla MI (o membership gruppo). 
2. Poi ri-lanciare il run 11→22 (script `run_1122.ps1` pronto, job_id mappati).
3. Verifica: `landing_ingestion` verde → catena fino a gold.
