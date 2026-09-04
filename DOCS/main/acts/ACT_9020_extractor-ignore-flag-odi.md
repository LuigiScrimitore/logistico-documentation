# ACT_9020 · Extractor: opzione per ignorare il flag ODI sulle transazionali

**Status**: done
**Type**: fix
**Origin**: emerged
**fuori-sprint**: emergente
**Fase / Wave**: trasversale — Ingestion (landing simulator)
**Gg (stima)**: 0.5
**Blocco**: nessuno (locale)
**Created**: 2026-09-02   **Closed**: 2026-09-02   **Owner**: Francesco Foconi
**Dipende da**: —      **Blocca**: seed completo landing DEV (prep massa critica, worklog 2026-09-02-01)
**ADR collegate**: —      **OP collegati**: OP-08 (FULL vs DELTA), OP-31 (validazioni delta sorgente)

## Contesto e motivazione
L'extractor Oracle→CSV (`scripts/landing_simulator/extract_oracle_to_landing.py`) applica, per le tabelle
`mode: delta` con `flag_column` configurato, il filtro CDC dell'ODI legacy: `NVL(<flag>, 0) = 0`
(vedi `build_query`, ~riga 297). Il flag `*_DATA_ESTRAZIONE_DWH` marca i record **già consumati dall'ODI di
produzione**: in produzione questo lascia passare **solo i record non ancora estratti** — cioè, per una
fotografia storica, quasi nulla. Effetto: il **seed della landing DEV** con dati reali risulta
vuoto/parziale sulle transazionali, anche quando la finestra data conterrebbe righe.

Questo è **strutturale**, non un bug di dato (memoria `logistico-oracle-flag-estrazione-dwh`). Ad agosto era
stato aggirato **commentando a mano** i `flag_column` nel `config.yaml` (fragile: va ricordato di
ripristinarli, e cambia il file tracciato). Serve un interruttore pulito e non-distruttivo.

**Transazionali con flag ODI oggi** (10): `sto_tes_carichi` (STCAR_), `pesate` (PSP_), `tracciace178`
(CE178_), `dettaglio_carr` (DTCRL_), `cartellino` (CARTE_), `imbfmovim` (IMF_), `abb_tolti` (ABT_),
`storico_riepiloghi` (RPLPR_), `testate_bolle` (TEBO_), `storico_bolle` (BOL_).

## Obiettivo
Poter estrarre le transazionali **ignorando il flag ODI**, mantenendo la **finestra data** come filtro,
**senza modificare il `config.yaml`** e **senza cambiare il comportamento di default** (nessuna regressione
per CI/altri usi). Criterio di fatto:
- nuovo flag CLI `--ignore-odi-flag` (default OFF → comportamento identico ad oggi);
- con `--ignore-odi-flag` la clausola `NVL(<flag>,0)=0` **non** viene aggiunta; resta il filtro `from/to date`;
- log esplicito di quali tabelle hanno il flag ignorato;
- gestione del caso `imbfmovim` (nessun `date_column`): ignorando il flag resta **senza filtro** → warning
  chiaro di "lettura totale".

## Analisi tecnica
- `build_query(...)`: aggiungere parametro `ignore_odi_flag: bool = False`. Il filtro flag passa da
  `if table.flag_column:` a `if table.flag_column and not ignore_odi_flag:`.
- Warning "né data né flag → lettura totale": estendere la condizione a `(not table.flag_column or
  ignore_odi_flag)` così scatta anche quando il flag è presente ma ignorato e non c'è finestra data.
- Log `info` per audit quando un flag viene ignorato (nome tabella + colonna flag).
- CLI: `--ignore-odi-flag` (`action="store_true"`, default `False`), propagato alla chiamata `build_query`
  (~riga 490).
- **Non** si tocca `config.yaml`: i `flag_column` restano dichiarati (servono al comportamento di default).

## Sviluppo (diario)
- 2026-09-02 · Creata ACT. Diagnosi confermata su `config.yaml` (10 transazionali con flag). Scelto approccio
  opt-in via CLI invece del commento manuale del config.
- 2026-09-02 · Implementato in `extract_oracle_to_landing.py`: param `ignore_odi_flag` in `build_query`, flag
  CLI `--ignore-odi-flag`, log audit su flag ignorato, warning "lettura totale" esteso al caso flag-ignorato.
  Verifica dry-run OK (vedi sotto). Config invariato. Non ancora validato su dati reali (attende seed via VPN).
- 2026-09-02 · Esteso il wrapper `seed_landing_dev.ps1`: switch `-IgnoreOdiFlag` (propaga `--ignore-odi-flag`)
  + **auto-detect interprete Python** (`Resolve-PySelector`: preferisce `py -3.12` dove `py -3` è una versione
  senza oracledb, fallback `-3` → portabile, non rompe altre macchine). Dry-run wrapper OK.

## Verifica
- `--dry-run --ignore-odi-flag --tables pesate --sites lgcx`: la SQL stampata **non** contiene
  `NVL(PSP_DATA_ESTRAZIONE_DWH, 0) = 0` ma contiene il filtro su `PSP_DATABOLLA`.
- Senza il flag (default): la SQL **contiene** ancora `NVL(...)=0` (nessuna regressione).
- Estrazione reale di una fetta con `--ignore-odi-flag` restituisce righe > della stessa fetta senza flag.

## Esito
Modifica implementata in `scripts/landing_simulator/extract_oracle_to_landing.py` (non committata).
Verifica dry-run (2026-09-02, `py -3.12`):
- default: `... AND NVL(PSP_DATA_ESTRAZIONE_DWH, 0) = 0` (nessuna regressione);
- `--ignore-odi-flag`: `WHERE PSP_DATABOLLA >= :from AND <= :to` (niente NVL) + log "flag ODI ... IGNORATO";
- `imbfmovim` (no date_column) + `--ignore-odi-flag`: warning "lettura totale" corretto, `max-rows` fa da rete.

Validazione su **dati reali** (2026-09-02, VPN, finestra 2026-08-01..07, `lgcx/pesate`):
- default (con flag): **0 righe** (tutte già consumate dall'ODI di prod);
- `--ignore-odi-flag`: **1065 righe** (fotografia storica reale).
Diagnosi confermata: il flag CDC svuotava il seed storico. Obiettivo raggiunto.

Wrapper `seed_landing_dev.ps1` esteso con `-IgnoreOdiFlag` + auto-detect interprete Python.
File toccati: `scripts/landing_simulator/extract_oracle_to_landing.py`, `scripts/landing_simulator/seed_landing_dev.ps1`.
Commit: — (in attesa di push).

## Lezioni
- [[LL-024]] — Il filtro CDC dell'ODI non è adatto al seed storico: renderlo opt-in, non cablato nel config.
- Correlata: [[LL-022]] — seedando lo storico emerge il bug JDN su `DATA_SCADENZA` ([[ACT_9021]]).

## Follow-up
- Il wrapper `seed_landing_dev.ps1` potrebbe esporre lo stesso switch (`-IgnoreOdiFlag`) → eventuale ACT
  separata se serve.
