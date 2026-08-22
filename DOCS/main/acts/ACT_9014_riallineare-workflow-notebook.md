# ACT_9014 · Riallineare i workflow ai notebook reali (DAG derivato dal codice)

**Status**: done
**Type**: fix   **Origin**: emerged (audit durante [[ACT_9010]], 2026-08-04)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (orchestrazione)
**Gg (stima)**: 2   **Closed**: 2026-08-04   **Blocco**: 🟢 (completata in locale; run reale cloud-gated)
**Created**: 2026-08-04
**Dipende da**: —   **Blocca**: (sbloccato) esecuzione reale dei workflow → [[ACT_GATE-1]]..[[ACT_GATE-7]], [[ACT_8.1.3]]
**ADR collegate**: **ADR-0019 (DAG derivato — creata da questa ACT)**, ADR-0009 (serverless), ADR-0007, ADR-0014   **OP collegati**: OP-29 (ordering), OP-32 (L-03), RS-01..08

## Contesto e motivazione
Aggiungendo il task DQ ([[ACT_9010]]) è emerso che i `workflows/*.yml` **non riflettevano la pipeline reale**:
erano fermi alla v3.0.0 (2026-06-08), mentre il codice è stato riscritto (standard 2-notebook ADR-0007,
catena rebuild-from-raw) e alcuni notebook **rimossi** come rami secchi ([[ACT_RS-01]]).

**Perché era grave**: `databricks bundle validate` **non** verifica l'esistenza dei notebook → il deploy
sarebbe passato e i run avrebbero fallito a runtime, oppure avrebbero prodotto **solo una parte** del Gold
con il DQ gate a bocciare tabelle mai popolate.

## Audit iniziale (2026-08-04)
**104** notebook · **58** path orchestrati · **52 orfani** · **6 path rotti**:
| notebook_path nel YML | Perché mancava |
|---|---|
| `silver_timbrature_sessioni` | rimosso (RS-05) |
| `silver_prep_sped_integrata` | rimosso, sostituito da `silver_prep_prep_sped` (RS-04) |
| `silver_swap` | rimosso (RS-03) |
| `silver_costo_trasporto` | rimosso (RS-06) |
| `bronze_pdv` | rimosso, PDV da CDT_DW (RS-01) |
| `silver_giacenze_daily` | **mai esistito** → il reale è `silver_prep_giacenze` |

Orfani critici: `gold_f_turno_prep_sito` (**fact certificato che nessun workflow produceva**),
`gold_lad_resolver`, `gold_lu_from_cdtdw`, le dimensioni Gold e **tutta la catena silver curated**.

## Come è stata risolta — DAG derivato, non riscritto a mano
La correzione manuale avrebbe risolto il sintomo lasciando la causa (già ricapitata una volta). Scelta
architetturale in **ADR-0019**: il DAG si **deriva dal codice**.
1. **Estrazione del grafo reale**: per ogni notebook si estraggono le tabelle lette/scritte
   (`spark.read.table`, `saveAsTable`, `SOURCE_TABLE`/`TARGET_TABLE`) → `depends_on` = chi scrive ciò che leggo.
2. **Bronze**: scrivono su tabella a nome dinamico (f-string) e il grafo non le vedeva → la tabella si ricava
   dalla costante `TABLE_NAME`, **abilitando le dipendenze bronze→silver** che altrimenti mancavano (i silver
   sarebbero potuti partire prima dei loro bronze).
3. **Parametri**: `base_parameters` derivati dai **widget realmente dichiarati** nel notebook → nessun
   parametro inventato né dimenticato.
4. **Riassegnazioni esplicite**: anagrafiche condivise (`artdgene`, `apvpunto_vendita`) spostate in
   `logistica_landing_ingestion` (00:30) perché servono al `dim_refresh` (01:00); **LAD resolver** messo
   **tra i fact e gli aggregati** (in testa a `logistica_aggregati`, un task per fact) così gli `A_*` leggono
   FK già risolte → **chiude il residuo L-03 di OP-32**.
5. **Esclusioni motivate** (6): `bronze_swap`, `bronze_vettori_locale` (deny list runner),
   `silver_trasporti` (superato da `silver_prep_trasporto`), `silver_t_trasp_mtv`, `silver_prep_bolle`,
   `gold_f_giacenze_monthly`.
6. **Guardrail** `tests/test_workflows_alignment.py` (30 test): path esistenti, `depends_on` valide, nessun
   ciclo, compute serverless + `environment_key`, **nessun orfano** fuori allow-list, e `base_parameters`
   che esistono come widget.

Fonte di verità per la ricostruzione: `tests/local_bronze/run_big_rerun.py` (flusso validato sui 22 siti).

## Verifica
- **7 workflow, 103 task**; **95/101 notebook orchestrati**, 6 esclusi con motivo.
- Guardrail: **30/30 test verdi** → 0 path rotti, 0 `depends_on` rotte, 0 cicli, 0 cluster classici, 0 orfani imprevisti.
- Sanity check DAG giacenze (ordine critico OP-29):
  `catena_clean`+`catena_esterni_clean` → `catena_unificata` → `t_stock` → `prep_giacenze` → `gold_f_giacenze_daily` → `dq_gate`.
- `02_pipeline_mapping.md`: sezione "Mappatura workflow → notebook" **rigenerata dai YML** (non più a mano).
- ⚠️ Il run reale in cloud resta da verificare nei gate di fase.

## Esito
Da 58 path (6 rotti) a **103 task** su 7 workflow con **95 notebook orchestrati** e dipendenze derivate dai
dati realmente letti/scritti. Il disallineamento non può ripresentarsi silenziosamente: lo intercetta il
guardrail. Chiuso anche L-03 di OP-32 (LAD schedulato).

## Follow-up
1. **Dipendenze cross-workflow** garantite solo dagli schedule sfalsati → valutare `run_job_task` o trigger
   su aggiornamento tabella (ADR-0019, conseguenze).
2. Verificare a regime i tempi/finestra: 103 task su serverless vanno ri-tarati al primo run (ADR-0015).
3. Estendere il DQ gate alle pipeline ora orchestrate e non ancora coperte (dimensioni `LU_*`, Bronze) → [[ACT_9010]] follow-up.
4. Aggiungere il guardrail alla pipeline CI GitLab quando i repo saranno attivi ([[ACT_9011]]).
