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
    return p.replace("../notebooks/", "") if p else None


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
