# ADR-0028 · Naming canonico "vettore": colonna VETTORE_COD + dimensione LU_VETTORE

**Status**: accepted (2026-10-21)

**Contesto**:
Il concetto di trasportatore nel gold era stato chiamato **corriere** (`CORRIERE_COD`, dimensione `LU_CORRIERE`,
silver `dim_corriere`), mentre tutte le **sorgenti** usano "vettore" (`VETTORE_CARICO_COD` su CDT_DW.F_CARICO,
`VETTORE_SPED_COD`, `VET_CODICE`). Il **cliente** richiede espressamente — requisito **non derogabile** — che
il nome esposto sia **vettore** (vedi revisione mappa colonne F_CARICO, [[ACT_9031]]).

**Alternative considerate**:
1. Solo F_CARICO → incoerenza di naming tra i fatti (stesso concetto, due nomi). Scartata.
2. Solo la colonna in tutti i fatti, tabella `LU_CORRIERE` invariata → tabella "corriere" con chiave "vettore",
   incoerente. Scartata.
3. **Rinomina completa colonna + tabella** (scelta): un solo nome, "vettore", end-to-end.

**Decisione**:
- **Colonna canonica = `VETTORE_COD`** (e natural key `VETTORE_COD_NAT`) su **tutti** i fatti che la espongono:
  `F_CARICO`, `F_TRASPORTO`, `F_PREP_SPED`, `A_OUTBOUND_MENSILE`.
- **Dimensione = `LU_VETTORE`** (gold) / **`dim_vettore`** (silver). Chiave `VETTORE_COD`.
- Allineati: `gold_lad_resolver` (dim_pk `VETTORE_COD`), i 4 KPI SQL (costo_trasporto, fill_rate, resa_corrieri,
  optimize), `lib/logistica_utils` (`attach_carico_dimensions` espone `VETTORE_COD_NAT` + join `LU_VETTORE`),
  i notebook dimensione (file rinominati `gold_dim_vettore.py` / `silver_dim_vettore.py`) e il workflow
  `logistica_dim_refresh`.
- Le **sorgenti** restano col loro nome originale (`STCAR_COD_CORRIERE`, `VETTORE_SPED_COD`, `VET_CODICE`):
  il rename è sul **modello gold/silver**, non sull'estrazione.

**Conseguenze**:
+ Naming coerente col cliente e con le sorgenti (vettore ovunque).
+ Un solo canonico → join/LAD/KPI allineati.
− **Richiede migrazione** (una-tantum, per ambiente): le tabelle gold già scritte hanno `CORRIERE_COD`/`LU_CORRIERE`.
  Passi: (1) deploy nuovo codice via CI; (2) `full_refresh` con overwriteSchema dei fatti impattati per eliminare
  la vecchia colonna `CORRIERE_COD`; (3) `dim_refresh` crea `LU_VETTORE`; (4) `DROP` di `LU_CORRIERE` e silver
  `dim_corriere` dopo validazione. Idem su prod al go-live. Vedi [[ACT_9031]].
− Il **wheel** `logistica_utils` va ricompilato e ricaricato sul Volume (il rename è anche nella lib, [[ADR-0025]]).
− La validazione **non** si fa in sandbox personale (condivide i cataloghi `*_dev` → muterebbe lo schema condiviso):
  si valida sul **dev condiviso via CI** con la migrazione sopra.
