# FASE 5 — Wave D: Trasporti (Outbound)

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** D | **Stato:** 🔵 F_TRASPORTO/F_ORDINI OK locale; quadratura pendente

## 1. Obiettivo & scope
Spedizione in uscita: dagli ordini e spedizioni al fact `F_TRASPORTO` (grana bolla) e `F_ORDINI`,
con aggancio vettore/corriere e calcolo costo a fasce di peso.

## 2. Sorgenti
Sistema **track**: `SPEDIZIONI`, `vettori`. Sistema **cdt_estr_raw**: `AUTOMEZZI`. Sistema **cnd**:
`t_trasp_mtv`. Ordini pendenti derivati da `sto_tes_carichi` (logistix).

## 3. Bronze
`spedizioni` (DELTA_MERGE), `vettori_track` (FULL, 96 righe), `automezzi` (FULL, ~1.9k), `t_trasp_mtv`
(DELTA, CND).

## 4. Silver
| Notebook | Target | Note |
|---|---|---|
| `silver_vettori_clean` | `logistica.vettori_track_clean` | FULL overwrite |
| `silver_automezzi_clean` | `logistica.automezzi_clean` | clean 1:1 |
| `silver_spedizioni_clean` | `logistica.spedizioni_clean` | dedup su SP_ID, MERGE |
| `silver_ordini` | `logistica.ordine` | filtro `FLAG_TRASFERITO != 'S'` (pendenti) |
| `silver_trasp_mtv_build` | `logistica.s_trasp_mtv` | rebuild catena trasporti (sostituzione WL2) |
| `silver_prep_trasporto` | `logistica_curated.trasporto` | JOIN + UNION CONS/TRANSITO, MERGE |
| `silver_prep_ordini` | `logistica_curated.ordini` | normalizzazione per Gold |

## 5. Gold
| Notebook | Target | Grain / regole |
|---|---|---|
| `gold_f_trasporto` | `logistica.F_TRASPORTO` | grana **bolla**; vettore/corriere agganciato |
| `gold_f_ordini` | `logistica.F_ORDINI` | ordini di consegna |

## 6. Regole di business chiave
- **Costo trasporto a fasce peso**: vedi `../01_architettura.md` §7.2.
- F_TRASPORTO a grana bolla → **non porta quantità/costo** aggregati (deliberato): `QTA_TRASPORTATA_TOT`
  e `COSTO_STIMATO_EUR_TOT` restano NULL in `A_OUTBOUND_MENSILE` finché non disponibili i listini corrieri.

## 7. Data Quality & quadratura
Q-04 quadratura `F_TRASPORTO` (QTA_CONSEGNATA, COSTO_EUR) vs Oracle — su cloud.

## 8. Open points di fase
- Listini corrieri assenti → costi trasporto non valorizzati (dipendenza esterna).
- OP-31 🟠 semi-join `ESTRAI_SPEDIZIONI` (CDC) vs finestra piena su `SP_DATABOLLA` — da validare su delta multipli.
- Rami secchi rimossi (RS-03/06/08): `silver_swap`, `silver_costo_trasporto`, `silver_trasp_mtv_build` deprecato — vedi `../06_backlog.md` §5d.

## 9. Stato & dipendenze
OK in locale. Dipende da FASE 1 (LU_CORRIERE/vettore) e dalle spedizioni TRACK via landing.

## 10. Riferimenti
`../02_pipeline_mapping.md` §7 "Trasporti", `../05_open_points.md` (OP-26/31), `../06_backlog.md` §5d.
