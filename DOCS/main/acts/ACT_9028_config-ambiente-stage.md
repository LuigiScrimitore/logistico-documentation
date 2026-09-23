# ACT_9028 · Configurare l'ambiente `stage` (pre-produzione osservata)

**Status**: proposed
**Type**: infra
**Origin**: OP-INF-3 (emerged da ADR-0027)
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: trasversale (piattaforma / ambienti)
**Gg (stima)**: —
**Blocco**: infra (Azure/Terraform + Unity Catalog) — richiede apply su `infrastructure`
**Created**: 2026-09-23   **Closed**: —   **Owner**: team (infra + workflows)
**Dipende da**: ADR-0027 (modello 4 ambienti), ADR-0004 (naming catalog `_stage`)
**Blocca**: promozione dei flussi in pre-produzione (F_CARICO e successivi)
**ADR collegate**: [[ADR-0027]], [[ADR-0004]], [[ADR-0022]], [[ADR-0021]]   **OP collegati**: OP-INF-3

## Contesto e motivazione
ADR-0027 formalizza il modello a **4 ambienti** (sandbox → dev → stage → prod). Oggi esistono solo `_dev` e
`_prod`: l'ambiente **`stage`** è previsto ([[ADR-0004]], D4: "`_stage` previsto ma non configurato") ma **non
esiste**. Senza stage non c'è una **pre-produzione** dove un flusso, una volta verde e quadrato, giri per N
giorni sotto monitoraggio + `dq_gate` prima di essere promosso in prod. Questa ACT lo configura end-to-end.

## Obiettivo
Rendere `stage` un ambiente deployabile e schedulabile: catalog/schemi/Volume/grant `_stage` + target DAB
`stage` con naming `[stage]` + regola CI di promozione **dev→stage**.

## Come farla

### 1) Infra Terraform (`infrastructure`) — catalog `_stage`
- Replicare per l'ambiente `stage` ciò che esiste per `dev`: catalog di layer `landing_stage`, `bronze_stage`,
  `silver_stage`, `gold_stage`, `config_stage` (schema `logistica`/`condiviso` come da ADR-0004), **Volume**
  `landing_stage.logistica.files`, e i **grant** al gruppo writer + reader (analoghi a `Group-Engineering-dev`).
- Parametrizzare l'ambiente (variabile `env`/suffisso) invece di duplicare i moduli, se il codice lo consente.
- Applicare via CI **Managed Identity** (ADR-0022): `plan` → gate manuale `apply`. Nuova release `infrastructure`.

### 2) Target DAB `stage` (`databricks.yml`)
- Aggiungere il target `stage` accanto a `dev`/`prod`:
  - `mode: production` (schedule **attivi**, semantica di rilascio — non `mode:development`);
  - `presets.name_prefix: "[stage] "` → job **`[stage] logistica_*`** (distinti da dev `[dev <identità>]` e
    prod canonico → nessuna collisione, [[LL-030]]);
  - `root_path` stabile per lo stage (coerente con la topologia workspace scelta, vedi Punti aperti);
  - `variables`: `env: stage`, `landing_base_path: /Volumes/landing_stage/logistica/files`,
    `retail_master_schema: bronze_stage.condiviso`; `presets.tags.env: stage`.
- Validare: `databricks bundle validate --target stage` (verificare in particolare che `name_prefix` sia
  applicato sotto `mode: production`).

### 3) CI GitLab — promozione dev→stage
- Aggiungere in `workflows` uno stage `deploy-stage` (`databricks bundle deploy --target stage`), triggerato
  su **promozione** (tag `stage-*` o branch dedicato, da definire), auth MI. `deploy_prod` resta su tag +
  gate manuale. Aggiornare il runbook multirepo (16) con il flusso dev→stage→prod.

### 4) Doc
- Aggiornare `10_piano_migrazione_databricks.md` (§ambienti/catalog), `14_release_kit.md` (gate go-live),
  `16_runbook_multirepo`. Chiudere/aggiornare **OP-INF-3**. Voce worklog al push.

## Come verificarla
- `infrastructure` apply `stage` verde (catalog + Volume + grant creati).
- `bundle validate --target stage` ok; `deploy --target stage` crea **7 job `[stage] logistica_*`**.
- Ri-deploy stage → **7→7** stessi job_id (update in-place, niente duplicati — test anti-[[LL-030]]).
- Un flusso (es. F_CARICO) gira in stage su `*_stage` con `dq_gate` verde.

## Punti aperti (da decidere prima/durante)
- **Topologia workspace**: dev/stage/prod nello **stesso** workspace UC (separazione via catalog + prefissi
  job) o **workspace distinti** (impatta `DATABRICKS_HOST_*` e la CI). Il naming regge in entrambi i casi.
- **Trigger di promozione** dev→stage: tag vs branch dedicato.
- **Auth**: MI unica anche per stage (atteso, coerente ADR-0022).

## Esito
- (da compilare all'esecuzione)
