# Registro Rename Gold → Impatto MicroStrategy

**Ultimo aggiornamento:** 2026-07-05
**Scopo:** tracciare **ogni rinomina** (schema, tabella, colonna) sul layer **Gold / DataMart / viste KPI**
che è **letto da MicroStrategy**, per valutare l'impatto sul modello di reporting prima del rilascio.

> Regola: qualunque rename di oggetto Gold consumato da MSTR (tabelle `F_*`, `A_*`, viste `kpi_*`)
> va registrato **qui** con mapping vecchio→nuovo e stato dell'impatto MSTR. Il layer silver
> (`logistica`, `logistica_curated`) NON è letto da MSTR → impatto MSTR nullo (registrato solo per completezza).

> **⚠️ Nota reporting (2026-07-04):** oggi MicroStrategy è mappato su **viste** (`kpi_*`), non
> direttamente sulle tabelle `F_*`/`A_*`. Quindi un rename di colonna tabella **non impatta subito
> MSTR** ma richiede la **revisione delle viste** che lo espongono (le viste sono lo strato di
> disaccoppiamento). Azione futura: **analisi del modello MSTR** per mappare esattamente quali
> viste/attributi/metriche legge, e da lì determinare l'impatto reale dei rename tabella.

## Legenda impatto MSTR
| Stato | Significato |
|-------|-------------|
| 🔴 DA RECEPIRE | attributo/metrica MSTR da aggiornare/rimappare prima del rilascio |
| 🟡 DA VERIFICARE | possibile impatto, dipende da come MSTR mappa l'oggetto |
| ⚪ NESSUNO | oggetto non consumato da MSTR (es. layer silver) |
| ✅ RECEPITO | modello MSTR aggiornato |

---

## A. Rename schema / tabelle

| Data | Vecchio | Nuovo | Layer | Impatto MSTR |
|------|---------|-------|-------|--------------|
| 2026-07-03 | `silver_dev.prep_logistica` | `silver_dev.logistica_curated` | Silver | ⚪ NESSUNO (silver non letto da MSTR) |

---

## B. Rename colonne aggregati `A_*` (⚠️ letti da MicroStrategy)

### B.1 — `gold.logistica_dm.A_INBOUND_MENSILE` (v3.0 → v4.0, 2026-07-04)
Causa: F_CARICO passato a grain **etichetta** (v4.0); l'aggregato v3 leggeva colonne del vecchio grain riga-dettaglio (inesistenti). Grain aggregato invariato: `FORNITORE_COD + SITO_COD + ANNO_MESE`.

| Colonna v3.0 (rimossa) | Colonna v4.0 (nuova) | Note |
|------------------------|----------------------|------|
| `QTA_ORDINATA_TOT` | `QTA_ORDINATA_TOT` | ✅ = SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN) in **PEZZI** (fix unità 2026-07-05; prima era in colli → ammanco errato) |
| `NRO_PZ_CARICATI_TOT` | `QTA_CARICO_TOT` | quantità caricata/ricevuta in **PEZZI** (colli×pz) |
| — | `QTA_UF_CARICO_TOT` | nuova: quantità in UF |
| `PESO_LORDO_TOT` | `PESO_CARICO_TOT` | peso da anagrafica articolo (PES_CARICO) |
| — | `VOL_CARICO_TOT` | nuova: volume |
| — | `NUM_PLT_TOT`, `NUM_IMB_TOT` | nuove: pallet / imballi |
| `NUM_RIGHE_DETTAGLIO` | `NUM_ETICHETTE` | conteggio al nuovo grain (etichette) |
| `NUM_CARICHI` | `NUM_CARICHI` | invariata (ora countDistinct NUM_DOC_CARICO) |
| `SCARTO_QTA_TOT` | `AMMANCO_QTA_TOT` | ✅ **ammanco in PEZZI** = pezzi ordinati − pezzi ricevuti (fix unità 2026-07-05); validato +253.243 pz = 1.51% |
| `TASSO_SCARTO` | `TASSO_AMMANCO` | ✅ ammanco / ordinato (pezzi) |

**Impatto MSTR:** 🔴 DA RECEPIRE — metriche MSTR su A_INBOUND (qtà/peso/scarto) da rimappare ai nuovi nomi; le metriche di scarto vanno ridefinite (vedi §D).

