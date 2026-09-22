---
data: 2026-09-10
titolo: "Run completo 09 set (7/7) + allineamento anagrafiche e load storico 03→08 (42/42 verde) + fix LL-029 .cache() serverless"
autore: Francesco Foconi
push_monorepo: "n/d (solo DEV, non ancora pushato)"
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: []
lesson: [LL-029]
op: []
---

## Obiettivo
1. Run completo E2E dei 7 job in DEV sul giorno **2026-09-09**.
2. Allineare le **anagrafiche/riferimenti** anche sui giorni 03→08 (che avevano solo i transazionali)
   e caricare la storia giorno-per-giorno.

## Cosa e' stato fatto

### 1) Run 09 → 7/7 verde (ha scoperto LL-029)
- Seed full 2026-09-09 (logistix/stat/cdt_estr_raw/track + cdtdw), `--ignore-odi-flag`: 375 file
  (~2,95M righe) + cdtdw 6 file (~1,49M). Il 09 era completamente vuoto (self-contained).
- Run 7 job run_date=2026-09-09: **6/7**, unico rosso **prep_sped**.
- Root cause (nuovo bug latente): `silver_storico_liste_uniche` (+gemello `silver_storico_bolle_uniche`)
  usa `.cache()` **solo nel ramo incrementale** (`incremental = not full_refresh AND target esiste`,
  sotto-ramo batch parziale). Il run del 02 era full/primo → non toccava il cache; il 09 e' il **primo
  incrementale reale** → il serverless blocca `.cache()`:
  `[NOT_SUPPORTED_WITH_SERVERLESS] PERSIST TABLE ...`.
- Fix ([[LL-029]]): rimosso `.cache()` (solo hint di performance; Photon+disk cache rimaterializza).
  `bundle deploy -t dev` → ri-run prep_sped(09)+datamart(09) → **09 chiuso 7/7 verde**.

### 2) Allineamento anagrafiche 03→08 (replica, non ri-estrazione)
- Le anagrafiche/cdtdw sono snapshot `full`/`lookup` a validita' corrente (DATFIN_VALID=99999999):
  estrarle oggi per un giorno passato darebbe **righe identiche** allo snapshot del 09. Quindi
  **replica** server-side Volume→Volume dello snapshot 09 nelle partizioni 03→08 (no Oracle).
- Set replicato (escludendo transazionali e `catena`/`catena_esterni` = stock giornaliero non
  backfillabile): cdt-estr-raw (5), cdtdw (6), stat (2: buoni_eco/tipo_attivita_eco), track (vettori),
  logistix anagrafiche (9 tab × 22 siti). Totale **1272 copie, ok=1272 ko=0**.
- Nota tooling: `databricks fs cp` in PowerShell fallisce se l'output e' rediretto a null
  (`*> $null` / `| Out-Null` → "Flusso illeggibile"); va **catturato in variabile** (`$x = & databricks ... 2>&1`).

### 3) Load storico 03→08 → 42/42 verde
- 7 job per ciascun giorno 03→08, ordine cronologico. **Tutti SUCCESS** (7 righe di log perse per
  contesa in scrittura, ri-verificate via API `jobs list-runs`: tutte TERMINATED/SUCCESS).
- Storia DEV ora completa e verde **01→09** (01/02 gia' a posto).

## Doc aggiornati
- `lessons/LL-029_serverless-cache-persist-non-supportato.md` (nuovo) + INDEX rigenerato (29 lezioni).
- Notebook: `silver_storico_liste_uniche.py`, `silver_storico_bolle_uniche.py` (rimosso `.cache()`).

## Stato / prossimi passi — INDICAZIONI TEAM
- **Modifica solo in DEV**: fix `.cache()` deployata sul bundle dev di ffoconi, **non ancora pushata**
  sul monorepo. Al prossimo ciclo va portata su monorepo + single-repo (rebuild wheel non necessario:
  la fix e' nei notebook, non nella lib).
- `catena`/giacenze per 03→08 restano vuote (stock non backfillabile, [[LL-006]]): atteso.
- Anagrafiche/cdtdw su 03→08 sono lo snapshot corrente replicato (uniforme), non lo storico as-of-date
  (il sorgente non ha valid-time): adeguato per test DEV.
