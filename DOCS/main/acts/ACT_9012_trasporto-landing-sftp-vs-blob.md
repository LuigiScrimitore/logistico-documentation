# ACT_9012 · Trasporto verso landing — SFTP vs Blob (AzCopy/API) + `send_to_landing` pluggable

**Status**: resolved (protocollo) — 2026-08-31, [[ADR-0023]]
**Type**: analysis   **Origin**: emerged (thread mail "attivazione servizio sftp per logistico", 6 lug–3 ago 2026)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 0 — Landing & Ingestion
**Gg (stima)**: 1 (parte pluggable) + call   **Blocco**: 🤝 decisione cliente/Reply → **decisa: AzCopy** (2026-08-31)
**Created**: 2026-08-03   **Closed**: 2026-08-31 (protocollo; residuo C6 landing_mode aperto)
**Dipende da**: ~~esito call SFTP/Blob~~ → **deciso AzCopy** ([[ADR-0023]])   **Blocca**: C6 (`landing_mode`, ancora aperto), primo trasporto in landing
**ADR collegate**: [[ADR-0023]] (trasporto AzCopy — decisione), ADR-0003 (landing UC Volume), ADR-0005 (no segreti/canale export)   **OP collegati**: OP-07 (path landing), C5 (chiuso), C6 (aperto), OP-02 (estrazione anagrafiche)

> **Aggiornamento 2026-08-31 — deciso AzCopy (dai sistemi).** Il protocollo di trasporto è **AzCopy**, non SFTP
> ([[ADR-0023]]). **A tendere** eseguito da **processi ODI** (che invocano AzCopy), **owner: team** (ODI
> trasversale). **Per ora** si tiene lo script `send_to_sftp.py`; il backend AzCopy (`send_to_landing.py
> --transport azcopy`) si sviluppa su **branch dedicato**. Resta aperto **C6** (`landing_mode` external vs
> managed, da confermare con la piattaforma).

## Contesto e motivazione
Thread mail (`DOCS/altro/logistico azure sftp.pdf`, 7 messaggi 6 lug→3 ago 2026). **Reply** (Eddy Boscolo,
Erin Damini) spinge per **Azure Blob Storage via HTTPS (AzCopy/API)** invece di SFTP: SFTP su Azure ha una
**fee fissa ~195€/mese** per la sola attivazione del protocollo. **Conad** (Erika Lo Iacono, PM; Silvio
Torracchi; Service Owner = **Stefano Innocenti**) è cauta: volumi logistico ~1 GB/settimana (~1/60 dei flussi
vendita), costo non determinante, timore di complessità/rallentamenti su progetto in corso; disponibile se
percorso chiaro senza impatti. **Stato: aperto, call da fissare.**

## Obiettivo
Chiudere la modalità di alimentazione della landing (protocollo + accesso), sbloccando C5/C6, con impatto
minimo sul nostro codice. Farci trovare pronti a **entrambe** le opzioni.

## Analisi tecnica — punti fermi
**1. Per la nostra pipeline il protocollo è TRASPARENTE.** SFTP-su-Azure è un front-end sullo **stesso**
storage account Blob; sia SFTP sia AzCopy/API depositano i file **nello stesso container ADLS**. I Bronze
leggono via **External Location UC** in modo identico. Condizione: stesso container + convenzione path
(`<sorgente>-landing/<tabella>/YYYY/MM/DD/`, OP-07) + formato (CSV/Parquet, auto-detect già presente, C2).
⇒ conferma la direzione **`landing_mode=external`** (C6), non managed.

**2. TRASPORTO ≠ ESTRAZIONE (nodo architetturale).** Il flusso ha due step distinti:
`estrazione (Oracle on-prem → file CSV/Parquet)` → `trasporto (SFTP oppure AzCopy/API) → landing`.
- La discussione SFTP/Blob riguarda **solo il trasporto**.
- **AzCopy** = tool CLI Microsoft che **copia file** su Azure Storage (non estrae dai DB). **"API"** nella
  mail = **API/SDK di Azure Storage** (upload programmatico su Blob, es. `azure-storage-blob`), alternativa
  ad AzCopy — **non** significa che la sorgente esponga API. Entrambi presuppongono che i file **esistano già**.
