---
data: 2026-09-25
titolo: "Giro completo giorno 24: estrazione+landing cloud + run 7/7 via MI (grant UC ok)"
autore: Francesco Foconi
push_monorepo: "doc-pass worklog (PR dedicata)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: []
adr: []
lesson: [LL-033, LL-032, LL-034]
op: [OP-INF-3]
---

## Cosa e' stato fatto
Giro completo (estrazione → landing cloud → run Databricks) per il **run_date 2026-09-24**, eseguito
**con la Managed Identity** `id_dev_dataplatform_workload_00` (non da sandbox).

### 1) Estrazione + landing cloud
- Seed full del 24 (logistix/stat/cdt_estr_raw/track + cdtdw), `--ignore-odi-flag`, **copia sul Volume**
  (niente `-NoCopy`), `-NoArchive`. Landing cloud ora **01→24** completa (verificato su Volume).

### 2) Run 7 job via MI (run_date=2026-09-24)
- Lanciati i **job esistenti della MI** `[dev id_dev_dataplatform_workload_00] logistica_*` via
  `jobs run-now` (nessun deploy) — a wave: landing_ingestion → dim_refresh →
  carichi/giacenze/trasporti → prep_sped → datamart.
- **Esito: 7/7 SUCCESS** (11:02 → 11:17).

## Perche' ora funziona (contesto)
- **Grant UC alla MI ok** ([[LL-033]] risolto): la MI puo' leggere/scrivere i catalog `*_dev` → i job
  girano end-to-end (prima erano bloccati).
- **Permessi job via bundle** ([[LL-032]]): il blocco `permissions: CAN_MANAGE Group-Engineering-dev`
  nel `databricks.yml` (gia' su main) rende i job MI **visibili e lanciabili** dai nostri utenti →
  `run-now` possibile senza essere owner. **Nessun deploy → nessun doppione** ([[LL-030]]).
- **Fix dup F_CARICO** ([[LL-034]]) gia' deployata sulla MI (lavoro parallelo): `carichi` verde.

## Note operative
- L'estrazione (VPN Conad) ha richiesto due tentativi: primo abort per VPN giu' (`DPY-6005`), ok al
  riavvio VPN. Pattern ricorrente su questi giri manuali.
- Verifica anti-duplicazione: run via `run-now` sui 7 job esistenti (stessi job_id) → nessuna nuova
  risorsa creata.

## Stato
- Landing cloud DEV: **01→24**. Giorno 24 processato **7/7** in DEV via MI.
- Giro "estrazione → landing → Databricks" con la MI confermato funzionante end-to-end.
