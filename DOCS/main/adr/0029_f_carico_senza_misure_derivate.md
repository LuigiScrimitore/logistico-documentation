# ADR-0029 · F_CARICO senza misure derivate: via `QTA_ORD_FORN` e `VAL_COSTO_CARICO`

**Status**: accepted (2026-10-30) — supersedes, per F_CARICO, [[OP-CAR-1]] e [[OP-CAR-3]]; supersedes [[ADR-0012]] per la
parte ammanco in `A_INBOUND_MENSILE`

**Contesto**:
`F_CARICO` esponeva due misure che non nascono dal carico:
- `QTA_ORD_FORN` (quantità ordinata al fornitore): nel legacy distribuita per riga con una formula CEIL/FLOOR degenere;
  da noi (OP-CAR-3 opzione B) tutta sulla prima etichetta del gruppo (sito, ordine, radice, variante). Alimentava
  ordinato e ammanco di `A_INBOUND_MENSILE` ([[ADR-0012]]) e il KPI qualità ricevimento.
- `VAL_COSTO_CARICO` (qta × ultimo costo stock da `cndstostock`): NULL da noi (OP-CAR-1, sorgente dismessa).
Al SAL del 2026-10-29/30 il cliente ha stabilito che sono **misure non proprie dei carichi**: in futuro saranno
**derivate da altri fatti** (ordini, costi), non portate nella fact carichi.

**Alternative considerate**:
1. Tenerle allineate al legacy riga per riga (CEIL/FLOOR + costo da cndstostock): riapre due decisioni chiuse per misure
   che il cliente non vuole nel fatto. Scartata.
2. Tenerle come oggi (opzione B / NULL): fatto con misure che non gli appartengono e che non quadrano col legacy. Scartata.
3. **Rimuoverle** da F_CARICO e dai derivati che ne dipendono (scelta).

**Decisione**:
- `F_CARICO` (silver `logistica_curated.carico` e gold) **non espone** `QTA_ORD_FORN` né `VAL_COSTO_CARICO`.
  `NUM_PZ_IMB_ORD_FORN` resta: è un attributo della riga di carico (pezzi per imballo ordinato), non una misura.
- `A_INBOUND_MENSILE` perde `QTA_ORDINATA_TOT`, `AMMANCO_QTA_TOT`, `TASSO_AMMANCO`; le altre misure restano.
- KPI `kpi_qualita_ricevimento` (sql/kpi) **sospeso** finché l'ordinato non arriva da un fatto ordini.
- Perimetro della quadratura F_CARICO vs CDT_DW: righe/chiavi + `QTA_UF_CARICO`, `QTA_CARICO`, `PES_CARICO`, `VOL_CARICO`.
- Punto aperto per la reintroduzione: ordinato/ammanco derivati dal fatto ordini (OP-CAR-8).

**Conseguenze**:
+ La fact carichi contiene solo misure del carico; la quadratura col legacy ha un perimetro raggiungibile al 100%.
+ Spariscono due divergenze note dal legacy (OP-CAR-1, OP-CAR-3).
− Ordinato/ammanco e KPI qualità ricevimento non disponibili fino a OP-CAR-8. Nessun impatto oggi: progetto in sviluppo,
  nessun consumatore di gold (dashboard/analisi) al 2026-10-30.
− **Migrazione una tantum** per ambiente: gold scrive con `mergeSchema`/`replaceWhere`, che non elimina colonne →
  riscrittura con `overwriteSchema` di `F_CARICO`, `silver.logistica_curated.carico` e `A_INBOUND_MENSILE` (come
  [[ADR-0028]]); `DROP VIEW` del KPI sospeso se presente.
− Tocca `lib/logistica_utils/acceptance.py` → wheel da ricompilare e ricaricare sul Volume ([[ADR-0025]]).
Esecuzione: [[ACT_9039]].
