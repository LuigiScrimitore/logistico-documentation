"""Guardrail: selezione "come il legacy" dell'estrattore landing (ACT_9030).

La finestra sulle date (data ordine per le liste, data bolla per le pesate) perdeva i prelievi e i carichi
fatti più di 2 giorni dopo la data filtrata. La selezione legacy_flag / parent replica l'ODI in sola lettura:
questi test fissano la forma delle query senza bisogno di Oracle.

Esecuzione: pytest tests/test_extract_selection.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("yaml", reason="pyyaml non installato")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "landing_simulator"))
X = pytest.importorskip("extract_oracle_to_landing")

_, _, SYSTEMS = X.load_config(ROOT / "scripts" / "landing_simulator" / "config.yaml")
CTX = X.SelectionCtx(run_date=date(2026, 10, 16), stamp_from=date(2026, 10, 14))


def _q(system: str, table: str, ctx=CTX):
    spec = SYSTEMS[system]
    return X.build_query(spec, spec.tables[table], None, None, run_date=ctx.run_date, sel_ctx=ctx)


def test_flag_con_sospesi_limitati_e_timbro():
    sql, binds = _q("logistix", "sto_tes_carichi")
    assert "NVL(STCAR_DATA_ESTRAZIONE_DWH, 0) < 100000000000 AND STCAR_DATA_CARICO >= :pend_sto_tes_carichi" in sql
    assert "OR STCAR_DATA_ESTRAZIONE_DWH >= :stamp_from" in sql
    assert binds["stamp_from"] == 202610140000
    assert binds["pend_sto_tes_carichi"] == date(2026, 9, 16).toordinal() + 1721425   # run_date - 30 gg, giuliano


def test_righe_carico_dai_carichi_selezionati():
    sql, _ = _q("logistix", "sto_righe_carico")
    assert "(SRCAR_NRO_CARICO, SRCAR_COD_MAGAZZINO) IN (SELECT STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO" in sql
    assert "FROM STO_TES_CARICHI@{DBLINK}" in sql   # stesso db-link del sito


def test_liste_e_riepiloghi_dalle_bolle_emesse():
    sql, _ = _q("stat", "storico_riepiloghi")
    # stesso anno di preparazione: i numeri di riepilogo si riciclano negli anni (worklog 2026-10-16-05)
    assert ("(RPLPR_SITO, RPLPR_NRO_RIEPILOGO, RPLPR_COD_NEGOZIO, CASE WHEN RPLPR_DATA_PREPARAZ > 0 THEN "
            "TO_CHAR(TO_DATE(RPLPR_DATA_PREPARAZ, 'J'), 'YYYY') END) IN (SELECT LSPRL_SITO") in sql
    assert "(LSPRL_SITO, LSPRL_COD_NEGOZIO, LSPRL_NRO_BOLLA, LSPRL_DATA_BOLLA) IN (SELECT TEBO_SITO" in sql
    assert "(TEBO_STATO = 'E' AND TEBO_FLAG_ESTRAZIONE_DWH = 'N')" in sql
    assert "TEBO_DATA_ESTRAZIONE_DWH >= :stamp_from" in sql


def test_finestra_chiusa_senza_sospesi():
    ctx = X.SelectionCtx(run_date=date(2026, 10, 16), stamp_from=date(2026, 10, 12), stamp_to=date(2026, 10, 16))
    sql, binds = _q("logistix", "pesate", ctx)
    assert "PSP_DATA_ESTRAZIONE_DWH >= :stamp_from AND PSP_DATA_ESTRAZIONE_DWH < :stamp_to" in sql
    assert "NVL(" not in sql
    assert binds["stamp_to"] == 202610160000


def test_tabelle_senza_selezione_restano_a_finestra():
    spec = SYSTEMS["track"]
    sql, binds = X.build_query(spec, spec.tables["spedizioni"], None, None, lookback_days=3,
                               run_date=date(2026, 10, 16), sel_ctx=CTX)
    assert "SP_DATABOLLA >= :from_date" in sql and "stamp_from" not in binds


def test_pending_where_fuori_whitelist_rifiutata():
    t = X.TableSpec(name="x", mode="delta", columns=[], merge_keys=[], flag_column="F_X",
                    selection="legacy_flag", pending_where="F_X = 'N' OR 1=1")
    with pytest.raises(ValueError):
        X.selection_where(SYSTEMS["stat"], t, CTX, {})
