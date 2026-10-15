---
data: 2026-10-15
titolo: "Schedulazione dev nel bundle: catena 07:00-08:30, landing da logisticolanding, attiva solo nel deploy della CI"
autore: Francesco Foconi
push_monorepo: "PR dedicata (branch feat/cutover-passo2-orchestratore)"
push_documentation: "split dopo merge"
push_gitlab: "workflows: rilascio solo main, nessun tag (LL-031)"
act: [ACT_OP-INF-4]
adr: [ADR-0003]
lesson: [LL-037]
op: [OP-INF-4]
---

## Contesto
Il test del 15/10 (worklog 2026-10-14-01) ha dato **7/7 job SUCCESS** con la catena schedulata su Databricks dalle 07:00
alle 08:30 e la landing letta da `logisticolanding`. Quella configurazione era stata messa **a mano via API**: il prossimo
`deploy_dev` l'avrebbe annullata (job in pausa, percorso Volume, orari notturni). Va portata nel bundle.

Il trigger "File arrival" con orchestratore (piano del 14/10) resta un'evoluzione possibile: per ora si torna agli
**orari fissi, come prima**, su richiesta dell'utente.

## Decisioni
1. **Orari** (Europe/Rome), dopo l'arrivo della landing alle ~06:13 (job ODI delle 06:00):
   `landing_ingestion` 07:00 · `dim_refresh` 07:15 · `carichi` 07:30 · `giacenze` 07:45 · `trasporti` 08:00 ·
   `prep_sped` 08:15 · `datamart` 08:30. Il job più lungo del test dura 8,5 minuti: 15 minuti di distanza bastano.
   Dopo le 02:00 la `run_date` di default (`{{job.start_time.iso_date}}`, in UTC) coincide con il giorno italiano.
2. **`landing_base_path` dev** = `abfss://logisticolanding@stdevdataplatformweudata.dfs.core.windows.net`
   (cutover validato il 14/10). Prod invariato.
3. **Schedule attivi solo nel deploy della CI.** Nuova variabile del bundle `schedule_pause_status`:
   - default `PAUSED` → i deploy delle sandbox personali (`[dev <utente>]`) restano in pausa;
   - CI GitLab `deploy_dev` passa `--var="schedule_pause_status=UNPAUSED"` → i job della Managed Identity
     (`[dev id_dev_dataplatform_workload_00]`) girano;
   - target `prod` = `PAUSED` **fino al go-live**: prod non è ancora in uso, così un deploy in prod fatto per errore
     non fa partire niente. Al go-live si porta a `UNPAUSED` (una riga in `databricks.yml`).

   Aggiorna la regola di [[LL-037]]: il `pause_status` ora si dichiara, ma tramite variabile decisa per deploy, non
   scritto fisso nello YAML.
4. **Mail di errore**: `luigi.scrimitore@aperion.it` e `francesco.foconi@quanticx.com` su tutti e 7 i job.

## Passi
1. Doc (questo worklog, [[LL-037]], [[ACT_OP-INF-4]]).
2. `databricks.yml` (variabile, `landing_base_path` dev) + 7 YAML dei job (cron, `pause_status`, mail) + CI del repo
   `workflows` in `split_to_multirepo.py`.
3. `bundle validate`: dev → PAUSED, dev con la variabile → UNPAUSED, prod → PAUSED.
4. PR + merge, split su GitHub, rilascio `workflows` su GitLab (solo main) → la CI fa il deploy.
5. Verifica sui job dev della Managed Identity: orari, UNPAUSED, percorso, mail.

## Esito
_(in corso)_
