"""
test_send_to_landing.py — Guardrail per il trasporto landing pluggable (KIT-01 / ADR-0023).

Copre il backend AzCopy (costruzione URL, mascheramento SAS, auth mode, comando) e il
riuso del piano di upload + il dry-run end-to-end. Nessuna dipendenza da Spark/Azure.
"""

import os
import sys

import pytest

# Lo script vive in scripts/sftp/ e importa send_to_sftp dallo stesso folder.
_SCRIPTS_SFTP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "sftp")
if _SCRIPTS_SFTP not in sys.path:
    sys.path.insert(0, _SCRIPTS_SFTP)

import send_to_landing as stl  # noqa: E402


# --------------------------------------------------------------------------- URL/SAS
def test_azcopy_dest_url_with_sas():
    cfg = stl.AzCopyConfig(dest_url="https://acct.blob.core.windows.net/cont", sas="?sig=ABC")
    url = stl.azcopy_dest_url(cfg, "/logistix-landing/t/2026/06/10/p.csv")
    assert url == "https://acct.blob.core.windows.net/cont/logistix-landing/t/2026/06/10/p.csv?sig=ABC"


def test_azcopy_dest_url_placeholder_when_missing():
    cfg = stl.AzCopyConfig()  # nessuna dest_url
    url = stl.azcopy_dest_url(cfg, "/a/b.csv")
    assert url == "<AZCOPY_DEST_URL>/a/b.csv"


def test_azcopy_dest_url_strips_double_slash():
    cfg = stl.AzCopyConfig(dest_url="https://acct.blob.core.windows.net/cont/")
    assert stl.azcopy_dest_url(cfg, "/a/b.csv") == "https://acct.blob.core.windows.net/cont/a/b.csv"


def test_mask_sas_hides_query():
    masked = stl._mask_sas("https://x/y.csv?sv=2024&sig=SECRET")
    assert "SECRET" not in masked
    assert masked == "https://x/y.csv?<SAS>"


def test_mask_sas_noop_without_query():
    assert stl._mask_sas("https://x/y.csv") == "https://x/y.csv"


# --------------------------------------------------------------------------- auth mode
def test_auth_mode_sas():
    assert stl.AzCopyConfig(sas="?sig=x").auth_mode() == "SAS"


def test_auth_mode_aad():
    assert stl.AzCopyConfig(auto_login_type="MSI").auth_mode() == "AAD/MSI"


def test_auth_mode_unconfigured():
    assert stl.AzCopyConfig().auth_mode() == "NON CONFIGURATA"


def test_config_from_env_adds_sas_question_mark(monkeypatch):
    monkeypatch.setenv("AZCOPY_SAS", "sv=2024&sig=x")  # senza '?'
    monkeypatch.setenv("AZCOPY_DEST_URL", "https://acct.blob.core.windows.net/cont")
    cfg = stl.AzCopyConfig.from_env()
    assert cfg.sas == "?sv=2024&sig=x"
    assert cfg.auth_mode() == "SAS"


# --------------------------------------------------------------------------- comando
def test_azcopy_command_shape():
    cfg = stl.AzCopyConfig(dest_url="https://acct.blob.core.windows.net/cont", sas="?sig=x")
    item = stl.UploadItem(local_path="/tmp/p.csv", remote_path="/sys/t/p.csv", size=10, system="sys")
    cmd = stl.azcopy_command(cfg, item)
    assert cmd[0:2] == ["azcopy", "copy"]
    assert cmd[-1] == "--overwrite=ifSourceNewer"
    assert cmd[3].endswith("?sig=x")


def test_default_remote_base():
    assert stl._default_remote_base("azcopy") == ""
    assert stl._default_remote_base("sftp")  # non vuoto (env o /data)


# --------------------------------------------------------------------------- piano + dry-run
@pytest.fixture()
def landing(tmp_path):
    d = tmp_path / "landing" / "logistix-landing" / "sto_tes_carichi" / "2026" / "06" / "10"
    d.mkdir(parents=True)
    (d / "part-0.csv").write_text("a;b;c\n")
    (d / "note.txt").write_text("escluso")  # non CSV/Parquet
    return tmp_path / "landing"


def test_plan_selects_only_supported_formats(landing):
    plan = stl.build_upload_plan(landing, "2026-06-10", "", layout="mirror")
    names = [os.path.basename(str(it.local_path)) for it in plan]
    assert names == ["part-0.csv"]  # note.txt escluso
    assert plan[0].remote_path == "/logistix-landing/sto_tes_carichi/2026/06/10/part-0.csv"


def test_dry_run_azcopy_returns_zero(landing, capsys):
    rc = stl.main(["--landing", str(landing), "--run-date", "2026-06-10"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "transport=azcopy" in out
    assert "azcopy copy" in out


def test_dry_run_sftp_returns_zero(landing, capsys):
    rc = stl.main(["--landing", str(landing), "--transport", "sftp", "--run-date", "2026-06-10"])
    assert rc == 0
    assert "DRY-RUN (sftp)" in capsys.readouterr().out


def test_send_azcopy_without_dest_fails_cleanly(landing, monkeypatch, capsys):
    monkeypatch.delenv("AZCOPY_DEST_URL", raising=False)
    monkeypatch.delenv("AZCOPY_SAS", raising=False)
    rc = stl.main(["--landing", str(landing), "--transport", "azcopy", "--send"])
    assert rc == 1
    assert "AZCOPY_DEST_URL" in capsys.readouterr().out
