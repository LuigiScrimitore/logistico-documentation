# ACT_9005 · Re-run di validazione + regressione (post-modifiche di schema)

**Status**: done   **Type**: analysis   **Origin**: emerged (validazione end-to-end post-modifiche)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: trasversale (validazione locale)
**Gg (stima)**: 1   **Closed**: 2026-08-20   **Blocco**: 🟢 (eseguito in locale)
**Created**: 2026-07-05
**Dipende da**: modifiche schema ([[ACT_9001]] grain etichetta, [[ACT_9002]] ammanco, [[ACT_9003]] NUM_PLT, prep_sped v4)
**Blocca**: (sbloccato) quadrature dati
**ADR collegate**: ADR-0010 (incrementale/idempotenza), ADR-0012 (ammanco in pezzi)   **OP collegati**: OP-29 (ordering), OP-33 (grain), OP-PSP-2 (DATA_PREL), OP-02 (residui orphan)

## Contesto e motivazione
Le modifiche di schema (grain etichetta F_CARICO, ammanco in pezzi, NUM_PLT, prep_sped v4) erano state
implementate ma **mai validate con un re-run**. Serviva confermare che i numeri prodotti coincidessero con
quelli dichiarati nelle rispettive ACT.

**Scope ridotto rispetto al piano originale (22 siti full):** C: aveva solo **16 GB liberi** contro i ~49 GB
richiesti dal full re-run ([[ACT_MNT-01]]). Poiché i Bronze erano **già popolati** (29 tabelle) e le modifiche
da validare vivono in Silver-curated/Gold, si è eseguito un **re-run mirato per fasi**
(`--only SILVER_PREP` → `GOLD_FACT` → `GOLD_AGG`), che copre esattamente ciò che è cambiato.

## Esito re-run — 21/21 notebook OK, 0 FAIL
| Fase | Notebook | Esito |
|---|---|---|
| SILVER_PREP | 7 | ✅ 7/7 (prep_sped 353s, il più lento) |
| GOLD_FACT | 8 | ✅ 8/8 |
| GOLD_AGG | 6 | ✅ 6/6 |

Righe per fact: F_PREP_SPED 7.316.805 · F_TURNO_PREP_SITO 196.823 · F_TRASPORTO 79.641 · F_CARICO 59.621 ·
F_GIACENZE_DAILY 55.203 · F_TRACCIABILITA_LOTTI 43.297 · F_ORDINI 9.502 · F_MOVIMENTAZIONE 126 (sul giorno).

## Valori attesi — tutti confermati
| Verifica | Atteso (da ACT) | Misurato |
|---|---|---|
| F_CARICO grain **etichetta** univoco ([[ACT_9001]]) | nessun duplicato | 59.621 righe = 59.621 chiavi ✅ |
| `SUM(QTA_ORD_FORN)` ([[ACT_9002]]) | 1.921.348 su 38.210 gruppi | **1.921.348 / 38.210** ✅ |
| Una sola etichetta per gruppo porta la qta (row_number) | = n. gruppi | 38.210 = 38.210 ✅ |
| Ammanco in **pezzi** (ADR-0012) | +253.243 pz ≈ 1,51% | **253.243 → 1,51%** ✅ |
| NUM_PLT ([[ACT_9003]], giorno 2026-06-10) | 126 righe, PLT 3.640 ≥ MISS 3.543 | **126 / 3.640 / 3.543** ✅ |
| Grain 9 chiavi F_PREP_SPED (OP-33) | univoco | 7.316.805 gruppi, **0 in eccesso** ✅ |
| Orphan sentinel `-1` | 0,0% | **0,0% su 11 FK** ✅ |
| Residui orphan `ART_RADICE_COD` (gated OP-02) | 77 | **77** (0,0005%) ✅ |
| Idempotenza write (duplicati entro partizione) | 0 | **0**, `max_righe_per_chiave = 1` ✅ |

## 🔴 Problema trovato e risolto: 6,7M righe stale in F_PREP_SPED
Il re-run ha fatto emergere che `F_PREP_SPED` conteneva **14.029.061 righe** invece di 7.316.805:
- **6.712.256 righe nella partizione `DATA_PREL = NULL`**, con `DWH_UPDATED_AT = 2026-07-02 07:42` → residuo
  del run del **2 luglio**, precedente al fix **OP-PSP-2** (che ha reso `DATA_PREL` una data reale);
