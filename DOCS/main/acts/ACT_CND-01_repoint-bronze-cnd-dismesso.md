# ACT_CND-01 · Ri-punto dei Bronze che leggono ancora la sorgente `cnd` (dismessa in SCELTA B)

**Status**: in-progress (rimozione dead-code fatta e validata, PR aperto; blocchi sito → OP-TRA-1)
**Type**: refactoring / design pipeline   **Origin**: emerged (campagna "massa critica", 2026-09-02)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasporti + giacenze + prep_spedizioni
**Blocco**: 🟠 richiede l'intento di disegno SCELTA-B per ogni sorgente (config lo accenna, non specifica il rebuild)
**Created**: 2026-09-02   **Closed**: —
**Dipende da**: seed `track`/`cdt_estr` (fatto per 2026-09-01); disegno SCELTA-B
**Blocca**: `gold_f_trasporto`, gold giacenze, prep_spedizioni (non arrivano a gold)
**ADR collegate**: [[ADR-0017]] (rilascio a fasi)   **OP collegati**: OP-CND-1   **Vedi anche**: [[ACT_ST-01]] (flusso stock)

## Contesto e motivazione
In SCELTA B il sistema sorgente **`cnd` è dismesso** (le WL*/staging non si leggono più; si leggono le sorgenti
raw da `track`/`cdt_estr`/`logistix`). Ma **tre Bronze puntano ancora a `cnd-landing/`**, quindi vanno in
`PATH_NOT_FOUND` al run (il seed non produce `cnd`, per design):

| Bronze | Legge (`cnd`) | Target | Consumato da | Intento SCELTA-B (da `config.yaml`) |
|---|---|---|---|---|
| `bronze_vettori` | `t_vettori` | `bronze_dev.logistica.t_vettori` | `silver_vettori_clean` | superato da `vettori@track` (già `bronze_vettori_track`) |
| `bronze_trasporti` | `t_trasp_mtv` | `…​.t_trasp_mtv` | `silver_trasporti` | **rebuild** MTV da `spedizioni@track` |
| `bronze_giacenze_snapshot` | `t_stock` | `…​.t_stock` | `silver_prep_giacenze`, `silver_giacenze_aggregata` | `cndstostock` **dismesso** → stock da logistix `catena` (silver_t_stock degrada) |

## Perché non è un fix meccanico
Non basta cambiare il path: cambia la **sorgente e la semantica**. Es. `t_trasp_mtv` non esiste più come raw →
va **ricostruito** da `spedizioni@track` (logica di rebuild da definire col team); `t_stock` è dismesso →
lo stock passa da `catena` (logistix) con degrado documentato. Coerente con la linea "non mascherare le tabelle
assenti": qui si **ridisegna il flusso**, non si aggancia un default.

## Piano (bozza — da validare col team)
1. **`bronze_vettori`**: verificare che `silver_vettori_clean` sia superato da `silver_dim_corriere` (che usa
   `vettori_track`). Se sì → **rimuovere** `bronze_vettori` + `silver_vettori_clean` dal DAG trasporti e ri-puntare
   i consumer a `vettori_track`.
2. **`bronze_trasporti`**: definire il **rebuild di `s_trasp_mtv`** da `bronze_spedizioni` (track) in `silver_trasporti`
   (grain, chiavi, join). Rimuovere il Bronze `cnd`.
3. **`bronze_giacenze_snapshot`**: rimuovere (t_stock dismesso); `silver_prep_giacenze`/`silver_giacenze_aggregata`
   leggono lo stock da `catena` (logistix), con `VAL_STOCK_*` degradati come da config. Coordinare con [[ACT_ST-01]].
4. Aggiornare i workflow (rimozione task), i test e la doc di fase.

## Dove si esegue
Monorepo GitHub (`notebooks/bronze/{trasporti,giacenze}`, `notebooks/silver/{trasporti,giacenze}`, `workflows/`).

