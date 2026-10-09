---
data: 2026-10-09
titolo: "Pausa degli schedule dei 7 job dev del logistico + fix durevole negli YAML (LL-037)"
autore: Francesco Foconi
push_monorepo: "PR #22 (worklog + LL-037 + 7 YAML workflows)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "workflows: rilascio su main (no tag) → deploy_dev"
act: []
adr: []
lesson: [LL-037]
op: []
---

## Contesto
Inventario di ciò che è schedulato su Databricks per il logistico: **7 job**, tutti
`[dev id_dev_dataplatform_workload_00] logistica_*` (owner = Managed Identity, deployati dalla CI),
con schedule **attivo (UNPAUSED)**. Nessun'altra risorsa schedulata: nessuna pipeline DLT, nessun job con tag
logistico sotto altro nome; i job canonici di prod creati per errore ([[LL-031]]) non esistono più.

| Job | Cron (Europe/Rome) | Esito ultime 4 notti (06→09/10) |
|---|---|---|
| landing_ingestion | 00:30 | FAILED ×4 |
| dim_refresh | 01:00 | FAILED ×4 |
| carichi | 02:00 | SUCCESS ×4 |
| giacenze | 03:30 | SUCCESS ×4 |
| prep_sped | 04:30 | SUCCESS ×4 |
| trasporti | 05:00 | FAILED ×4 |
| datamart | 06:00 | SUCCESS ×4 |

I job girano con `run_date` = data di esecuzione, ma per i giorni nuovi la landing del Volume non ha file
(la landing ora va su `logisticolanding` via relay, [[ACT_OP-INF-4]]). Risultato: consumo di compute,
3 job falliscono ogni notte e `email_alert` manda un avviso a Luigi.

## Perché `mode: development` non li metteva in pausa
DAB in development mette in pausa gli schedule **solo se lo YAML non dichiara `pause_status`**. I 7 file
`workflows/logistica_*.yml` hanno `pause_status: UNPAUSED` esplicito, quindi il deploy dev li lascia attivi.

## Cosa
1. **Pausa immediata** degli schedule dei 7 job via API (`jobs update`, `pause_status: PAUSED`, cron e timezone
   invariati). È reversibile e i job restano lanciabili a mano.
2. **Fix durevole** ([[LL-037]]): la pausa manuale non bastava, perché il prossimo `deploy_dev` (o un deploy da
   sandbox personale) riapplica gli YAML con `UNPAUSED`. Tolto `pause_status: UNPAUSED` dallo `schedule` dei 7
   file `workflows/logistica_*.yml` (al suo posto un commento). Così:
   - **dev** (`mode: development`) → il bundle mette in pausa gli schedule da solo, a qualunque deploy;
   - **prod** (`mode: production`) → schedule attivo come previsto (scrivere `PAUSED` a mano avrebbe fermato anche prod).
3. **Rilascio**: merge PR #22 → split → GitHub `logistico-workflows` → GitLab `logistico-workflows` (push solo
   `main`, nessun tag, [[LL-031]]) → `deploy_dev` della CI applica la nuova config ai 7 job.

## Verifica
- Pausa manuale: `jobs get` sui 7 job → `pause_status: PAUSED`, cron invariati. Nessun run logistico attivo.
- Fix, prima del rilascio: `bundle validate -o json`. Prima del fix `-t dev` risolveva **UNPAUSED** su tutti e 7;
  dopo il fix `-t dev` risolve **PAUSED** su tutti e 7 e `-t prod` resta **UNPAUSED**. Il warning di validate
  sui permessi della cartella sandbox personale c'era già prima, non è legato al fix.
- Dopo il deploy: i 7 job devono restare **PAUSED**, con gli **stessi job_id** (update in place, nessun duplicato).

## Prossimi passi
1. Rilascio su GitLab (serve la VPN per raggiungere `cp1lgitlab`) e verifica post-deploy.
2. Riattivare lo scheduling in dev solo se serve, e dopo il cutover `landing_mode=external` (i job leggeranno
   `logisticolanding`): per farlo si usa `presets.trigger_pause_status` sul target, non lo YAML del job.