- le partizioni datate contenevano esattamente le 7.316.805 righe scritte dal run di oggi
  (14.029.061 − 6.712.256 = 7.316.805);
- 6.336.834 chiavi risultavano presenti **sia** nella partizione NULL **sia** in una datata → duplicati logici.

**Causa**: il *dynamic partition overwrite* sostituisce solo le partizioni presenti nel nuovo dataframe. Dopo
il fix OP-PSP-2 il flusso non produce più righe con `DATA_PREL` NULL, quindi quella partizione **non viene
mai toccata** e sopravvive indefinitamente. Non è un difetto di idempotenza (verificato: 0 duplicati entro
partizione), è un **residuo di un cambio di semantica sulla colonna di partizione**.

**Impatto**: `SUM(QTA_PREP)` era **231.729.072 invece di 120.846.960**, cioè **+92%**. Qualsiasi conteggio,
KPI o quadratura su F_PREP_SPED sarebbe risultato gonfiato ~1,9× — errore silenzioso, la tabella "sembrava"
corretta. Stessa famiglia del bug tombstone ([[ACT_9006]]): sbagliava la lettura, non la pipeline.

**Risoluzione**: `DELETE FROM F_PREP_SPED WHERE DATA_PREL IS NULL` → rimosse esattamente 6.712.256 righe;
post-pulizia 7.316.805 righe, 0 NULL, grain univoco confermato.

## Validazione aggiuntiva: DQ gate in locale
Approfittando del warehouse rigenerato è stato eseguito **`notebooks/dq/dq_gate.py`** ([[ACT_9010]]) in
locale via lo shim del runner: **9/9 pipeline OK, 0 check falliti, 0 BLOCKING**, nessuna eccezione. Questo
promuove ACT_9010 da "efficacia verificabile solo in cloud" a **validata in locale**, e conferma che le
calibrazioni dei criteri non producono **falsi FAIL**.

## Lezioni (valide anche in cloud)
1. **Cambio di semantica della colonna di partizione ⇒ il dynamic overwrite non basta.** Serve un `DELETE`
   esplicito della vecchia partizione o un rebuild completo (CTAS), altrimenti restano righe invisibili che
   raddoppiano i totali. Da inserire nel playbook prima di ogni cambio di partizionamento.
2. **Il check `volume_max_dev_pct` del DQ gate avrebbe intercettato l'anomalia** (tabella al doppio dello
   storico): riscontro concreto del valore di [[ACT_9010]].
3. **Metodologica**: `COUNT(DISTINCT a,b,c)` **scarta le righe con NULL** in una delle colonne. Ha prodotto
   due falsi allarmi in questa sessione (406.849 "duplicati" su F_PREP_SPED, in realtà righe con chiave
   nullable). Per l'unicità su chiavi nullable usare `GROUP BY`.
4. Confrontare metriche di un **singolo giorno** con i totali di una tabella **multi-data** non è valido:
   `NUM_PLT_MOVIMENTATI` è NULL sulle 14 date precedenti (colonna aggiunta con ACT_9003 e valorizzata solo
   dal giorno rigenerato) → vedi follow-up.

## Follow-up
1. **Backfill `NUM_PLT_MOVIMENTATI`** sulle 14 date storiche (2026-06-13 → 06-27) dove è NULL, oppure
   accettarlo e documentarlo come "misura disponibile dal 2026-06-10".
2. **Full re-run 22 siti** (Bronze incluso) quando lo spazio disco lo consente ([[ACT_MNT-01]]) — questo
   re-run mirato valida le modifiche, non l'ingestion completa.
3. Passare al **run incrementale del giorno successivo** (`run_b_newday.py`) per validare il pattern
   incrementale sui dati rigenerati.
4. Verificare se altri fact hanno partizioni stale dello stesso tipo (F_CARICO/ANNO_MESE, F_GIACENZE/DATA_FOTO):
   controllo rapido consigliato prima delle quadrature.
