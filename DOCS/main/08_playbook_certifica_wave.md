# Playbook certifica & riscrittura fact — Wave di progetto

**Progetto:** Logistico 2.0
**Data:** 2026-07-02
**Scopo:** metodologia ripetibile (distillata dal lavoro su F_CARICO) per certificare e
riallineare ogni fact Gold alla logica legacy Exadata/ODI, e piano di applicazione a
partire da **F_PREP_SPED**.

---

## Parte A — Playbook (riusabile per tutti i fact)

### A0. Fonti autoritative (regola d'oro)
- Decodificare la logica **solo** dai sorgenti PL/SQL reali: `DOCS/99. SCRIPT/CDT_ESTR.sql`,
  `CDT_SA.sql`, `CDT_ESTR_VISTE.sql`.
- **NON** fidarsi dei `DOCS/Archive/mapping_*.md` (speculativi, pre-verifica schema: citano
  colonne inesistenti). Utili solo come indice di massima.
- Non inventare mai logica: sorgenti morte/dismesse o formule degeneri → **open point**.

### A1. Grain reale del fact CDT_DW
- `--discover` colonne + query di univocità su combinazioni chiave (come per F_CARICO:
  `(MAG_SITO_COD, NUM_DOC_*, NUM_ETICH...)`).
- Confermare col grain della **vista base** `V_*` / catena WL.
- **Pruning colonne — filtrare sul periodo di business**: per capire quali colonne sono
  costanti/null (escludibili), fare `SELECT DISTINCT`/`COUNT(DISTINCT)` **filtrando sulla
  data principale del fatto** (es. F_PREP_SPED → `GIORNO_BOLLA_SPED_ID BETWEEN ...`), NON su
  un sample `ROWNUM` grezzo: i fact CDT_DW contengono **righe storiche dismesse logicamente
  su Logistix ma ancora fisicamente presenti**, che inquinano i distinct e fanno sembrare
  popolate colonne in realtà morte.

### A2. Catena di trasformazione ODI
- Mappare `V_<area> (vista) → WL2 → WL3 → WL4 → T_<area> → CDT_DW.F_<area>`.
- Individuare per ogni sorgente se è **viva** (Logistix/EDW raggiungibile) o **morta**
  (dismessa/ferma, es. `cndstostock`, `articoli_foce` per i carichi).

### A3. Analisi colonne (classificazione)
Per ogni colonna CDT_DW: **(A)** già nel nostro silver · **(B)** nel bronze da esporre ·
**(C)** calcolabile da colonne disponibili · **(D)** da anagrafica master EDW (da estrarre) ·
**(E)** morta → open point documentato.

### A4. Chiavi e modello (pattern consolidati)
- **Sito**: `MAG_SITO_COD` (CDT_DW `0005C`) → codice canonico via `CDT_ESTR.S_LOGISTIX`
  (`int(cifre)` zero-pad 2). Pattern riusabile per tutti i fact.
- **Date**: FK `GIORNO_*_ID` → `L_GIORNO.GIORNO_DT` (JOIN).
- **Articolo**: `ART_RADICE_COD` + variante **logistica** (`ART_VARIANTE_LOGISTICA_ID`).
  Niente `ART_COD` (obsoleto) né varianti **storicizzate** (`ART_ST_*`).
- **Chiavi**: natural key validate ora (`surrogate_key_fallback`, fallback -1 / 'ND'),
  ID surrogati interi in futuro.

### A5. Anagrafiche master (EDW)
- Estrarre via `scripts/cdtdw_lookup_extractor` (READ-ONLY) con **watermark incrementale**
  `--audit-watermark` su `AUDIT_ID` (delta, non full ogni volta).
- Pubblicare in `bronze_dev.condiviso` via `gold_lu_from_cdtdw` con **MERGE** (upsert) per le
  tabelle incrementali (baseline CTAS + delta upsert).

### A6. Riscrittura silver_prep
- Da `silver_clean` (1:1) → `silver_prep` al **grain corretto**, fedele alla vista `V_*`.
- Modellazione (join guidati dal grain) + calcolo misure. Surrogate dimensioni NON qui
  (vivono nel Gold).

