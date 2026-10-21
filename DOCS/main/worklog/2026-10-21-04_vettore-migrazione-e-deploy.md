---
data: 2026-10-21
titolo: "Rinomina vettore resa definitiva su dev: wheel ricaricato, schema migrato (rename, dati preservati), deploy_dev CI = success"
autore: Francesco Foconi
push_monorepo: "doc su main"
push_documentation: "split dopo"
push_gitlab: "workflows v0.1.17 main (deploy_dev success, nessun tag/prod — LL-031)"
act: [ACT_9031]
adr: [ADR-0028, ADR-0025]
lesson: []
op: [Q-01]
---

## Contesto
Fase senza utenti: rendere **definitiva e operativa** la rinomina CORRIERE→VETTORE ([[ADR-0028]]) così che da
domani i job Databricks e l'estrattore si possano rilanciare e funzioni tutto.

## Fatto (tutto verificato)
1. **Wheel**: ricompilato `logistica_utils-1.0.0` e **ricaricato sul Volume** `/Volumes/landing_dev/logistica/files/_wheels/` (overwrite).
2. **Migrazione schema dev** (tutta in RENAME, **dati preservati**, 0 drop di dati): abilitato `columnMapping`,
   `RENAME COLUMN CORRIERE_COD→VETTORE_COD` (+ `_NAT`) su 9 tabelle (f_carico, f_ordini, a_outbound_mensile,
   silver carico_testata/ordine/curated.carico/curated.ordini) e `RENAME TABLE` `lu_corriere→lu_vettore`,
   `dim_corriere→dim_vettore`. Verifica: **0 colonne CORRIERE_COD residue**, `lu_vettore`/`dim_vettore` presenti.
3. **Deploy codice**: split monorepo → GitLab `workflows v0.1.17` (**push solo main**, no tag per [[LL-031]]) →
   pipeline CI **6417**: `validate` + `deploy_dev` = **success**. Nessun `deploy_prod`.
4. **Estrattore**: non impattato (estrae la sorgente `vettori`, nome invariato; sorgenti Oracle intatte).

## Stato
Dev **completamente allineato a VETTORE** (codice deployato + schema migrato + wheel nuovo). Rilanciando i job
(o alla schedulazione dev) i dati vengono scritti come `VETTORE_COD`/`LU_VETTORE` senza doppie colonne.

## Follow-up (housekeeping, non bloccante)
- Sync dei 4 single-repo GitHub e del repo lib su GitLab (il monorepo è la fonte; si allineano al prossimo giro).
- **PROD**: stessa sequenza (wheel + migrazione rename + deploy) al go-live, quando si rilascia a prod.
- Report **MicroStrategy/RAC** fuori repo: riallineare a `LU_VETTORE`/`VETTORE_COD`.
