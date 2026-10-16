"""Guardrail: i workflow (DAB) sono allineati ai notebook su disco? — ACT_9014

Questi test esistono perché il disallineamento si era già verificato: i YML puntavano a
6 notebook rimossi come rami secchi (RS-01..08) e ~50 notebook reali non erano orchestrati.
`databricks bundle validate` **non** verifica l'esistenza dei notebook, quindi il deploy
passava e i run fallivano a runtime. Questi test intercettano la regressione in locale/CI.

Esecuzione: pytest tests/test_workflows_alignment.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="pyyaml non installato")

ROOT = Path(__file__).resolve().parents[1]
WF_DIR = ROOT / "workflows"
NB_DIR = ROOT / "notebooks"

# Notebook deliberatamente NON orchestrati — motivo in DOCS/main/acts/ACT_9014_*.md.
# Aggiungere qui (con motivo) solo dopo una decisione consapevole.
ALLOWED_ORPHANS = {
    "bronze/trasporti/bronze_swap",              # JDBC deprecato (deny list del runner)
    "bronze/trasporti/bronze_vettori_locale",    # deny list del runner
    "silver/trasporti/silver_trasporti",         # superato da silver_prep_trasporto
    "silver/cdt_estr/silver_t_trasp_mtv",        # non nella catena rebuilt-from-raw
    "silver/prep_spedizioni/silver_prep_bolle",  # non nel runner validato
    "gold/giacenze/gold_f_giacenze_monthly",     # aggregato mensile via gold_dm_giacenze_monthly
}


def _workflows():
    files = sorted(WF_DIR.glob("*.yml"))
    assert files, f"nessun workflow trovato in {WF_DIR}"
    return files


def _load(path: Path) -> dict:
    """Restituisce il dict del job. Formato DAB (ADR-0021): `resources.jobs.<key>`
    (un job per file). Retrocompat con il vecchio formato "job nudo" (top-level)."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    jobs = (doc.get("resources") or {}).get("jobs") or {}
    return next(iter(jobs.values())) if jobs else doc


def _tasks(job: dict) -> list[dict]:
    return job.get("tasks") or []


def _nb_rel(task: dict) -> str | None:
    nt = task.get("notebook_task") or {}
    p = nt.get("notebook_path")
    if not p:
        return None
    rel = p.replace("../notebooks/", "")
    return rel[:-3] if rel.endswith(".py") else rel   # DAB vuole .py nel path; il test lavora senza


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_yaml_valido_e_non_vuoto(wf: Path):
    """Un job senza task non è valido per l'API Jobs: farebbe fallire il deploy."""
    job = _load(wf)
    tasks = _tasks(job)
    assert tasks, f"{wf.name}: nessun task definito"
    keys = [t["task_key"] for t in tasks]
    assert len(keys) == len(set(keys)), f"{wf.name}: task_key duplicati"


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_notebook_path_esistono(wf: Path):
    """Ogni notebook_path dichiarato deve esistere: `bundle validate` non lo controlla."""
    missing = []
    for t in _tasks(_load(wf)):
        rel = _nb_rel(t)
        if rel and not (NB_DIR / f"{rel}.py").is_file():
            missing.append(f"{t['task_key']} -> {rel}")
    assert not missing, f"{wf.name}: notebook inesistenti: {missing}"


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_dipendenze_coerenti_e_senza_cicli(wf: Path):
    job = _load(wf)
    tasks = _tasks(job)
    keys = {t["task_key"] for t in tasks}
    graph, broken = {}, []
    for t in tasks:
        deps = [d["task_key"] for d in (t.get("depends_on") or [])]
        graph[t["task_key"]] = deps
        broken += [f"{t['task_key']} -> {d}" for d in deps if d not in keys]
    assert not broken, f"{wf.name}: depends_on verso task inesistenti: {broken}"

    state: dict[str, int] = {}

    def has_cycle(node: str) -> bool:
        state[node] = 1
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                return True
            if state.get(nxt, 0) == 0 and has_cycle(nxt):
                return True
        state[node] = 2
        return False

    cycles = [k for k in graph if state.get(k, 0) == 0 and has_cycle(k)]
    assert not cycles, f"{wf.name}: ciclo nel DAG (coinvolge {cycles})"


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_compute_serverless(wf: Path):
    """ADR-0009: job cluster serverless. Nessun cluster classico, environment_key su ogni task."""
    job = _load(wf)
    assert "job_clusters" not in job, f"{wf.name}: job_clusters presente (atteso serverless)"
    for t in _tasks(job):
        assert "job_cluster_key" not in t, f"{wf.name}/{t['task_key']}: job_cluster_key presente"
        assert "environment_key" in t, f"{wf.name}/{t['task_key']}: environment_key mancante"