### A7. Gold
- FASE 3: `attach_<area>_dimensions` (colonne `_NAT` + `surrogate_key_fallback`).
- FASE 3b: misure da master (es. peso/volume da `LU_ART_UNITA_LOGISTICA`).
- Logica condivisa tra flusso normale e LAD handler (parità schema).

### A8. Quadratura
- Script parametrico per fact: CDT_DW (ODI) vs Gold Delta, grain confrontabile,
  soglia %, mapping sito via S_LOGISTIX. Generalizzare `quadratura_f_carico.py`.

### A9. Documentazione
- Aggiornare `07_certifica_gold_vs_cdtdw.md` (mapping colonne, stato, open point) e memoria.

---

## Parte B — Piano F_PREP_SPED

### Punto di partenza (vantaggio rispetto ai carichi)
L'area prep_spedizioni **ha già una catena WL modellata** in silver:
`storico_bolle_clean/uniche`, `storico_liste_clean/uniche`, `prep_riepiloghi`,
`prep_bolle`, `prep_prep_sped` → `gold_f_prep_sped`. Quindi il lavoro è prevalentemente
**certifica + allineamento mirato**, non ricostruzione da zero.

### Sorgenti / riferimenti ODI
- Fact: `CDT_DW.F_PREP_SPED` (verificare relazione con eventuale `F_TURNO_PREP_SITO`).
- Vista base: `V_PREP_SPED` (in `CDT_ESTR_VISTE.sql`) + catena WL in `CDT_ESTR.sql`.
- Sorgenti: `storico_bolle` + `storico_liste` (+ `riepiloghi`).
- Nota certifica: ODI aveva `SP_CHECK_PREP_SPED_NEW` che confrontava `F_PREP_SPED` con
  `LOGISTIX.RIEPILOGHI` (delta storici accettati) → utile come riferimento di quadratura.

### Passi (applicazione del playbook)
| # | Passo | Rif. playbook |
|---|---|---|
| P1 | `--discover` su `CDT_DW.F_PREP_SPED` + grain reale (query univocità) | A1 |
| P2 | Decodificare `V_PREP_SPED` + catena WL da CDT_ESTR(_VISTE).sql | A0, A2 |
| P3 | Gap analysis: confronto grain/colonne vista ODI ↔ nostro `silver_prep_prep_sped`/`gold_f_prep_sped` | A3 |
| P4 | Classificare colonne (A/B/C/D/E); identificare sorgenti morte → open point | A3, A2 |
| P5 | Allineare chiavi: sito S_LOGISTIX (già), date L_GIORNO, articolo radice+var logistica | A4 |
| P6 | Estrarre eventuali master mancanti (watermark AUDIT_ID) + pubblicare (MERGE) | A5 |
| P7 | Fix mirati su silver_prep (grain/misure) — non riscrittura totale se la catena WL regge | A6 |
| P8 | Allineare `gold_f_prep_sped` (dimensioni + misure) | A7 |
| P9 | Quadratura F_PREP_SPED vs CDT_DW (script parametrico) | A8 |
| P10 | Doc + open point | A9 |

### Criticità note (da `07_certifica`)
- Grain più complesso dei carichi (bolla × riga × operatore); confermare da vista.
- Delta storici accettati da ODI vs `RIEPILOGHI`: possibili differenze fisiologiche.

---

## Parte C — Sequenza wave

Ordine suggerito (per riuso crescente di pattern e anagrafiche):
1. **F_CARICO** — ✅ in corso (template)
2. **F_PREP_SPED** — prossimo (catena WL già presente)
3. **F_TURNO_PREP_SITO** — condivide operatori/turni con prep_sped
4. **F_TRASPORTO** (`F_TRASP_MTV`/`F_TRASP_TRATTA`)
5. **F_GIACENZE_DAILY** (`F_STOCK`) — dipende da `cndstostock` (verificare sorgente viva)
6. **F_MOVIMENTAZIONE_CARRELLISTI** (`F_MOV_CARR`)
7. **F_TRACCIABILITA_LOTTI** (`F_TRACC`)

Aggregati `A_*` (logistica_dm): certifica indiretta a valle dei fact certificati.
