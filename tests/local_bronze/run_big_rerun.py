"""
Orchestratore BIG RE-RUN completo (22 siti), a sessione Spark singola.
Esegue la pipeline in ordine di dipendenza esplicito (l'ordine alfabetico dei
run_all_* romperebbe le dipendenze del prep). Siti = tutti i 22 attivi.

Fasi: BRONZE -> SILVER_DIM -> GOLD_DIM(LU_*) -> SILVER_CLEAN/INTERM -> SILVER_PREP
      -> GOLD_FACT -> GOLD_AGG.
Esclude notebook deprecati/JDBC.
"""
from __future__ import annotations
import json, logging, sys, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(REPO_ROOT / "lib" / "logistica_utils"))
sys.path.insert(0, str(HERE))

from dbutils_stub import DBUtilsStub, NotebookExit  # noqa: E402
from spark_session import build_spark, ensure_databases  # noqa: E402
from run_notebook import _install_fqn_rewriters, _file_uri  # noqa: E402

RUN_DATE = "2026-06-10"
SITI_22 = ("laix,lbvx,lcax,leax,lfax,lfmx,lfqx,lfsx,lfvx,lgax,lgcx,lgnx,"
           "lgqx,lgrx,lgsx,lgvx,lgzx,lonx,losx,lslx,lsmx,lsvx")
LANDING = "/workspace/data/landing"
WAREHOUSE = "/workspace/data/warehouse"

# Bronze: tutti tranne JDBC/deprecati (ordine irrilevante, leggono landing)
BRONZE_DENY = ("bronze_swap", "bronze_ordini_righe", "bronze_ordini_testate",
               "bronze_contratti_corrieri", "bronze_vettori_locale")

SILVER_DIM = [f"silver/dimensioni/silver_dim_{x}" for x in
              ("sito", "operatore", "corriere", "topografia", "pdv", "articolo", "fornitore")]
GOLD_DIM = [f"gold/dimensioni/gold_dim_{x}" for x in
            ("calendario", "sito", "operatore", "corriere", "topografia",
             "struttura_merceologica", "pdv", "articolo", "fornitore")]
SILVER_CLEAN = [
    "silver/carichi/silver_carichi_testate", "silver/carichi/silver_carichi_dettagli",
    "silver/carichi/silver_pesate", "silver/carichi/silver_traccia_ce178",
    "silver/giacenze/silver_catena_clean", "silver/giacenze/silver_catena_esterni_clean",
    "silver/giacenze/silver_catena_unificata", "silver/cdt_estr/silver_t_stock",
    "silver/prep_spedizioni/silver_storico_liste_clean", "silver/prep_spedizioni/silver_storico_bolle_clean",
    "silver/prep_spedizioni/silver_storico_liste_uniche", "silver/prep_spedizioni/silver_storico_bolle_uniche",
    "silver/prep_spedizioni/silver_prep_riepiloghi",
    "silver/trasporti/silver_spedizioni_clean", "silver/trasporti/silver_automezzi_clean",
    "silver/trasporti/silver_vettori_clean", "silver/trasporti/silver_ordini",
    "silver/cdt_estr/silver_t_vettori",
    "silver/tracciabilita/silver_tracciabilita_lotto",
    "silver/tracciabilita/silver_sessione_carrellista", "silver/tracciabilita/silver_missione_carrellista",
]
SILVER_PREP = [
    "silver/carichi/silver_prep_carico",
    "silver/giacenze/silver_prep_giacenze", "silver/giacenze/silver_giacenze_aggregata",
    "silver/prep_spedizioni/silver_prep_prep_sped", "silver/prep_spedizioni/silver_prep_turno_prep_sito",
    "silver/trasporti/silver_prep_trasporto", "silver/trasporti/silver_prep_ordini",
]

GOLD_FACT = [
    "gold/carichi/gold_f_carico", "gold/giacenze/gold_f_giacenze_daily",
    "gold/prep_spedizioni/gold_f_prep_sped", "gold/prep_spedizioni/gold_f_turno_prep_sito",
    "gold/trasporti/gold_f_trasporto", "gold/trasporti/gold_f_ordini",
    "gold/carrellisti/gold_f_movimentazione_carrellisti", "gold/tracciabilita/gold_f_tracciabilita_lotti",
]
GOLD_AGG = [f"gold/aggregati/{x}" for x in
            ("gold_dm_giacenze_monthly", "gold_dm_turno_prep_sito", "gold_a_inbound_mensile",
             "gold_a_outbound_mensile", "gold_a_produttivita_mensile", "gold_a_stock_mensile")]


