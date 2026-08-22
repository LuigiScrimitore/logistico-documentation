# ACT_9010 · Task DQ standalone nei workflow (`dq_gate` + registry acceptance)

**Status**: done   **Type**: dq   **Origin**: emerged (cross-check doc-vs-codice 2026-08-01)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (DQ / orchestrazione)
**Gg (stima)**: 0.5   **Closed**: 2026-08-04   **Blocco**: 🟢 (completata **e validata in locale**; gate bloccante a regime da verificare in cloud)
**Created**: 2026-08-01
**Dipende da**: `dq_monitor`/`acceptance` (KIT-03/04)   **Blocca**: gating DQ in pipeline PROD, shadow mode
**ADR collegate**: ADR-0014 (DQ & alerting interni), ADR-0001 (control catalog `config_dev`)   **OP collegati**: OP-20 (alerting), OP-21 (framework DQ), OP-02 (residui orphan)

## Contesto e motivazione
Il release kit aveva introdotto `dq_monitor.py` (severità/persistenza/gate) e `acceptance.py`
(`AcceptanceCriteria` + `run_smoke_test`), ma il cross-check ha rilevato che **nessun workflow eseguiva
DQ come step**: i check vivevano dentro i singoli notebook (`check_orphan_rate` in 5 notebook), quindi
**non potevano bloccare** il run né lasciare un esito consultabile.

**Causa vera (verificata sul codice):** `dq_monitor`/`acceptance` sono **librerie, non notebook** →
mancava l'**entrypoint orchestrabile**. L'ACT originale lo indicava come "da verificare": confermato.
Inoltre `ACCEPTANCE_REGISTRY` conteneva criteri per **3 pipeline su ~10** target Gold.

## Obiettivo
Ogni workflow che produce Gold ha un **task DQ finale** che applica i criteri di accettazione, persiste gli
esiti e **blocca** il run su fallimenti BLOCKING.

## Analisi tecnica — cosa è stato fatto
**1. Notebook entrypoint `notebooks/dq/dq_gate.py`** (nuovo, 131 righe). Widget: `env`, `run_date`,
`pipelines` (csv di chiavi registry, `*` = tutte), `wave` (filtro alternativo), `gate` (true/false).
Comportamento:
- esegue `run_smoke_test(..., gate=False)` per **ogni** pipeline selezionata e decide **alla fine** → un
  fallimento sulla prima pipeline non nasconde lo stato delle altre;
- un'eccezione su una pipeline non interrompe le altre (conteggiata come BLOCKING);
- pipeline non presenti nel registry → **segnalate e saltate**, non fanno fallire il task (il registry si
  popola incrementalmente);
