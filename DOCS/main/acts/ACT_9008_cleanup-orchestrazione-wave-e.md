# ACT_9008 · Cleanup orchestrazione Wave E (`logistica_wave_e.yml` rimosso)

**Status**: done   **Type**: doc   **Origin**: emerged (cross-check doc-vs-codice 2026-08-01)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 6 — Wave E
**Gg (stima)**: 0.5   **Closed**: 2026-08-04
**Blocco**: 🟢 (completata in locale)
**Created**: 2026-08-01
**Dipende da**: —   **Blocca**: chiarezza doc Wave E ([[ACT_6.3.1]]), validità `bundle deploy`
**ADR collegate**: ADR-0009 (serverless — contesto [[ACT_9007]])   **OP collegati**: OP-MOV-1, OP-27

## Contesto e motivazione
Il cross-check ha rilevato che `workflows/logistica_wave_e.yml` era un **placeholder deprecato**
(`STATO: DEPRECATO`, `pause_status: PAUSED`, `tasks: []`): la Wave E **non ha** un workflow proprio. Nella
realtà i task sono distribuiti nei workflow esistenti. La documentazione parlava invece di un workflow
dedicato `logistica_wave_e` alle 05:30 → fuorviante. In più il fact carrellisti era citato come
`gold_f_turno`, nome che **non esiste** nel repo.

**Motivo tecnico decisivo per rimuovere (non mantenere) il placeholder**: un job con **`tasks: []` non è
valido** per l'API Jobs (serve almeno un task) → avrebbe fatto **fallire `databricks bundle validate/deploy`**
al primo rilascio. Non era quindi un placeholder innocuo.

## Obiettivo
Nessun workflow fantasma nel bundle; documentazione Wave E allineata all'orchestrazione reale; naming del
fact carrellisti corretto.

## Analisi tecnica — stato reale verificato
| Componente Wave E | Dove gira davvero | Task |
|---|---|---|
| **Tracciabilità CE178** | `workflows/logistica_carichi.yml` (02:00) | `bronze_tracciace178`, `silver_traccia_ce178`, `silver_tracciabilita_lotto`, `gold_f_tracciabilita_lotti` |
| **Carrellisti** | `workflows/logistica_prep_sped.yml` (04:30) | `bronze_dettaglio_carr`, `bronze_imbfmovim`, `silver_missione_carrellista`, `silver_sessione_carrellista`, `gold_f_movimentazione_carrellisti` |
| **Dimensione operatori/carrellisti** | `workflows/logistica_dim_refresh.yml` (01:00) | `silver dim_operatore` (UNION 4 anagrafiche, OP-15) |

**Decisione: Opzione A — rimuovere il placeholder.** Una futura estensione Wave E dedicata si creerà come
nuovo workflow **con task reali**. I workflow scendono così da 8 a **7**.

**Refuso naming corretto**: il fact carrellisti reale è **`gold_f_movimentazione_carrellisti`**
(`notebooks/gold/carrellisti/…`), non `gold_f_turno` (che non esiste). Attenzione a non confonderlo con
`gold_f_turno_prep_sito`, che è un **altro** fact (prep spedizioni, ACT_4.3.5).

## Sviluppo (diario)
- 2026-08-01 · placeholder vuoto rilevato; CE178 in carichi, carrellisti in prep_sped.
- 2026-08-04 · rimosso `workflows/logistica_wave_e.yml`; propagato su doc e ACT; corretto il refuso
  `gold_f_turno` (incl. rinomina file `ACT_6.2.5_gold-f-turno.md` → `ACT_6.2.5_gold-f-movimentazione-carrellisti.md`).

## Verifica
- `ls workflows/` → **7** file, nessun `logistica_wave_e.yml`; nessun job con `tasks: []` nel bundle.
- `grep gold_f_turno` (esclusi `gold_f_turno_prep_sito` e le note "non gold_f_turno") → **0** occorrenze fuorvianti.
- Nessun link rotto al vecchio nome file di ACT_6.2.5.
- Conteggio workflow allineato a 7 in `01_architettura.md` e `03_linee_guida.md`.

## Esito
Placeholder **rimosso** (evitato un fallimento certo di `bundle validate/deploy`). Documentazione allineata:
`01_architettura.md` (tabella workflow + nota Wave E + conteggio 7; corretto anche `logistica_datamart.yml`
→ file reale `logistica_aggregati.yml`), `03_linee_guida.md` (7 workflow + nota), `sprint_6.2`/`sprint_6.3`,
[[ACT_6.3.1]] (titolo e contesto riscritti), [[ACT_6.2.5]] (rinominata + contenuto corretto), 6.2.3/6.2.4/6.2.6
(riferimenti), `15_backlog_master.md` (righe 6.2.5 e 6.3.1).

## Follow-up
La validazione dell'orchestrazione Wave E in cloud resta in [[ACT_6.3.1]] / [[ACT_GATE-6]].
