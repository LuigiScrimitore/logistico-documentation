---
data: 2026-10-22
titolo: "Resilienza landing snapshot: i job landing/dim_refresh non falliscono più se manca il giorno (ACT_9034)"
autore: Francesco Foconi
push_monorepo: "main @333b57e"
push_github: "lib @8973385, workflows @c90e99c, documentation @63e8713"
push_gitlab: "lib v1.0.8, workflows v0.1.19 (push solo main, no tag - LL-031); deploy_dev success"
act: [ACT_9034]
adr: []
lesson: [LL-021]
op: []
---

## Incident
Run schedulate del 22/10: `logistica_landing_ingestion` e `logistica_dim_refresh` **FAILED**. Task KO:
5 bronze anagrafiche (`s_logistix`, `wl1_mag_sito_storico`, `apvpunto_vendita`, `buoni_eco`, `tipo_attivita`)
+ `gold_lu_from_cdtdw`. Errore reale: `[PATH_NOT_FOUND] .../cdt-estr-raw-landing/<tab>/2026/10/22/*.csv`.

## Causa (doppia)
1. **Dato**: l'estrazione odi3 del 22 ha consegnato transazionali e parte delle anagrafiche, ma NON quelle 5
   sorgenti + i lookup `cdtdw-landing` (consegna parziale, lato relay).
2. **Codice**: su serverless `PATH_NOT_FOUND` è una `pyspark.errors...AnalysisException` che **non eredita** da
   `pyspark.sql.utils.AnalysisException` (quella importata) → il `try/except` non la cattura → task KO invece di
   `NO_DATA`. Gap di [[LL-021]]: la fix 2026-09-01 copriva i carichi, non queste anagrafiche.

## Fatto
- Helper SSOT `resolve_landing_snapshot_path` in `lib/logistica_utils/utils.py`: verifica col `fs.ls` quale
  giorno esiste **prima** della `spark.read` e, per gli snapshot FULL, retrocede all'ultimo disponibile entro 7 gg
  (fallback = "stato corrente"). Agganciato ai 6 notebook. Unit test verde.
- Wheel ricompilato + ricaricato sul Volume `_wheels` (backup del precedente). Rilascio monorepo → GitHub →
  GitLab (lib v1.0.8, workflows v0.1.19, solo main). `deploy_dev` (MI) success; helper verificato sul notebook MI.
- **Re-run 22/10 = SUCCESS** per entrambi i job (landing run 389330436923961, dim_refresh run 426194327104925);
  i 6 task prima KO ora verdi via fallback al 21/10.

## Indicazioni al team
- Da oggi un **giorno di mancata consegna** di anagrafiche/lookup **non fa più fallire** la pipeline: usa
  l'ultimo snapshot (≤7 gg). Oltre 7 gg torna a fallire di proposito (per far emergere un outage reale).
- Il fallback è **solo** per snapshot FULL (anagrafiche/lookup). Transazionali/SNAPSHOT giacenze **non** lo usano.
- **Aperto (odi3)**: capire perché l'estrazione anagrafiche/lookup del 22 non ha consegnato (relay, fuori ambiente).
- Follow-up: estendere la robustezza (uscita `NO_DATA` senza fallback) anche ai bronze transazionali che oggi
  usano ancora il `try/except AnalysisException` stretto (latente, non emerso perché i loro file arrivano).