- stampa un riepilogo tabellare e con `gate=true` solleva `DQBlockingError` → task FAILED → si attiva la
  notifica email del job (ponte finché non arriva l'alerting Reply, OP-20);
- esiti persistiti in `config_<env>.logistica_etl.dq_results` (control catalog D1, stessa area del watermark).

**2. `ACCEPTANCE_REGISTRY` esteso da 3 a 9 pipeline** con colonne **verificate sui notebook Gold**:
`gold_f_prep_sped`, `gold_f_turno_prep_sito`, `gold_f_giacenze_daily`, `gold_f_trasporto`,
`gold_f_tracciabilita_lotti`, `gold_f_ordini`.

**Calibrazioni fatte per non generare falsi FAIL bloccanti** (il check orphan è BLOCKING sul sentinel `-1`):
- `F_PREP_SPED`: `ART_RADICE_COD` **escluso** dagli `orphan_fks` — ha residui fisiologici (articoli non nel
  Retail Master) gated su **OP-02** ([[ACT_OP-32]]); con soglia 0% avrebbe bloccato ogni run.
- `F_PREP_SPED`: `DATA_BOLLA_SPED` **non** in `not_null` — è NULL **by-design** sulle righe scartate
  (TIPO_SCAR 09/10, OP-PSP-1); si usa `DATA_PREL`.
- `F_GIACENZE_DAILY`: **nessun** orphan check — il fact è per `MAG_COD` e non ha aggancio dimensionale
  (0 `surrogate_key_fallback` nel notebook), coerente con [[ACT_9009]].
- `F_TRASPORTO`: nessuna misura `nonneg` — non espone KM/COSTO (ADR-0013) e `LEAD_TIME_GG` può essere
  negativo per date sorgente incoerenti.
- `F_ORDINI`: criteri minimi (esistenza + volume) — è passthrough dal silver, colonne non verificabili
  offline; `not_null`/`unique_keys` da calibrare al primo run cloud.

**3. Task `dq_gate` aggiunto a 5 workflow**, in coda ai task Gold, con `max_retries: 0` (un fallimento DQ
non si risolve ritentando):
| Workflow | depends_on | pipeline verificate |
|---|---|---|
| `logistica_carichi` | `gold_late_arriving`, `gold_f_tracciabilita_lotti` | f_carico, f_tracciabilita_lotti |
| `logistica_giacenze` | `gold_f_giacenze_daily` | f_giacenze_daily |
| `logistica_prep_sped` | task Gold del workflow | f_prep_sped, **f_turno_prep_sito**, f_movimentazione_carrellisti |
| `logistica_trasporti` | `gold_f_ordini`, `gold_f_trasporto` | f_ordini, f_trasporto |
| `logistica_aggregati` | i 6 task `a_*` | a_inbound_mensile |

`logistica_dim_refresh` e `logistica_landing_ingestion` **non** hanno il gate: le dimensioni `LU_*` e il
layer Bronze richiedono criteri diversi, non ancora definiti → follow-up.

## Verifica
- `ast.parse` su `dq_gate.py` e `py_compile` su `acceptance.py`: OK.
- Validazione YAML dei 7 workflow (pyyaml in Docker): dq_gate presente su 5/5 workflow Gold, **0 dipendenze
  rotte**, **0 cluster classici residui**, `environment_key` su tutti i task (coerente [[ACT_9007]]).
- ✅ **VALIDATO IN LOCALE (2026-08-20, [[ACT_9005]])**: `dq_gate` eseguito via lo shim del runner sul
  warehouse rigenerato → **9/9 pipeline OK, 0 check falliti, 0 BLOCKING**, nessuna eccezione. Confermato che
  le calibrazioni dei criteri **non producono falsi FAIL**. Persistenza verificata: **78 righe** in
  `config_dev.logistica_etl.dq_results` (9 `run_id`, uno per pipeline) con tutti i tipi di check attesi
  (`row_count`, `not_null`, `unique_keys`, `nonneg_*`, `volume`).
- Comando usato: `run_notebook.py --notebook notebooks/dq/dq_gate.py --run-date 2026-06-10
  --warehouse /workspace/data/warehouse --set pipelines=<csv> --set gate=false`.
- ⚠️ Resta da verificare **in cloud**: il comportamento del gate bloccante a regime (`gate=true` su un
  fallimento reale) e l'alerting via webhook/email (OP-20).

## Esito
La DQ passa da "check sparsi nei notebook" a **step orchestrato e bloccante**, con esiti persistiti e
criteri dichiarativi per 9 pipeline. Le soglie sono calibrate sui residui **noti e documentati** invece di
essere teoricamente a zero.

## Follow-up
1. **Criteri per dimensioni `LU_*` e Bronze** → gate su `dim_refresh`/`landing_ingestion` (nuova ACT quando serve).
2. Calibrare `F_ORDINI` e le soglie `volume_max_dev_pct` al primo run cloud reale (oggi prudenziali 25-30%).
3. Sostituire `LogNotifier` con webhook/email quando arriva l'alerting di piattaforma (OP-20, [[ACT_OP-25]]).
4. Verifica del gate a regime nei gate cloud [[ACT_GATE-2]]..[[ACT_GATE-7]] e nel monitoraggio shadow ([[ACT_8.2.1]]).
5. ✅ **Emerso durante questa attività e poi risolto**: i workflow puntavano a 6 notebook inesistenti e 52
   notebook reali non erano orchestrati → **[[ACT_9014]]** (DAG derivato dal codice, ADR-0019). Con il
   riallineamento `gold_f_turno_prep_sito` è ora prodotto e il DQ gate di `prep_sped` lo verifica.