def run_one(nb_path, spark, landing_uri):
    # Isola lo stato di sessione tra notebook: i notebook idempotenti settano
    # partitionOverwriteMode=dynamic, che persisterebbe nella sessione condivisa e
    # romperebbe i write con overwriteSchema dei notebook successivi. Reset a static.
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "static")
    # full_refresh=true: il big re-run e' un rebuild completo del giorno. Evita che i notebook
    # "uniche"/prep prendano il path incrementale degenere (tutta la clean con stesso
    # _silver_load_date -> join+cache dell'intero dataset -> spill enorme). I notebook senza
    # widget full_refresh ignorano l'override.
    overrides = {"env": "dev", "run_date": RUN_DATE, "landing_base_path": landing_uri,
                 "file_format": "csv", "siti": SITI_22, "full_refresh": "true"}
    dbutils = DBUtilsStub(widget_overrides=overrides)
    g = {"__name__": "__main__", "__file__": str(nb_path), "spark": spark,
         "dbutils": dbutils, "sc": spark.sparkContext}
    start = time.time()
    res = {"nb": str(nb_path.relative_to(REPO_ROOT)), "status": "?", "err": None, "s": 0.0}
    try:
        exec(compile(nb_path.read_text(encoding="utf-8-sig"), str(nb_path), "exec"), g)
        res["status"] = "OK"
    except NotebookExit as e:
        res["status"] = "OK"; res["err"] = f"exit({e.message!r})"
    except Exception as e:
        res["status"] = "FAIL"; res["err"] = str(e)[:300]; res["tb"] = traceback.format_exc()
    res["s"] = round(time.time() - start, 1)
    return res


def main():
    global RUN_DATE
    # --run-date YYYY-MM-DD: override del giorno (default 2026-06-10). Per il test incrementale
    # del nuovo giorno passare 2026-06-11. --only FASE1,FASE2: esegue solo quelle fasi.
    if "--run-date" in sys.argv:
        RUN_DATE = sys.argv[sys.argv.index("--run-date") + 1]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    logging.basicConfig(level=logging.WARNING)
    spark = build_spark(WAREHOUSE, app_name="big-rerun")
    ensure_databases(spark)
    _install_fqn_rewriters(spark)
    landing_uri = _file_uri(Path(LANDING))

    bronze = [p for p in sorted((REPO_ROOT / "notebooks" / "bronze").rglob("bronze_*.py"))
              if "__pycache__" not in p.parts and not any(d in p.name for d in BRONZE_DENY)]
    skip_bronze = "--skip-bronze" in sys.argv
    phases = [
        ("BRONZE", [] if skip_bronze else bronze),
        ("SILVER_DIM", [REPO_ROOT / "notebooks" / f"{x}.py" for x in SILVER_DIM]),
        ("GOLD_DIM", [REPO_ROOT / "notebooks" / f"{x}.py" for x in GOLD_DIM]),
        ("SILVER_CLEAN", [REPO_ROOT / "notebooks" / f"{x}.py" for x in SILVER_CLEAN]),
        ("SILVER_PREP", [REPO_ROOT / "notebooks" / f"{x}.py" for x in SILVER_PREP]),
        ("GOLD_FACT", [REPO_ROOT / "notebooks" / f"{x}.py" for x in GOLD_FACT]),
        ("GOLD_AGG", [REPO_ROOT / "notebooks" / f"{x}.py" for x in GOLD_AGG]),
    ]
    if only:
        phases = [(p, nbs) for p, nbs in phases if p in only]
    results = []
    for phase, nbs in phases:
        print(f"\n===== FASE {phase} ({len(nbs)} notebook) (run_date={RUN_DATE}) =====", flush=True)
        for nb in nbs:
            if not nb.exists():
                print(f"  [MISS] {nb.name}", flush=True); continue
            r = run_one(nb, spark, landing_uri); r["phase"] = phase; results.append(r)
            tag = "OK " if r["status"] == "OK" else "FAIL"
            print(f"  [{tag}] {nb.name} ({r['s']}s){' - '+r['err'] if r['err'] else ''}", flush=True)

    ok = sum(1 for r in results if r["status"] == "OK")
    fail = [r for r in results if r["status"] == "FAIL"]
    print(f"\n===== RIEPILOGO BIG RE-RUN: {ok} OK | {len(fail)} FAIL | {len(results)} tot =====", flush=True)
    for r in fail:
        print(f"  FAIL {r['nb']}: {r['err']}", flush=True)
    Path(f"{WAREHOUSE}/big_rerun_report.json").write_text(json.dumps(results, indent=2, default=str))
    spark.stop()
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
