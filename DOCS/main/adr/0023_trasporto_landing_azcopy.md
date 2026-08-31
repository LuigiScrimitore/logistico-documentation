# ADR-0023 · Trasporto verso landing = AzCopy (processi ODI), non SFTP

**Status**: accepted (2026-08-31) — chiude la questione protocollo di [[ACT_9012]] / C5

**Contesto**:
La landing va alimentata con i file estratti dai sorgenti (Logistix/STAT/TRACK + cdt_dw). Il **protocollo di
trasporto** era aperto — **SFTP** vs **AzCopy/Blob** — analizzato in [[ACT_9012]] (C5). Reply spingeva per
AzCopy/Blob su HTTPS per evitare la **fee SFTP ~195€/mese** (attivazione del protocollo su Azure Storage);
Conad era cauta (volumi logistico ~1 GB/settimana, ~1/60 dei flussi vendita). Il punto era lasciato "call da
fissare". **Aggiornamento dai sistemi (2026-08-31): deciso AzCopy al posto di SFTP.**

**Alternative considerate**:
1. **SFTP su Azure Storage**: front-end SFTP sullo stesso storage account Blob. Comporta una **fee fissa
   ~195€/mese** per la sola attivazione del protocollo. Nessun vantaggio funzionale per i nostri volumi.
2. **AzCopy/Blob su HTTPS** (scelto): copia dei file su ADLS via **AzCopy** (o SDK `azure-storage-blob`).
   Nessuna fee SFTP; per ~1 GB/settimana è ampiamente sufficiente; è il tooling standard Microsoft per il
   trasferimento verso Storage.

**Decisione**:
**Trasporto verso landing via AzCopy**, non SFTP.
- **A tendere** il trasporto sarà eseguito da **processi ODI** che invocano AzCopy. La creazione, modifica e
  gestione di questi processi ODI è **in carico al team** (ODI è trasversale, non strettamente legato al
  progetto Logistico).
- **Per ora si mantiene** lo script di send esistente (`scripts/sftp/send_to_sftp.py`, KIT-01) come
  ponte/testing; lo sviluppo del **backend AzCopy** (`send_to_landing.py --transport azcopy`) avverrà su un
  **branch dedicato**.
- Per la nostra pipeline il trasporto è **trasparente**: stesso container ADLS, convenzione path OP-07
  (`<sorgente>-landing/<tabella>/YYYY/MM/DD/`), formato CSV con auto-detect (C2). I Bronze non cambiano.

**Conseguenze**:
+ **Nessuna fee SFTP ~195€/mese**; chiude C5 e il punto #1 di [[ACT_9012]].
+ **Pipeline invariata** (protocollo trasparente): path, formato e SLA (04:00, OP-09) restano quelli concordati.
+ **Estrazione ≠ trasporto** resta valido: AzCopy è solo il *trasporto*; l'estrazione Oracle→file resta a
  monte, **on-prem**, per D5/[[ADR-0005]] (non gira su Databricks).
− **`landing_mode` external vs managed = ancora APERTO (C6)**: AzCopy scrive in un container; se popolato
  esternamente, UC lo legge via **External Location** (direzione probabile: `external`), ma va **confermato con
  la piattaforma** — **non deciso qui**. Impatta [[ADR-0003]]/D3 (landing = UC Volume *managed*): possibile
  revisione a valle della conferma.
− Richiesta a piattaforma/sistemi: **container + path + auth AzCopy** (SAS / Service Principal / Managed
  Identity) + **accesso in lettura da UC**. La mail "credenziali SFTP" (§F.2 di `12_checklist_infra_setup.md`)
  è **superata** → va riformulata come richiesta accesso container per AzCopy.
− **Ownership ODI**: il team mantiene i processi ODI di trasporto (sviluppo su branch dedicato), coordinandosi
  con chi gestisce l'ODI trasversale.

**Riferimenti**: [[ACT_9012]] (analisi SFTP vs Blob + `send_to_landing` pluggable) · [[ADR-0005]] (no segreti
Oracle / export su landing) · [[ADR-0003]] (landing UC Volume — da rivedere su C6) · C1/C5/C6/C7 e §F.2 in
`12_checklist_infra_setup.md` · OP-07/OP-09 in `05_open_points.md` · `14_release_kit.md` (KIT-01 / componente C).
