# ADR-0007 · Standard "2-notebook": modellazione in `curated`, normalizzazione+scrittura in `gold`

**Status**: accepted (2026-06)

**Contesto**:
Ogni fact Gold richiede due tipi di lavoro molto diversi: (a) **modellazione** — join tra silver
(testata⋈dettaglio⋈pesata, union CONS/TRANSITO, ecc.) e **calcoli** di business (SCARTO/AMMANCO,
ANNO_MESE, SEC_PREP_PREL…); (b) **normalizzazione** — aggancio delle dimensioni per chiave naturale con
fallback sentinel, DQ orphan-rate, e scrittura Delta partizionata. Mischiare le due in un unico notebook
gold rende il codice difficile da leggere, testare e ri-eseguire, e confonde "dove avviene il calcolo".

**Alternative considerate**:
1. **Notebook gold monolitico** (modella + calcola + aggancia + scrive) — meno file, ma responsabilità
   confuse, difficile isolare un bug di calcolo da uno di aggancio, ri-uso nullo.
2. **Standard 2-notebook**: la modellazione+calcoli vivono in un **silver `logistica_curated.<fact>`**
   (SSOT del "cosa contiene"); il **gold `gold_f_<fact>`** fa **solo** aggancio dimensioni + scrittura
   ("regola d'oro: legge SOLO da `silver.logistica_curated.<fact>`").

**Decisione**:
Adottare lo **standard 2-notebook** (Linee guida §1-bis) per tutte le fact: `silver.logistica_curated.*`
= modellazione/calcoli; `gold_f_*` = aggancio dimensioni (`surrogate_key_fallback -1` +
`check_orphan_rate`) + scrittura (overwrite/`replaceWhere`, `partitionOverwriteMode` dynamic).

**Conseguenze**:
+ Separazione netta delle responsabilità: un bug di calcolo si cerca nel curated, uno di aggancio nel gold.
+ Il curated è **testabile/quadrabile** indipendentemente; il gold è uniforme tra le fact (stesso pattern).
+ Abilita LAD (ADR-0011) e acceptance (KIT-02) a lavorare su uno schema gold prevedibile.
− Più notebook e una tabella curated in più per fact (costo di storage/manutenzione modesto).
− Disciplina richiesta: il gold **non** deve reintrodurre calcoli (è successo con `gold_late_arriving_handler`,
  segnalato "da rifattorizzare" in certifica §1.1).

**Riferimenti**:
- Linee guida §1-bis: `03_linee_guida.md`. Pattern per fact in `02_pipeline_mapping.md`.
- Codice: `notebooks/gold/*/gold_f_*.py` (regola d'oro nell'header) · `notebooks/silver/*/silver_prep_*.py` / `logistica_curated.*`.
- Collegate: ADR-0006 (grain), ADR-0008 (chiavi naturali), ADR-0011 (LAD).
