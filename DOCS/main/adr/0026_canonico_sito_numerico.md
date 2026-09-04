# ADR-0026 · Canonico sito: chiave numerica unica + attributi alfabetici sul gold

**Status**: accepted (2026-09-04)

**Contesto**:
Il codice sito/magazzino esiste in **tre rappresentazioni** tra le sorgenti dello stesso sito (es. Montopoli GV):
- **numerico** `20` (da `WL1.MAG_SITO_COD_ORIG` / cifre di `MAG_SITO_COD`) — usato dalle transazionali
  (spedizioni `SP_MAGAZZINO`, carichi `MAG_SITO_COD`);
- **alfabetico 4-char** `LGAX` (da `S_LOGISTIX.DBLINK_NAME` `LOG_LGAX`) — usato da catena/Logistix;
- **alfabetico 5-char** `0020A` (da `S_LOGISTIX.MAG_SITO_COD`) — codice "utente finale" CDT_DW.

La dimensione `LU_SITO` era costruita da `struttura_mag` (5 siti, `SITO_DESC` null) e, a causa di una alias-map
rotta ([[LL-025]]), restava di fatto alfabetica: i fatti trasporti (numerico) e giacenze/carichi (alfabetico)
non agganciavano coerentemente → orphan sito fino al 100% ([[OP-TRA-1]]). Emerso dai run E2E DEV ([[ACT_9026]]).

**Alternative considerate**:
1. **Due canonici** (giacenze alfabetico / trasporti numerico) con `LU_SITO` dual-key e dq per-area: mantiene la
   frammentazione, complica dq_gate e i join gold, non risolve la coerenza. Scartata.
2. **Unificare su alfabetico**: possibile ma i transazionali (numerico) sono la maggioranza e sarebbe un remap più
   invasivo; l'alfabetico resta comunque utile solo come display. Scartata.
3. **Unificare su NUMERICO come chiave, alfabetici come attributi** (scelta): un solo canonico per l'integrità
   referenziale; l'alfabetico si porta come attributo per il display sul gold.

**Decisione**:
- **Chiave canonica sito = NUMERICO 2 cifre** (`normalize_sito`, es. `20`, `05`) su **tutte** le aree (trasporti,
  carichi, giacenze). Anagrafica autoritativa dei siti = **`S_LOGISTIX`** (22 siti) ⋈ **`WL1_MAG_SITO_STORICO`**
  (codice numerico, filtro correnti+attivi `DATFIN_VALID=99999999 AND MAG_SITO_ORIG_ATTIVO=1`).
- `dim_sito`/`LU_SITO` costruita da S_LOGISTIX+WL1 (22 siti) ed **espone gli attributi alfabetici**:
  `SITO_COD` (numerico, chiave) + `SITO_COD_ALFA` (`LGAX`) + `SITO_COD_MAG` (`0020A`) + `SITO_DESC`.
- `get_sito_alias_map` (wheel) costruita **completa** da S_LOGISTIX+WL1 (+ fallback TABGEN), cast robusto
  ([[LL-025]]) → `normalize_sito` risolve gli alias alfabetici al numerico.
- Un **remap** di `SITO_COD` richiede `full_refresh=OVERWRITE` (il merge lascerebbe righe stale, [[LL-026]]).

**Conseguenze**:
+ **Orphan sito = 0** su carichi/trasporti/giacenze (validato DEV, run_date 2026-09-02) → dq_gate verdi.
+ Un solo canonico → join gold/LAD coerenti; l'alfabetico resta disponibile per report/utente finale.
+ Supera l'approccio alfabetico-per-trasporti tentato in ACT_9025 (che resta valido solo per il ramo giacenze
  `silver_t_stock`).
− Richiede `full_refresh` una-tantum delle silver che avevano già scritto il vecchio codice.
− La versione del pacchetto wheel resta 1.0.0 a runtime (`%pip` da Volume): la fix alias-map è nel wheel
  ribuildato, disallineata dal tag GitLab `v1.0.5` ([[LL-013]], nota versioning).

**Riferimenti**: [[ACT_9026]] · [[ACT_9027]] · [[LL-025]] (alias-map cast+completezza) · [[LL-026]]
(full_refresh=overwrite) · [[OP-TRA-1]] (chiuso) · [[logistico-sito-mapping]] · `S_LOGISTIX`/`WL1_MAG_SITO_STORICO`.
