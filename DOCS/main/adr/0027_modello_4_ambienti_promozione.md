# ADR-0027 · Modello a 4 ambienti per maturità (sandbox → dev → stage → prod) con promozione a gate

**Status**: proposta (2026-09-23)

**Contesto**:
Oggi il bundle DAB ha **due soli target**: `dev` (sandbox personali in home utente — [[ACT_9022]]/[[LL-023]];
oppure deploy condiviso via CI/MI) e `prod`. Non esiste un livello **intermedio** in cui un flusso, una volta
verde, giri per alcuni giorni sotto **monitoraggio + data quality** prima di essere promosso in produzione.
Serve inoltre distinguere lo **sviluppo personale volatile** (dove ognuno rompe e ricostruisce di continuo)
dal **dev condiviso** (dove si verifica che una patch sia stabile senza pestare i piedi agli altri).

Il modello deve essere coerente con:
- **ADR-0004** (naming catalog `<layer>_dev`/`_prod`, con `_stage` "previsto ma non configurato");
- **ADR-0017** (rilascio a fasi, no big-bang) e **ADR-0021** (deploy DAB pipeline per-area);
- **ADR-0022** (auth CI = Managed Identity **unica**, confermata: un solo set `[dev <mi>] logistica_*`);
- **[[LL-030]]**: il prefisso `[dev <identità>]` è lo **standard dei nomi job** e va mantenuto; i nomi
  canonici senza prefisso (`mode:production`) vanno usati **solo** per ambienti realmente di rilascio,
  **non** come workaround anti-duplicati sul dev; il `root_path` per identità deve restare **stabile**.

**Vincolo di dominio (il "perché conta")**: un processo (es. `F_CARICO`) non è "pronto" quando compila,
ma quando **quadra** rispetto al legacy CDT_DW e **mantiene i limiti di certifica nel tempo**. Il modello a
ambienti deve rendere esplicita questa **scala di maturità**, non solo separare dev da prod.

**Alternative considerate**:
1. **2 ambienti (dev/prod)** — com'è oggi. Semplice, ma nessuna pre-produzione: si promuove in prod un
   flusso verde "una volta", senza una finestra di osservazione su stabilità/DQ nel tempo. Rischio di
   certificare in prod ciò che non ha mai girato N giorni consecutivi verde. **Scartata.**
2. **3 ambienti (dev/stage/prod)** — introduce la pre-prod ma **non** distingue sviluppo personale da dev
   condiviso: gli sviluppatori deployano sullo stesso ambiente condiviso mentre sperimentano, con
   interferenze reciproche e dati instabili. **Scartata.**
3. **4 ambienti (sandbox/dev/stage/prod)** — separa lo sviluppo volatile (sandbox per-utente) dal dev
   condiviso e aggiunge la pre-prod osservata. Più infra e disciplina di promozione, ma allineato al
   dominio (scala di maturità) e agli ADR esistenti. **Scelta.**

**Decisione**:
Adottare un modello a **4 ambienti per maturità**, con promozione **solo in avanti** e a **gate** crescenti.

| Ambiente | Scopo | Chi/come deploya | DAB | Catalog (layer) | Naming job |
|---|---|---|---|---|---|
| **sandbox** | sviluppo evolutive, patch, bugfix; sperimentazione volatile | ogni dev **da locale** | `mode: development`, root_path in **home** ([[LL-023]]) | `<layer>_dev` | `[dev <utente>]` |
| **dev** | verificare che una patch **verde** sia stabile in ambiente condiviso | **CI GitLab / MI** | `mode: development`, root_path **condiviso stabile** | `<layer>_dev` | `[dev <mi>]` |
| **stage** | pre-produzione: versione **stabile e completa** in osservazione (monitoraggio + DQ) per N giorni | **CI GitLab / MI**, su promozione | `mode: production` + `name_prefix` | `<layer>_stage` (ADR-0004) | **`[stage] logistica_*`** |
| **prod** | processo **completo, stabile e certificato** | CI su **tag** + gate manuale | `mode: production` | `<layer>_prod` | canonico (`logistica_*`) |

