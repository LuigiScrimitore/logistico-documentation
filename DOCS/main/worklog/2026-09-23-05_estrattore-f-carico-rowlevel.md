---
data: 2026-09-23
titolo: "Estrattore row-level CDT_DW.F_CARICO per quadratura a gradi (ACT_9029, Q-01)"
autore: Francesco Foconi
push_monorepo: "PR dedicata (feat/act-9029)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "— (tooling quadratura, non tocca il bundle)"
act: [ACT_9029]
adr: []
lesson: []
op: [Q-01]
---

## Contesto
Verso la quadratura F_CARICO gold vs CDT_DW (Q-01, gate Fase 2), da fare **a gradi**: prima la
**struttura** (chiavi + numero colonne), poi la **bontà del dato**. Gli strumenti esistenti
(`quadratura_fact.py`/`quadratura_f_carico.py`) confrontano solo **KPI aggregati** (COUNT+SUM per
sito×giorno) e leggono il **gold locale**; mancava un modo per **portare giù i dati grezzi** di
`CDT_DW.F_CARICO` per giorni (per confronto strutturale e row-level).

## Cosa
Nuovo `scripts/quadratura/extract_f_carico.py` (READ-ONLY, riusa connessione/mapping di
`quadratura_f_carico.py`), interprete **`py -3.12`** (ha `oracledb`):
- `--discover` → colonne + tipi + **numero** + **chiavi** (PK/Unique da `ALL_CONSTRAINTS`) di
  `CDT_DW.F_CARICO` (fase 1, lato ODI).
- `--gold-schema` → colonne + numero del Gold F_CARICO (parquet locale) (fase 1, lato nuovo DWH).
- `--da/--a [--siti] [--out]` → estrazione **row-level per-giorno** (`SELECT f.*, g.GIORNO_DT` con join
  `L_GIORNO`) → **parquet** in `<LOGISTICO_DATA>/quadratura/f_carico/cdtdw/AAAA/MM/GG/`.
- ACT_9029 documenta piano e fasi.

## Stato
- Sintassi/compile OK; `--help`/esecuzione richiedono `py -3.12` + **VPN/Oracle**.
- **Da validare a runtime** con `--discover` (conferma nomi colonna/chiavi reali di F_CARICO).

## Prossimi passi
1. `py -3.12 extract_f_carico.py --discover` (valida schema/chiavi ODI) + `--gold-schema` (lato gold)
   → **confronto fase 1** (numero colonne + chiavi per lato, mapping semantico).
2. Estrazione di alcuni giorni coperti dal gold → **confronto fase 2** (bontà del dato, row-level).
3. **Decisione aperta (ACT_9029)**: gold di riferimento per la fase 2 = **locale** (warehouse parquet)
   o **cloud** (Databricks `gold_dev`)? Il locale può essere stantìo; il cloud richiede accesso DB.
