# ADR-0015 · Il tuning di esecuzione locale NON si trasferisce al cloud (ri-disegno su serverless)

**Status**: accepted (2026-07-05)

**Contesto**:
Lo sviluppo/collaudo avviene in **locale** su Spark single-machine (container Docker). Lì abbiamo dovuto
tarare parametri per far girare i job pesanti: `SPARK_DRIVER_MEMORY=12g`, gestione dello **spill**
(storico_bolle_uniche arrivava a ~57GB di spill), `partitionOverwriteMode` dynamic/static, guard
anti-degenerazione. C'è il rischio concreto che questi valori vengano **ereditati acriticamente** in
cloud. Ma su Databricks **serverless** (ADR-0009) shuffle, autoscaling, memoria e profilo di costo sono
un altro mondo: i valori locali sono **artefatti single-machine**, non ottimi cloud.

**Alternative considerate**:
1. **Portare le config locali in cloud** (stesso driver memory, stessi flag) — rischioso: sizing errato,
   spreco o OOM, costi non ottimizzati; falso senso di "già tarato".
2. **Ri-disegnare il tuning a fresco sul cloud**, osservando gli Spark UI reali, tenendo però la
   **logica** algoritmica (che è indipendente dalla macchina).

**Decisione**:
Il **sizing** (memoria driver, spill, cluster) si **ri-tara a fresco** su serverless, partendo dai
default e osservando i Spark UI/costi per wave. **NON** si eredita il locale. La **logica** invece **è
trasferibile** e va mantenuta: guard anti-degenerazione delle "uniche" (impacted>50%→full path),
`full_refresh` nel full-rebuild, MERGE null-safe, watermark, pruning `_row_hash`.

**Conseguenze**:
+ Evita di trascinare in cloud config nate per un vincolo locale; tuning basato su misure reali.
+ Distinzione netta **logica (migra)** vs **sizing (si ritara)** — guida chiara per il team.
− Il tuning cloud è un'attività da fare **per pipeline** al primo rilascio (parte del ciclo a fasi),
  non "gratis". Va messo in conto tempo di osservazione/iterazione.

**Riferimenti**:
- Sezione tuning cloud: `14_release_kit.md` §3.G (checklist "cosa NON portare dal locale").
- Contesto locale (lezioni): memory `big-rerun-pending` (spill 57GB, driver 12g, per-fase), `wsl-vhdx-disk-reclaim`.
- Collegate: ADR-0009 (serverless), ADR-0010 (incrementale/guard), ADR-0017 (rilascio a fasi).