- L'**estrazione** (step a monte) per **D5/ADR-0005 non gira su Databricks**: serve host **on-prem** con
  accesso Oracle + connettività Azure. **Chi la fa** è la vera domanda di ownership (vedi Punti aperti).

**3. Adattamento del nostro codice = piccolo, solo l'ultimo salto.** `scripts/sftp/send_to_sftp.py` (KIT-01)
→ evolvere in `send_to_landing.py` **pluggable**: `--transport sftp | azcopy | blob-api`. Estrazione, path,
formato invariati. Backend Blob via **SDK `azure-storage-blob`** (per ~1 GB/sett basta; AzCopy solo se serve
parallelismo). Auth: SAS o Service Principal con permessi per-container (mai segreti nel repo — `.env`/secret CI).

**Mondo "extra-logistico" impattato dallo stesso ragionamento** (tutto step-1/estrazione, indipendente dal
trasporto): `scripts/cdtdw_lookup_extractor` (anagrafiche `LU_*` → `bronze.condiviso`, **ponte fino a OP-02**)
e `scripts/quadratura` (dato di riferimento CDT_DW → export su landing per il confronto in cloud, DBR-04).
Restano tool di sviluppo/ponte da eseguire su host on-prem con accesso CDT_DW.

## Punti aperti (da portare alla call)
1. **SFTP vs Blob (AzCopy/API)** — decisione **cliente/Reply** (costo + tooling push). Per noi indifferente.
2. **"Quale SFTP esistente?"** (domanda di Silvio) → chiarire che logistico è **nuovo**: nessun SFTP da
   riusare; l'SFTP di G5/PJ è un altro flusso.
3. **Chi estrae i dati operativi** (Logistix/STAT/TRACK → file) e **dove gira**? Preferenza: lato **sorgente
   Conad** (coerente con as-is e D5). Da confermare.
4. **Estrazione CDT_DW** (anagrafiche-ponte + export quadratura): serve un runner on-prem con accesso CDT_DW
   (Conad fornisce l'export o ospita il nostro estrattore). Collegato a **OP-02**.
5. La nostra **unica richiesta**, qualunque scelta: container + path + **accesso lettura da UC** (External
   Location + Storage Credential o managed identity) + conferma formato.

## Verifica
Decisione protocollo verbalizzata; a valle: `send_to_landing.py` col backend scelto deposita nel container
concordato; un Bronze legge la landing via UC senza modifiche di logica; `landing_mode=external` compilato.

## Esito
**Protocollo deciso: AzCopy** (2026-08-31, dai sistemi → [[ADR-0023]]). Trasporto a tendere via **processi ODI**
(owner: team). Punto #1 (SFTP vs Blob) chiuso; punto #2 (nessun SFTP da riusare) confermato. Restano aperti i
punti di **ownership estrazione** (#3/#4) e **C6** (`landing_mode`).

## Follow-up
1. **Branch dedicato** per il backend AzCopy in `send_to_landing.py` (evolvere `send_to_sftp.py`, KIT-01) —
   auth container (SAS/SP/MI), path OP-07, formato invariato. Lo script attuale si mantiene nel frattempo.
2. **C6** — confermare con la piattaforma `landing_mode` (external probabile) → eventuale revisione di
   [[ADR-0003]]; flip in Terraform ([[ACT_0.1.3]]) a valle.
3. ✅ **Inviata (2026-08-31)** la richiesta accesso landing (§F.2 riformulata): **un container ADLS unico** su
   `stdevdataplatformweudata` + auth AzCopy (SAS/SP/MI) + accesso lettura UC + conferma `landing_mode` external.
   In attesa risposta piattaforma. Framing: Logistico prototipo per AzCopy standard (dismissione SFTP a tendere).
4. Ownership/host **estrazione** dati operativi + CDT_DW (invariato: on-prem, collega [[ACT_OP-02]]).
