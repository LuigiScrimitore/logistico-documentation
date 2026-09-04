# ADR-0025 · Provisioning del wheel `logistica_utils` su compute serverless

**Status**: accepted-interim (2026-09-01) — sblocca DBR-05; il canale *definitivo* (env-level) resta da validare

**Contesto**:
I job girano su **compute serverless** (ADR-0009) e i notebook importano la libreria condivisa `logistica_utils`
(multi-repo: repo separato, wheel dal Package Registry GitLab — DBR-05). Al primo run reale (smoke test
`logistica_carichi` DEV) il provisioning del wheel come **dipendenza d'ambiente** (`environments.dependencies`)
**non ha funzionato**, in due varianti, prima ancora di eseguire il notebook. Diagnosi completa: [[LL-020]].

**Alternative considerate**:
1. **Env-dependency da Package Registry GitLab** (`logistica_utils==1.0.4`): il serverless cerca su **PyPI
   pubblico** (nessun index privato configurato) → 404; e il registry GitLab è **on-prem, irraggiungibile** dal
   serverless Azure. Scartata.
2. **Env-dependency da wheel su Volume UC** (`/Volumes/.../x.whl`): il **build dell'environment** gira prima che il
   contesto UC/Volume sia disponibile → non raggiunge il Volume → build appeso ~3 min → `notebook command received
   after detach`, 3 tentativi falliti. Scartata (per ora).
3. **`%pip install` del wheel-on-Volume in prima cella del notebook** (scelto, interim): gira **a runtime**, con
   identità e accesso UC attivi → installa in modo affidabile. Validato: bronze + silver (con dati) → SUCCESS.
4. **Env-dependency da wheel su path Workspace via DAB `artifacts`** (target, da validare): il wheel entra nel
   bundle e viene referenziato per path Workspace nelle `environments.dependencies` → **una** config per tutti i
   task, **zero** `%pip` per-notebook. Non ancora testato.

**Decisione**:
- **Interim**: install del wheel via **`%pip install /Volumes/landing_dev/logistica/files/_wheels/<wheel>`** in
  **prima cella** di ogni notebook che importa la lib; `environments.dependencies: []`. Il wheel è **pubblicato sul
  Volume UC** (per ora upload manuale via `databricks fs cp`).
- **Packaging del wheel**: `install_requires=[]`; `pyspark`/`delta-spark` **solo in `extras_require`** (runtime
  forniti da Databricks). Vedi [[LL-020]].
- **Target**: validare l'alternativa **4** (DAB artifacts + path Workspace). Se regge, sostituisce il `%pip`
  per-notebook (che è lento e ripetuto su ~100 notebook) e diventa il provisioning definitivo → questo ADR passerà
  ad `accepted`.

**Conseguenze**:
+ **DBR-05 sbloccato**: la pipeline gira davvero su serverless (E2E validato bronze→silver su dati reali).
+ Nessuna dipendenza dal registry GitLab on-prem a runtime.
− **`%pip` per-notebook è interim**: overhead d'install per task e cella ripetuta ovunque → da rimpiazzare con env-level.
− **Pubblicazione del wheel sul Volume è manuale**: va **automatizzata** (step CI: `fs cp` del wheel sul Volume, o
  DAB artifacts) — legato a DBR-05 e alla scelta del canale definitivo.
− Applicato **solo all'area carichi** (rilascio a fasi, [[ADR-0017]]): le altre aree adottano lo stesso pattern
  quando il loro job viene attivato.

**Riferimenti**: [[LL-020]] (wheel su serverless: %pip non env) · [[LL-021]] (UC serverless: input_file_name /
path lazy) · [[ADR-0009]] (compute serverless) · [[ADR-0021]] (deploy DAB per-area) · [[LL-013]] (versione wheel
dal tag) · DBR-05 · `17_runbook_seed_landing_manuale.md` (smoke test / seed manuale).