## Analisi consumer (2026-09-02, Francesco)
Verifica del DAG reale: **i silver "veri" sono GIÀ ripuntati a SCELTA-B** — il repoint è per gran parte fatto,
resta **dead-code removal** dei rami `cnd`, non una ricostruzione:
- **vettori**: `silver_dim_corriere` legge `bronze.logistica.vettori_track` (non `t_vettori`). `silver.logistica.vettori_clean`
  ha **0 consumer**. → Ramo morto: `bronze_vettori` (cnd) → `silver_vettori_clean`. (`silver_t_vettori` legge
  `vettori_track_clean`: verificare se ha consumer, altrimenti morto anch'esso.)
- **trasporti**: `silver_prep_trasporto` legge `spedizioni_clean` → scrive `silver.logistica_curated.trasporto`, che è
  la **unica sorgente** di `gold_f_trasporto`. `silver_trasporti` (vecchio) legge `t_trasp_mtv` (cnd) e scrive
  `silver.logistica.trasporto` (schema `logistica`, **non** `curated`) → **nessun consumer**. → Ramo morto:
  `bronze_trasporti` (cnd) → `silver_trasporti` (+ `silver_t_trasp_mtv`, da verificare).
- **stock**: `silver_prep_giacenze` legge `silver.logistica.t_stock`, popolata da `silver_t_stock` ← `catena_unificata`
  (logistix) + `cndstostock_clean` (opzionale, degrada VAL_STOCK→0). `bronze_giacenze_snapshot` scrive
  `bronze.logistica.t_stock` (bronze), che **nessuno legge** (il silver legge la SILVER t_stock, non la bronze).
  → Ramo morto: `bronze_giacenze_snapshot` (cnd).

**Conseguenza sul piano**: i 3 Bronze `cnd` non vanno "ricostruiti" ma **rimossi** dal DAG insieme ai silver
intermedi orfani e ai relativi task nei workflow `logistica_trasporti`/`logistica_giacenze`. Prima della rimozione:
confermare **consumer=0** per `silver_t_vettori` e `silver_t_trasp_mtv` (LL-010: mai drop silenziosi). Il "rebuild MTV"
del piano originale (nodo 2) **è già realizzato** da `silver_prep_trasporto`. La valorizzazione stock resta degradata
(cndstostock dismesso) come da config — nessuna azione qui.

## Esito
**In corso (2026-09-02, Francesco).** Rimossi 7 notebook morti (`bronze_vettori`, `bronze_trasporti`,
`bronze_giacenze_snapshot`, `silver_t_vettori`, `silver_t_trasp_mtv`, `silver_vettori_clean`, `silver_trasporti`)
+ i relativi task in `workflows/logistica_trasporti.yml` (4 task) e `logistica_giacenze.yml` (1 task + 1 depends_on
spurio in `silver_prep_giacenze`). `bundle validate` OK, `deploy -t dev` OK (7 file deleted). Lavoro su branch
locale `feat/act-cnd-01-remove-dead-cnd` (commit locale WIP, **non ancora PR**).

**Test E2E in DEV (sandbox `[dev flabffoconi]`, run_date 2026-09-02, seed logistix/stat/cdtdw/track/cdt_estr):**
- **Trasporti**: rimozione VALIDATA — bronze→silver→**gold_f_trasporto SUCCESS, gold_f_ordini SUCCESS**. Il DAG gira
  senza i rami morti. Job FAILED solo su `dq_gate` (1 check **blocking**, qualità dati — indipendente dalla rimozione).
- **Giacenze**: DAG parte senza `bronze_giacenze_snapshot`; bloccato **a monte** su `bronze_movimenti_magazzino`
  → `PATH_NOT_FOUND` su `lccx/imbfmovim` (sito 0 righe → nessun file; pattern [[LL-021]]) — **indipendente** dalla rimozione.

**Aggiornamento 2026-09-03 — rimozione VALIDATA, blocchi residui ricondotti a temi separati:**
1. `bronze_movimenti_magazzino` (PATH_NOT_FOUND lccx) → **risolto** da [[ACT_9024]] (PR #4 mergiato). Ri-run
   giacenze: il DAG arriva a `catena_unificata` (44.094 righe) — la rimozione non introduce regressioni.
2. `dq_gate` giacenze+trasporti → entrambi ricondotti al **problema sito sistemico** [[OP-TRA-1]] (3 formati di
   `MAG_SITO_COD`: `catena` minuscolo, `struttura_mag`/`lu_sito` MAIUSCOLO, `spedizioni` numerico). `silver_t_stock`=0
   (case) e `gold_f_trasporto` orphan 100% (numerico). **Indipendenti dalla rimozione** — attendono la conferma del
   canonico sito dal team. La certificazione [[ACT_ST-01]] (valore stock) resta a valle del fix sito.

**Conclusione**: il dead-code removal dei rami `cnd` è **completo e validato** (DAG integri, gold trasporti verdi,
nessun consumer perso). Aperto come **PR** (2026-09-03), lasciato a revisione team (refactoring d'area). I due blocchi
sito non appartengono a questo ACT.

## Follow-up
- Serve una decisione di dominio sul **rebuild MTV** (`t_trasp_mtv` ← `spedizioni@track`) prima di implementare il punto 2.
