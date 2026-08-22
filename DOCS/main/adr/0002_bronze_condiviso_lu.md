# ADR-0002 · Lookup master condivise (`LU_*`) in `bronze_<env>.condiviso`

**Status**: accepted (retroactive) (2026-07-02)

**Contesto**:
Le fact logistiche (F_CARICO, F_PREP_SPED, …) si agganciano a **dimensioni master** che **non** sono
di proprietà della logistica: articolo (`LU_ART_RADICE`, `LU_ART_UNITA_LOGISTICA`), fornitore
(`LU_FORNITORE`), punto vendita (`LU_PDV`), calendario (`LU_GIORNO/LU_MESE`). Queste anagrafiche vivono
nel **DWH Retail (CDT_DW)** e, a regime, sono prodotte dal flusso aziendale **"Master Data Master"** con
naming `LU_*`. Reply **non** prevede uno schema `gold.condiviso` dedicato alla logistica. Sorge quindi
il problema: *dove legge le master il nostro flusso*, senza (a) dipendere da un perimetro Retail non
ancora pronto (OP-02 aperto) e (b) senza accoppiare la nostra pipeline al Retail in modo bloccante.

**Alternative considerate**:
1. **Catalog/schema `gold_prod.condiviso` nostro** che replica le master — invade il perimetro
   Retail/Reply e crea ambiguità su chi è owner delle master; rischio di due "verità" anagrafiche.
2. **Join diretto alle tabelle Retail** appena disponibili — bloccante: finché OP-02 non definisce
   percorsi/nomi ufficiali, la pipeline non partirebbe.
3. **Estrarre le `LU_*` da CDT_DW e pubblicarle in uno schema isolato nostro** — disaccoppiamento
   totale, la logistica parte subito, si ripunta al Retail quando OP-02 sarà chiuso.

**Decisione**:
Decisione **D2**: per il primo rilascio le `LU_*` da CDT_DW vivono in **`bronze_<env>.condiviso`**
(schema isolato, popolato dal push/estrazione cdt_dw — `gold_lu_from_cdtdw.py`). Le fact Gold portano
**sempre le chiavi naturali** (es. `FORNITORE_COD`, `ART_RADICE_COD`); la join alle master è **opzionale
e parametrica** via `retail_master_schema` (placeholder che oggi punta a `bronze_<env>.condiviso`,
domani a Gold Retail). Il LAD resolver (ADR-0011) usa lo stesso parametro.

**Conseguenze**:
+ La logistica **parte senza attendere** il consolidamento master Retail; disaccoppiamento netto.
+ Le fact restano valide (chiavi naturali) anche senza join master; la risoluzione surrogata è additiva.
− **Duplicazione temporanea** delle master in `bronze.condiviso` → da ripuntare a Gold Retail alla
  chiusura di OP-02 (una-tantum, cambiando `retail_master_schema`).
− La risoluzione ART/FORNITORE dipende dalla completezza del master estratto (vedi orphan/quarantena LAD).

**Riferimenti**:
- Sezione anagrafiche/lookup condivise: `01_architettura.md` (modello a stella, dimensioni) e `05_open_points.md` (OP-01, OP-02).
- Codice: `notebooks/gold/condiviso/gold_lu_from_cdtdw.py` · `scripts/cdtdw_lookup_extractor/`.
- Collegate: ADR-0008 (chiavi naturali), ADR-0011 (LAD). Memory `project-d1-d5-decisions`, `gold-natural-key-vs-surrogate`.
