# Documenti tecnici di fase — Logistico 2.0

**Ultimo aggiornamento:** 2026-07-02

Un documento tecnico **dettagliato per ogni fase** di progetto. Sono la SSOT operativa della singola
fase: sorgenti, notebook, grain, regole di business, DQ/quadratura, open point e stato. Complementari
ai fondamentali (`../01`-`../04`) che restano trasversali.

> **Best practice (vincolante):** ad ogni attività completata, allineare **in contestuale** il doc di
> fase impattato + i registri (`../05_open_points`, `../06_backlog`) + gli eventuali fondamentali.
> Aggiornare la data header del doc toccato.

## Indice

| Fase | Documento | Wave | Fact principali |
|------|-----------|------|-----------------|
| 0 | [F0_infrastruttura.md](F0_infrastruttura.md) | — | (Unity Catalog, DAB, CI/CD, migrazione brownfield) |
| 1 | [F1_master_data.md](F1_master_data.md) | — | dimensioni `LU_*`/`dim_*`, anagrafiche |
| 2 | [F2_carichi.md](F2_carichi.md) | A | `F_CARICO`, `F_TRACCIABILITA_LOTTI` |
| 3 | [F3_giacenze.md](F3_giacenze.md) | B | `F_GIACENZE_DAILY` |
| 4 | [F4_prep_spedizioni.md](F4_prep_spedizioni.md) | C | `F_PREP_SPED`, `F_TURNO_PREP_SITO` |
| 5 | [F5_trasporti.md](F5_trasporti.md) | D | `F_TRASPORTO`, `F_ORDINI` |
| 6 | [F6_tracciabilita_carrellisti.md](F6_tracciabilita_carrellisti.md) | E | CE178, movimentazione carrellisti |
| 7 | [F7_kpi_aggregati.md](F7_kpi_aggregati.md) | — | aggregati `A_*`, view KPI |
| 8 | [F8_shadow_cutover.md](F8_shadow_cutover.md) | — | shadow mode, quadratura, cut-over |

## Template di sezione (per uniformità)

Ogni doc di fase segue questa struttura:

1. **Obiettivo & scope** — cosa produce la fase, confini
2. **Sorgenti** — sistemi e tabelle raw di input
3. **Bronze** — notebook, tabelle, modalità di scrittura
4. **Silver** — clean + prep, join, grain
5. **Gold** — fact/aggregati, grain, regole di business
6. **Dimensioni/anagrafiche agganciate**
7. **Data Quality & quadratura**
8. **Open points di fase**
9. **Stato & dipendenze**
10. **Riferimenti**