**Naming job stage (deciso)**: il target DAB `stage` usa **`mode: production`** (schedule **attivi** per la
finestra di osservazione, semantica di rilascio — non `mode:development` che pausa gli schedule e aggiunge
convenienze da sandbox) + preset **`name_prefix: "[stage] "`** → job **`[stage] logistica_*`**. Così è
distinto da dev (`[dev <identità>]`) e da prod (canonico `logistica_*`): **nessuna collisione anche a
workspace condiviso**. Coerente con [[LL-030]] (il canonico senza prefisso resta riservato a **prod**; stage
ha un prefisso esplicito di ambiente). Da validare in fase implementativa che `name_prefix` sia applicato
sotto `mode: production` (`databricks bundle validate --target stage`).

**Scala di promozione (gate)** — esempio `F_CARICO`:
1. **sandbox → dev**: il processo è **verde** end-to-end (bronze→silver→gold, niente errori). Si promuove
   la patch via CI GitLab (l'attuale flusso `promote_to_gitlab.py` + `deploy_dev`).
2. **dev → stage**: il processo è **funzionalmente completo e quadrato** vs CDT_DW (entro le tolleranze di
   certifica). Si promuove in stage, dove **gira per N giorni** sotto `dq_gate` + monitoraggio.
3. **stage → prod**: dopo la finestra di osservazione, se la pipeline è **sempre verde** e **mantiene i
   limiti di certifica del dato**, si promuove in prod (tag + gate manuale).

I gate 2 e 3 si appoggiano al framework DQ/acceptance interno ([[ADR-0014]], OP-21) e ai criteri di
accettazione parallel-run (OP-24). La durata "N giorni" è **per-caso** (dipende dalla criticità/volatilità
del flusso), non un valore fisso.

**Conseguenze**:
+ Scala di maturità esplicita: in prod arriva solo ciò che ha **dimostrato stabilità nel tempo**, non solo
  "verde una volta". Coerente con la certifica vs CDT_DW e con il rilascio a fasi (ADR-0017).
+ Sandbox isolate: lo sviluppo volatile non destabilizza il dev condiviso.
+ Migrazione tra ambienti = cambio del **solo suffisso catalog** (`_dev`→`_stage`→`_prod`, ADR-0004,
  `_CATALOG_MAP`), più il target DAB.
− **Nuova infra Terraform**: creare i catalog/schemi/Volume/grant `_stage` (oggi non esistono) — segue
  ACT dedicata lato `infrastructure`.
− **Nuovo target DAB `stage`** nel `databricks.yml` (oltre a dev/prod) + estensione del tooling di
  promozione (`promote_to_gitlab.py` / regole CI dev→stage→prod).
− **Configurazione stage**: da realizzare con **[[ACT_9028]]** (catalog `_stage` via Terraform + target DAB
  `stage` con naming `[stage]` + regole di promozione dev→stage).
− **Punti aperti da risolvere in fase implementativa** (non decisi qui):
  - **Topologia workspace**: dev/stage/prod nello **stesso** workspace UC (separazione via catalog `_dev`/
    `_stage`/`_prod` + prefissi job) o su **workspace distinti** (impatta `DATABRICKS_HOST_*` e la CI)?
    Il naming `[stage]`/`[dev …]`/canonico regge in entrambi i casi; la scelta è su isolamento/costi.
  - **Sandbox vs dev sullo stesso catalog `_dev`**: definire se i sandbox scrivono su schemi/percorsi
    isolati per-utente o condividono i dati dev (rischio di clobber). Coerente con LL-030 lato *job*
    (identità distinte), da decidere lato *dati*.
  - **Auth CI per stage/prod**: MI unica anche per stage? (dev già confermato MI unica, ADR-0022.)
− Più disciplina operativa: la promozione diventa un processo con evidenze (DQ verde N giorni, quadratura),
  da formalizzare nel processo di go-live (OP-25) e nel cutover plan (OP-24).

**Riferimenti**:
- Estende: **ADR-0004** (naming ambienti, `_stage` ora definito come ambiente reale). Collegate: ADR-0014
  (DQ interni), ADR-0016 (multi-repo), ADR-0017 (rilascio a fasi), ADR-0021 (deploy per-area),
  ADR-0022 (auth MI). Lezioni: [[LL-023]] (root_path home sandbox), [[LL-030]] (naming `[dev <identità>]`).
- Origine: **OP-INF-3** (`05_open_points.md`) · anticipato da **ACT_9022**.
- Doc architetturali: `10_piano_migrazione_databricks.md` (§ambienti/catalog), `14_release_kit.md` (gate go-live).
- Implementazione (follow-up): **[[ACT_9028]]** — catalog `_stage` (Terraform) + target DAB `stage` (`databricks.yml`, naming `[stage]`) + regole di promozione dev→stage.
