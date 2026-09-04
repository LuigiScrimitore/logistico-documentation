# ACT_9026 · dim_sito da S_LOGISTIX+WL1 — fix orphan sito trasporti

**Status**: done
**Type**: fix
**Origin**: emerged (OP-TRA-1, orphan sito trasporti residuo dopo [[ACT_9025]])
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: FASE 3 — Wave Trasporti / Dimensioni
**Gg (stima)**: 1
**Blocco**: nessuno
**Created**: 2026-09-03   **Closed**: 2026-09-03
**Dipende da**: —   **Blocca**: chiusura OP-TRA-1 (orphan sito trasporti → 0)
**ADR collegate**: —   **OP collegati**: OP-TRA-1

## Contesto e motivazione
Dopo [[ACT_9025]] (giacenze verde) l'orphan sito dei trasporti restava ~69,8%. Root cause: la dimensione
`silver.logistica.dim_sito` (→ `LU_SITO`) era costruita da `bronze.logistica.struttura_mag`, che contiene
**solo 5 siti** e nessuna descrizione (SITO_DESC null). Le transazionali trasporti (`silver_ordini`,
`silver_trasporti`, `silver_spedizioni_clean`) referenziano invece **~18 siti** (via `normalize_sito` →
codice **numerico 2 cifre**). I 13 "fuori-master" NON erano errori di mapping: sono siti logistici reali e
attivi. L'anagrafica autoritativa dei siti è **S_LOGISTIX** (22 siti attivi, con `DBLINK_DESC` = nome sito).

## Obiettivo
`dim_sito`/`LU_SITO` contiene **tutti** i siti attivi con codice canonico numerico (== output di
`normalize_sito`) + descrizione reale → orphan sito trasporti **= 0**, senza toccare la logica delle
transazionali (che già producono il numerico corretto).

## Analisi tecnica
Catena di mapping (verificata su Oracle, VPN):
- `S_LOGISTIX` — 22 siti attivi: `MAG_SITO_COD` (canonico alfa `0020A`), `DBLINK_NAME` (`LOG_LGAX`),
  `DBLINK_DESC` (nome sito).
- `WL1_MAG_SITO_STORICO` — storico mapping: `MAG_SITO_COD` (alfa) ↔ `MAG_SITO_COD_ORIG` (numerico usato
  dalle transazionali). Filtro **correnti+attivi** = `DATFIN_VALID=99999999 AND MAG_SITO_ORIG_ATTIVO=1`.

Verifica robustezza del filtro (script `scratchpad/q_check.py`):
- **0 ambiguità**: con `DATFIN=99999999 AND ATTIVO=1` ogni `MAG_SITO_COD_ORIG` mappa a **un solo** sito.
- codici solo-`ATTIVO=0` = `1,19,2` (storici sostituiti, non nelle spedizioni) → giustamente esclusi.
- copertura spedizioni: **18/18** magazzini mappati a un sito attivo.

Implementazione:
1. `config.yaml` (landing `cdt_estr_raw`): aggiunte `s_logistix` + `wl1_mag_sito_storico` (mode full).
2. Nuovi bronze `bronze_s_logistix.py` + `bronze_wl1_mag_sito_storico.py` (template `bronze_automezzi`,
   FULL_OVERWRITE) in `notebooks/bronze/anagrafiche/`; task aggiunti a `logistica_landing_ingestion.yml`.
3. `silver_dim_sito.py` v4.0.0: build da `S_LOGISTIX ⋈ WL1(active)` su `MAG_SITO_COD`; `SITO_COD` =
   `lpad(digits(MAG_SITO_COD_ORIG),2)` (== `normalize_sito`), `SITO_DESC` = `DBLINK_DESC`, + colonne
   riferimento `SITO_COD_ALFA` (LGAX) e `SITO_COD_MAG` (0020A). Cast double per robustezza bronze
   string/parquet ("20"/"20.0"). Overwrite full.
4. `gold_dim_sito.py`: porta la `SITO_DESC` reale (prima forzata a null placeholder).

`silver_spedizioni_clean` / `silver_ordini` / `silver_trasporti` **non modificati**: già producono il
numerico canonico via `normalize_sito`.

## Verifica
- [x] seed `s_logistix` (22) + `wl1_mag_sito_storico` (60) in landing DEV + bronze (run one-off, SUCCESS).
- [x] run `silver_dim_sito` → **22 siti** con `SITO_COD` numerico + `SITO_DESC` reale + `SITO_COD_ALFA`/`SITO_COD_MAG`.
- [x] fix wheel `get_sito_alias_map` ([[LL-025]]) + rebuild/upload Volume `_wheels` → alias alfa risolti.
- [x] fix full_refresh=OVERWRITE ([[LL-026]]) su `silver_ordini`/`silver_trasporti`/`silver_spedizioni_clean`.
- [x] full_refresh `ordine` + `spedizioni_clean` → **orphan sito = 0** (cross-check vs `dim_sito`: ordine 5/5 ok,
      spedizioni 18/18 ok). `trasporto`/mtv/gold non ancora materializzati in DEV a questo run_date.
- [ ] non-regressione giacenze: `dim_sito` cambia grain (numerico), ma giacenze usa il ramo alfabetico
      ([[ACT_9025]], `silver_t_stock`) → non impattato; da confermare al prossimo run giacenze.

## Esito
**Fix validato in DEV (run_date 2026-09-02), orphan sito trasporti = 0.**
- `dim_sito` v4.0.0: 22 siti da `S_LOGISTIX ⋈ WL1` (numerico + descrizione reale) — era 5 siti da `struttura_mag`.
- `get_sito_alias_map` ([[LL-025]]): mappa completa da S_LOGISTIX+WL1 + cast double; risolve gli alias alfabetici
  (`LGAX/LONX/LCAX/LSLX/LGCX`) che restavano orphan.
- `full_refresh` ora fa overwrite ([[LL-026]]): il remap di `SITO_COD` non lascia righe stale duplicate.
- `spedizioni_clean` NON toccato nella logica (già numerico via `normalize_sito`); l'unica dipendenza era la
  alias-map (wheel).
Chiude la parte **trasporti** di OP-TRA-1 (la parte giacenze era già chiusa da [[ACT_9025]]).

## Lezioni
- I "fuori-master" sito erano dati reali, non errori: l'anagrafica master (`struttura_mag`, 5 siti) era
  **incompleta** rispetto alla realtà operativa (`S_LOGISTIX`, 22 siti). Vedi [[LL-025]] (mapping sito).

## Follow-up
- Valutare deprecazione di `struttura_mag` come sorgente sito una volta validata `S_LOGISTIX`.
- `get_sito_alias_map` (wheel) resta limitata a TABGEN tab 7 (5 alias): valutare estensione da S_LOGISTIX
  o deprecazione (le transazionali numeriche non ne hanno bisogno). Vedi [[LL-025]].