def test_nessun_notebook_orfano():
    """Ogni notebook (esclusi templates e allow-list) è orchestrato da almeno un workflow."""
    orchestrated = {
        rel
        for wf in _workflows()
        for t in _tasks(_load(wf))
        if (rel := _nb_rel(t))
    }
    on_disk = {
        str(p.relative_to(NB_DIR)).replace(os.sep, "/")[: -len(".py")]
        for p in NB_DIR.rglob("*.py")
        if "templates" not in p.parts
    }
    orphans = sorted(on_disk - orchestrated - ALLOWED_ORPHANS)
    assert not orphans, (
        "notebook non orchestrati da alcun workflow: "
        f"{orphans}. Se è voluto, aggiungerli ad ALLOWED_ORPHANS con il motivo."
    )


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_job_parameters_referenziati_sono_dichiarati(wf: Path):
    """Ogni `{{job.parameters.X}}` usato dai task DEVE essere dichiarato nei `parameters` del job.
    `bundle validate` NON lo verifica, ma l'API jobs/create lo rifiuta (400 INVALID_PARAMETER_VALUE)
    al deploy — quindi lo intercettiamo qui in locale (ACT_9018, deploy_dev)."""
    import re

    job = _load(wf)
    declared = {p["name"] for p in (job.get("parameters") or [])}
    used = set(re.findall(r"\{\{job\.parameters\.([a-zA-Z_]+)\}\}", wf.read_text(encoding="utf-8")))
    missing = sorted(used - declared)
    assert not missing, f"{wf.name}: job.parameters usati ma non dichiarati nel job: {missing}"


def test_parametri_task_esistono_come_widget():
    """Un base_parameter senza widget corrispondente sarebbe silenziosamente ignorato."""
    import re

    problems = []
    for wf in _workflows():
        for t in _tasks(_load(wf)):
            rel = _nb_rel(t)
            if not rel:
                continue
            nb = NB_DIR / f"{rel}.py"
            if not nb.is_file():
                continue  # coperto da test_notebook_path_esistono
            src = nb.read_text(encoding="utf-8")
            widgets = set(re.findall(r'widgets\.(?:text|dropdown)\("([a-zA-Z_]+)"', src))
            passed = set((t.get("notebook_task") or {}).get("base_parameters") or {})
            extra = passed - widgets
            if extra:
                problems.append(f"{wf.name}/{t['task_key']}: parametri senza widget {sorted(extra)}")
    assert not problems, problems


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_yaml_senza_chiavi_duplicate(wf: Path):
    """Con una chiave duplicata (es. due `depends_on` nello stesso task) YAML tiene l'ultima e
    `bundle validate` non avvisa: in datamart si era persa una dipendenza (LL-038)."""

    class _Loader(yaml.SafeLoader):
        pass

    dup: list[str] = []

    def _mapping(loader, node, deep=False):
        seen = set()
        for k, _v in node.value:
            key = loader.construct_object(k, deep=deep)
            if key in seen:
                dup.append(f"'{key}' riga {k.start_mark.line + 1}")
            seen.add(key)
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    _Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)
    yaml.load(wf.read_text(encoding="utf-8"), Loader=_Loader)
    assert not dup, f"{wf.name}: chiavi duplicate {dup}"