Gli altri aggregati `A_OUTBOUND_MENSILE`, `A_GIACENZE_MONTHLY`, `A_STOCK_MENSILE`, `A_PRODUTTIVITA_MENSILE`, `A_TURNO_PREP_SITO`: **nessun rename** (verificati coerenti coi fact, FASE 5/6).

---

## C. Rename / stato viste KPI (`kpi_*`)

| Data | Vecchia vista | Nuova vista | Stato | Impatto MSTR |
|------|---------------|-------------|-------|--------------|
| 2026-07-04 | `kpi_lead_time_fornitore` | `kpi_volumi_inbound_fornitore` | riscritta su A_INBOUND v4.0 | 🔴 DA RECEPIRE (nome vista + colonne cambiati) |
| 2026-07-04 | `kpi_qualita_ricevimento` | *(nome invariato)* | ✅ RIABILITATA su A_INBOUND v4.0 con misure **ammanco** (QTA_ORDINATA_TOT, QTA_RICEVUTA_TOT, AMMANCO_QTA_TOT, TASSO_AMMANCO) | 🔴 DA RECEPIRE (colonne cambiate: scarto→ammanco, sorgente ora aggregato) |

---

## D. Convenzione misure "ammanco" (ex "scarto") — ✅ APPLICATA 2026-07-04, unità corretta 2026-07-05

Le misure di "scarto ricevimento" sono **misure di business** (ordinato − ricevuto), non regole di scarto record.
Per chiarezza terminologica (evitare confusione con lo scarto-di-record) rinominate in **ammanco**.
L'ammanco vive **solo** in `A_INBOUND_MENSILE` (AMMANCO_QTA_TOT, TASSO_AMMANCO) e `kpi_qualita_ricevimento`.
Mapping:

| Nome storico (scarto) | Nome nuovo (ammanco) | Dove | Stato |
|-----------------------|----------------------|------|-------|
| `SCARTO_QTA` | ~~`AMMANCO_QTA`~~ | silver `carico_dettaglio` | ❌ **rimossa** (2026-07-05): unità mista + ammanco è concetto di ordine/gruppo, non di riga |
| `SCARTO_QTA_TOT` | `AMMANCO_QTA_TOT` | `A_INBOUND_MENSILE` | ✅ applicato (in pezzi) |
| `TASSO_SCARTO` | `TASSO_AMMANCO` | `A_INBOUND_MENSILE` | ✅ applicato |
| `NUM_RIGHE_CON_SCARTO`, `PERC_RIGHE_SCARTO`, `FLAG_SCARTO` | — | ~~kpi/dettaglio~~ | ❌ non ripristinati: metriche **per-riga**, non calcolabili al grain etichetta. La KPI usa l'ammanco **quantitativo aggregato**. |

**Definizione (unità PEZZI, fix 2026-07-05):** `QTA_ORD_FORN` è in **colli**, `QTA_CARICO` in **pezzi**
(fattore `NUM_PZ_IMB_ORD_FORN`). In `A_INBOUND`:
`QTA_ORDINATA_TOT = SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN)` [pezzi],
`AMMANCO_QTA_TOT = QTA_ORDINATA_TOT − QTA_CARICO_TOT`, `TASSO_AMMANCO = AMMANCO/ordinato`.
Validato: +253.243 pz = **1.51%** (prima −14.6M per unità miste colli/pezzi).
Nota grain: l'ordinato è concentrato sulla prima etichetta del gruppo (OP-CAR-3) → ammanco significativo
**solo aggregato** (non per singola etichetta). Vedi anche **OP-NAMING** (fase 2): i nomi ODI `QTA_ORD_FORN`/
`QTA_CARICO` restano per fedeltà/quadratura; unità nei commenti colonna; rename fisico rinviato.

---

## E. Come usare questo registro
1. Ad ogni rename di oggetto Gold consumato da MSTR → aggiungere riga qui con vecchio→nuovo + impatto.
2. Prima del rilascio MSTR → tutte le righe 🔴/🟡 vanno portate a ✅ RECEPITO col team BI.
3. Riferimenti: `05_open_points.md` (OP-CAR-3), `milestones/fase_7.md`, `sql/kpi/`.
