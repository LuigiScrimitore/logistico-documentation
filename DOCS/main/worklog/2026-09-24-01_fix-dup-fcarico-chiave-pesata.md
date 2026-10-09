---
data: 2026-09-24
titolo: "Fix duplicati F_CARICO: chiave naturale pesata senza DATA_BOLLA (silver_pesate) — LL-034"
autore: Francesco Foconi
push_monorepo: "PR dedicata (silver_pesate.py + LL-034 + worklog + INDEX)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "da rilasciare (workflows) per applicare il fix al deploy dev"
act: []
adr: []
lesson: [LL-034]
op: [OP-CAR-3]
---

## Contesto
Run cloud 11→22 (job MI, env=dev): 6 job su 7 verdi tutti i giorni, **`carichi` KO tutti i 12 i giorni**
sul `dq_gate` (`unique_keys` BLOCKING su F_CARICO). Root cause isolata ([[LL-034]]): `silver_pesate`
deduplica/MERGE su chiave naturale **`(SITO_COD, ETICHET_NRO, DATA_BOLLA)`**; `DATA_BOLLA` è instabile
tra ri-estrazioni (finestra lookback, [[LL-024]]) → la stessa pesata viene inserita 2 volte → la catena
carichi (join su `BOLLA_NRO`, pesata guida il grain) va in **fan-out** → 3 righe duplicate su F_CARICO
202609 (0,0066%). Il `dq_gate` ha correttamente bloccato.

## Cosa
- `notebooks/silver/carichi/silver_pesate.py`: chiave naturale (Window dedup **+** condizione MERGE)
  da `(SITO_COD, ETICHET_NRO, DATA_BOLLA)` a **`(SITO_COD, CARICO_LOG_NRO, ETICHET_NRO)`**.
  `DATA_BOLLA` diventa attributo (si tiene l'ultimo snapshot via `_bronze_insert_ts` DESC).
  Verificato che `p.DATA_BOLLA` **non è usata** in `silver_prep_carico` → nessun impatto downstream.
- Doc: [[LL-034]] (chiave pesata senza DATA_BOLLA) + INDEX lezioni/worklog rigenerati.
- `dq_gate` **invariato** (calibrato bene: ha fatto il suo lavoro).

## Prossimi passi
1. Merge PR monorepo.
2. Rilascio `workflows` su GitLab (push **solo `main`**, no tag — [[LL-031]]) → `deploy_dev` applica il fix.
3. Cleanup one-time: run `silver_pesate` con **`full_refresh=true`** → ricostruisce silver.pesata pulita
   (97 righe di troppo → 0).
4. Ri-run `carichi` 11→22 → verifica `unique_keys` F_CARICO = 0 dup → job verde.

## Verifica (metodo)
- `SELECT ... FROM gold_dev.logistica.F_CARICO ... GROUP BY grana HAVING COUNT(*)>1` → 0 righe.
- `SELECT ... FROM silver_dev.logistica.pesata GROUP BY (SITO,CARICO_LOG_NRO,ETICHET_NRO) HAVING COUNT(*)>1` → 0.
- `config_dev.etl.dq_results`: F_CARICO `unique_keys` passed=true.

## Esito (2026-09-24) — RISOLTO
- Rollout: PR #17 mergiata → split → GitHub `workflows` @7a40690 → GitLab `workflows` **v0.1.9**
  (push **solo main, no tag** — [[LL-031]]) → **deploy_dev** applicato (notebook MI in dev aggiornato, verificato).
- Cleanup one-time: `silver_pesate` `full_refresh=true` → **silver.pesata pulita** (0 duplicati su
  `(SITO,CARICO_LOG_NRO,ETICHET_NRO)`, 155.521 righe).
- **Ri-run `carichi` 11→22: 12/12 SUCCESS** (il `dq_gate` passa: fallimento gate = job KO, quindi tutti verdi = gate ok).
- **F_CARICO 202609: 0 duplicati** (82.612 righe). Problema chiuso.
- Nota operativa: `jobs submit`/`run-now` con OVERWRITE sono bloccati dal classificatore auto-mode di
  Claude Code → cleanup e ri-run lanciati dall'utente in PowerShell (script **ASCII**, niente `&&` / `—` / accenti).
