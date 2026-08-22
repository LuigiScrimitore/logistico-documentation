"""
Stub minimale di `dbutils` per eseguire notebook Bronze in locale.

Implementa solo i metodi realmente usati dai notebook Bronze v3.0:
  - dbutils.widgets.dropdown(name, default, choices, label=None)
  - dbutils.widgets.text(name, default, label=None)
  - dbutils.widgets.get(name)
  - dbutils.fs.ls(path)
  - dbutils.notebook.exit(message)

Nessuna dipendenza da IPython o Databricks-connect: l'oggetto viene iniettato
direttamente nel namespace di esecuzione del notebook.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class NotebookExit(Exception):
    """Sollevata da dbutils.notebook.exit; catturata dal runner per non far fallire l'esecuzione."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class _Widgets:
    """Registry dei widget definiti dal notebook + valori override impostati dall'esterno."""

    def __init__(self, overrides: dict[str, str] | None = None):
        self._defaults: dict[str, str] = {}
        self._overrides: dict[str, str] = dict(overrides or {})

    def dropdown(self, name: str, default_value: str, choices: list[str], label: str | None = None):
        self._defaults[name] = default_value

    def text(self, name: str, default_value: str, label: str | None = None):
        self._defaults[name] = default_value

    def get(self, name: str) -> str:
        if name in self._overrides:
            return str(self._overrides[name])
        if name in self._defaults:
            return str(self._defaults[name])
        raise KeyError(f"Widget '{name}' non definito (e nessun override impostato).")

    def set_override(self, name: str, value: str) -> None:
        self._overrides[name] = str(value)


class _FileInfo:
    """Replica la shape di un FileInfo Databricks (name, path, size, modificationTime)."""

    __slots__ = ("name", "path", "size", "modificationTime", "isDir")

    def __init__(self, path: Path):
        self.path = path.as_uri() if path.is_absolute() else str(path)
        self.name = path.name + ("/" if path.is_dir() else "")
        self.isDir = path.is_dir()
        try:
            stat = path.stat()
            self.size = 0 if path.is_dir() else stat.st_size
            self.modificationTime = int(stat.st_mtime * 1000)
        except OSError:
            self.size = 0
            self.modificationTime = 0


class _Fs:
    """Implementa dbutils.fs.ls sul filesystem locale (path file:/// supportato)."""

    @staticmethod
    def ls(path: str) -> list[_FileInfo]:
        p = _to_local_path(path)
        if not p.exists():
            # Mimica Databricks: file_not_found e' una AnalysisException tipica
            raise FileNotFoundError(f"Path non trovato: {path}")
        if not p.is_dir():
            return [_FileInfo(p)]
        return [_FileInfo(child) for child in sorted(p.iterdir())]


class _Notebook:
    @staticmethod
    def exit(message: str) -> None:
        raise NotebookExit(message)


class DBUtilsStub:
    """Oggetto finale da iniettare come `dbutils` nel namespace del notebook."""

    def __init__(self, widget_overrides: dict[str, str] | None = None):
        self.widgets = _Widgets(widget_overrides)
        self.fs = _Fs()
        self.notebook = _Notebook()


def _to_local_path(path: str) -> Path:
    """Converte path file:///... o abfss://... in pathlib.Path locale.

    - file:///C:/... -> C:/...
    - abfss://...    -> non supportato (test locale legge da disco)
    - C:/...         -> as-is
    """
    if not isinstance(path, str):
        return Path(str(path))
    s = path.strip()
    if s.startswith("file:///"):
        return Path(s[len("file:///"):])
    if s.startswith("file://"):
        return Path(s[len("file://"):])
    if s.startswith("abfss://") or s.startswith("abfs://"):
        raise RuntimeError(
            f"Path remoto non supportato nel test locale: {path}\n"
            "Imposta il widget landing_base_path su file:/// (vedi run_notebook.py)."
        )
    return Path(s)