def _nb_tables(nb: Path) -> tuple[set[str], set[str]]:
    """(tabelle lette, tabelle scritte) di un notebook, ricavate dalle costanti stringa
    (`X_CATALOG = get_catalog("silver", env)`, `TARGET_TABLE = f"{...}.schema.tab"`, `SRC_* = ...`)
    e dai riferimenti `f"{CATALOG}.schema.tab"` inline. Nomi in minuscolo, catalogo `<layer>_dev`."""
    import re

    src = nb.read_text(encoding="utf-8")
    env: dict[str, str] = {}
    for m in re.finditer(r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+?)\s*(?:#.*)?$', src, re.M):
        k, v = m.group(1), m.group(2)
        cat = re.match(r'get_catalog\(\s*"(\w+)"', v)
        if cat:
            env[k] = f"{cat.group(1)}_dev"
            continue
        lit = re.match(r'^f?"([^"]*)"$', v)
        if lit:
            val = lit.group(1)
            for _ in range(3):
                val = re.sub(r"\{([A-Z_][A-Z0-9_]*)\}", lambda x: env.get(x.group(1), x.group(0)), val)
            env[k] = val
    is_table = re.compile(r"^(bronze|silver|gold)_dev\.\w+\.\w+$")
    write_vars = {"TARGET_TABLE", "FULL_TARGET", "TARGET_NAME"}
    writes = {v.lower() for k, v in env.items() if k in write_vars and is_table.match(v)}
    reads = {v.lower() for k, v in env.items() if k not in write_vars and is_table.match(v)}

    def _res(part: str) -> str:
        return env.get(part.strip("{}"), part) if part.startswith("{") else part

    for m in re.finditer(r'f?"(\{\w+\}|\w+_dev)\.(\{\w+\}|\w+)\.(\w+)"', src):
        t = f"{_res(m.group(1))}.{_res(m.group(2))}.{m.group(3)}".lower()
        if is_table.match(t) and t not in writes:
            reads.add(t)
    return reads, writes


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_task_parte_dopo_chi_scrive_i_suoi_input(wf: Path):
    """Se un task legge una tabella scritta da un altro task dello stesso job, quel task deve
    essere tra i suoi antenati. Altrimenti parte prima, legge dati vecchi ed esce verde:
    F_PREP_SPED è rimasta ferma al 02/09 per sei settimane così (LL-038)."""
    tasks = {t["task_key"]: t for t in _tasks(_load(wf))}
    io = {}
    for k, t in tasks.items():
        rel = _nb_rel(t)
        if rel and (NB_DIR / f"{rel}.py").is_file():
            io[k] = _nb_tables(NB_DIR / f"{rel}.py")
    producers: dict[str, list[str]] = {}
    for k, (_r, w) in io.items():
        for tab in w:
            producers.setdefault(tab, []).append(k)

    def ancestors(k: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        for d in tasks[k].get("depends_on") or []:
            if d["task_key"] not in seen:
                seen.add(d["task_key"])
                ancestors(d["task_key"], seen)
        return seen

    missing = []
    for k, (reads, _w) in io.items():
        anc = ancestors(k)
        for tab in sorted(reads):
            missing += [f"{k} legge {tab} scritta da {p}" for p in producers.get(tab, []) if p != k and p not in anc]
    assert not missing, f"{wf.name}: depends_on mancanti: {missing}"


@pytest.mark.parametrize("wf", _workflows(), ids=lambda p: p.name)
def test_task_che_scrivono_la_stessa_tabella_sono_ordinati(wf: Path):
    """Due task dello stesso job che scrivono la stessa tabella devono essere ordinati (uno antenato
    dell'altro): in parallelo Delta rifiuta il secondo commit (ConcurrentAppendException) e il retry
    nasconde il problema. Caso reale: gold_late_arriving_handler e gold_f_carico su F_CARICO (LL-038)."""
    tasks = {t["task_key"]: t for t in _tasks(_load(wf))}
    writers: dict[str, list[str]] = {}
    for k, t in tasks.items():
        rel = _nb_rel(t)
        if rel and (NB_DIR / f"{rel}.py").is_file():
            for tab in _nb_tables(NB_DIR / f"{rel}.py")[1]:
                writers.setdefault(tab, []).append(k)

    def ancestors(k: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        for d in tasks[k].get("depends_on") or []:
            if d["task_key"] not in seen:
                seen.add(d["task_key"])
                ancestors(d["task_key"], seen)
        return seen

    paralleli = []
    for tab, ks in sorted(writers.items()):
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                if a not in ancestors(b) and b not in ancestors(a):
                    paralleli.append(f"{a} e {b} scrivono {tab}")
    assert not paralleli, f"{wf.name}: scritture parallele sulla stessa tabella: {paralleli}"
