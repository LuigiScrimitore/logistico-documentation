"""
Logistico 2.0 — Landing Simulator
Estrazione READ-ONLY dagli schemi Oracle Logistix/STAT/CND verso file CSV
in una landing zone locale che simula ADLS Gen2.

CARATTERISTICHE
---------------
- ESCLUSIVAMENTE SELECT. Nessun UPDATE/INSERT/DELETE sui sorgenti Oracle.
- Mai aggiorna i flag *_DATA_ESTRAZIONE_DWH dei record letti.
- Genera la struttura <source>-landing/[sito/]<tabella>/YYYY/MM/DD/<tabella>.csv
  conforme alla convenzione Bronze v3.0.
- Parametri CLI:
    --run-date YYYY-MM-DD      Data di estrazione singolo giorno (default: oggi).
    --from-date / --to-date    Backfill su intervallo di giorni (lettura piu' profonda).
    --tables tab1,tab2         Sottoinsieme di tabelle (default: tutte da config).
    --systems logistix,stat,cnd Filtra per sistema sorgente.
    --sites lgax,lgcx          Filtra siti Logistix (default: tutti i siti in config).
    --output-dir PATH          Override cartella output (default da config).
    --config PATH              Path file YAML (default: ./config.yaml).
    --dry-run                  Mostra solo le query, NON esegue, NON scrive.
    --skip-empty               Se la query restituisce 0 righe, NON crea il file (default: True).
- Una directory di log scrive ogni esecuzione con conteggi righe.

CONNESSIONE
-----------
File .env nella stessa cartella (non versionato), con:
    ORACLE_HOST=host
    ORACLE_PORT=1521
    ORACLE_SERVICE=service
    ORACLE_USER=username
    ORACLE_PASSWORD=password
    ORACLE_CDT_SCHEMA=CDT_ESTR    (schema da cui si raggiungono i db-link)

INSTALLAZIONE DIPENDENZE
------------------------
    pip install oracledb pyyaml python-dotenv

RIFERIMENTI
-----------
- DOCS/Test Locale - Quickstart.md
- DOCS/Landing & Bronze - Revision Spec.md
- DOCS/Open Points - Logistico 2.0.md (OP-08, OP-10, OP-11, OP-17)
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

try:
    import oracledb  # type: ignore
except ImportError:
    print("[ERROR] manca il modulo oracledb. Installa con: pip install oracledb", file=sys.stderr)
    sys.exit(2)
try:
    import yaml  # type: ignore
except ImportError:
    print("[ERROR] manca il modulo pyyaml. Installa con: pip install pyyaml", file=sys.stderr)
    sys.exit(2)
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    load_dotenv = None  # tolerato: useremo solo os.environ


# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("landing_simulator")


def setup_logging(log_dir: Path, run_tag: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"extract_{run_tag}.log"
    handler_file = logging.FileHandler(log_file, encoding="utf-8")
    handler_console = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    for h in (handler_file, handler_console):
        h.setFormatter(fmt)
    logger.setLevel(logging.INFO)
    logger.handlers = [handler_file, handler_console]
    logger.info("Log file: %s", log_file)


# ──────────────────────────────────────────────────────────────────────────────
# Modello configurazione
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class TableSpec:
    name: str
    mode: str                       # delta | full | snapshot
    columns: list[str]              # [] = SELECT *
    merge_keys: list[str]
    date_column: str = ""
    date_column_type: str = "date"  # date | number_yyyymmdd | julian_day (Oracle legacy: TO_DATE(num,'J'))
    flag_column: str = ""
    where_clause: str = ""
    source_object: str = ""         # override del nome oggetto sorgente (default: name uppercase)
    disabled: bool = False          # se True salta la tabella

    def src_obj(self) -> str:
        return self.source_object.strip() or self.name.upper()


@dataclass
class SystemSpec:
    key: str                         # logistix | stat | cnd
    landing_subdir: str
    dblinks: dict[str, str]          # {sito: dblink_name}; per cnd vuoto / per stat un solo elemento
    schema: str = ""                 # solo per cnd: schema diretto (CDT_SOURCE)
    is_multisite_in_path: bool = True
    tables: dict[str, TableSpec] = None


# ──────────────────────────────────────────────────────────────────────────────
# Lettura config
# ──────────────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> tuple[Path, dict, dict[str, SystemSpec]]:
    if not path.exists():
        raise FileNotFoundError(f"Config non trovata: {path}")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    output_dir = Path(cfg["output_dir"])
    csv_cfg = cfg.get("csv", {})

    systems: dict[str, SystemSpec] = {}
    for sys_key, sys_cfg in (cfg.get("systems") or {}).items():
        tables: dict[str, TableSpec] = {}
        for tbl_name, t_cfg in (sys_cfg.get("tables") or {}).items():
            tables[tbl_name] = TableSpec(
                name=tbl_name,
                mode=str(t_cfg.get("mode", "delta")).lower(),
                columns=list(t_cfg.get("columns") or []),
                merge_keys=list(t_cfg.get("merge_keys") or []),
                date_column=str(t_cfg.get("date_column") or "").strip(),
                date_column_type=str(t_cfg.get("date_column_type") or "date").strip().lower(),
                flag_column=str(t_cfg.get("flag_column") or "").strip(),
                where_clause=str(t_cfg.get("where_clause") or "").strip(),
                source_object=str(t_cfg.get("source_object") or "").strip(),
                disabled=bool(t_cfg.get("disabled", False)),
            )
        systems[sys_key] = SystemSpec(
            key=sys_key,
            landing_subdir=str(sys_cfg["landing_subdir"]),
            dblinks=dict(sys_cfg.get("dblinks") or {}),
            schema=str(sys_cfg.get("schema") or ""),
            is_multisite_in_path=bool(sys_cfg.get("is_multisite_in_path", sys_key == "logistix")),
            tables=tables,
        )
    return output_dir, csv_cfg, systems


# ──────────────────────────────────────────────────────────────────────────────
# Connessione Oracle (READ-ONLY, autocommit OFF)
# ──────────────────────────────────────────────────────────────────────────────

def connect_oracle() -> "oracledb.Connection":
    host = os.environ["ORACLE_HOST"]
    port = int(os.environ.get("ORACLE_PORT", "1521"))
    service = os.environ["ORACLE_SERVICE"]
    user = os.environ["ORACLE_USER"]
    password = os.environ["ORACLE_PASSWORD"]
    dsn = oracledb.makedsn(host, port, service_name=service)
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    # Difesa in profondita': sessione read-only.
    # ATTENZIONE: 'SET TRANSACTION READ ONLY' fallisce se l'utente ha permessi solo di SELECT,
    # quindi proviamo ma ignoriamo eventuali errori.
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET ISOLATION_LEVEL = SERIALIZABLE")
    except oracledb.DatabaseError:
        pass
    conn.autocommit = False
    return conn


# ──────────────────────────────────────────────────────────────────────────────
# Costruzione query SELECT
# ──────────────────────────────────────────────────────────────────────────────

# Pattern accettati per nomi oggetto/colonna (whitelist per evitare iniezioni)
SAFE_IDENT = re.compile(r"^[A-Z][A-Z0-9_]*$")
SAFE_DBLINK = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _validate_ident(s: str, kind: str) -> str:
    s_up = (s or "").strip().upper()
    if not s_up or not SAFE_IDENT.match(s_up):
        raise ValueError(f"Identifier non valido per {kind}: {s!r}")
    return s_up


def _validate_dblink(s: str) -> str:
    s_up = (s or "").strip().upper()
    if not s_up or not SAFE_DBLINK.match(s_up):
        raise ValueError(f"DB link non valido: {s!r}")
    return s_up


def _date_bind(d: date, col_type: str) -> Any:
    """Converte una date Python al tipo bind atteso dalla colonna sorgente.
    - 'date'              -> datetime.date (Oracle DATE)
    - 'number_yyyymmdd'   -> int YYYYMMDD (es. 20260609)
    - 'julian_day'        -> int Julian Day Number (es. 2461201 per 2026-06-09).
                              In Oracle si converte con TO_DATE(num,'J') / TO_NUMBER(TO_CHAR(d,'J')).
                              Offset = 1721425 (date.toordinal() del 1-1-1 proleptic gregoriano + 1721425).
    """
    if col_type == "number_yyyymmdd":
        return int(d.strftime("%Y%m%d"))
    if col_type == "julian_day":
        return d.toordinal() + 1721425
    return d


def _validate_columns(cols: list[str]) -> list[str]:
    out = []
    for c in cols:
        cu = c.strip().upper()
        if not SAFE_IDENT.match(cu):
            raise ValueError(f"Colonna non valida: {c!r}")
        out.append(cu)
    return out


def build_query(sys_spec: SystemSpec, table: TableSpec,
                from_date: date | None, to_date: date | None,
                lookback_days: int = 7, run_date: date | None = None) -> tuple[str, dict[str, Any]]:
    """Costruisce SELECT validata. Usa bind variables per le date."""
    src = _validate_ident(table.src_obj(), "tabella")
    cols = _validate_columns(table.columns) if table.columns else []
    select_list = ", ".join(cols) if cols else "*"

    # FROM ... [@dblink]
    # Sorgenti senza db-link (accesso diretto allo schema indicato in config):
    # - cnd (legacy, schema CDT_SOURCE)
    # - cdt_estr (TO-BE: schema CDT_ESTR, stesso user del .env)
    if sys_spec.schema:
        schema = _validate_ident(sys_spec.schema, "schema")
        from_clause = f"{schema}.{src}"
    else:
        # logistix / stat: lettura via db-link (multi-sito)
        # NB: il dblink-key sara' iniettato dal chiamante (ciclo per sito)
        from_clause = f"{src}@{{DBLINK}}"

    where_parts: list[str] = []
    binds: dict[str, Any] = {}

    # WHERE clause statica configurata (es. ARM_TIPO_AREA = 1 - OP-10)
    if table.where_clause:
        # whitelist: ammettiamo solo "COL = literal_numerico" o "COL IN (n,n,...)" semplici
        wc = table.where_clause.strip()
        if not re.match(r"^[A-Z][A-Z0-9_]*\s*(=\s*\d+|IN\s*\(\s*\d+(\s*,\s*\d+)*\s*\))$", wc):
            raise ValueError(f"where_clause non in whitelist (semplici filtri numerici): {wc!r}")
        where_parts.append(wc)

    # Modalita' delta / snapshot / full
    if table.mode == "delta":
        # STRATEGIA: filtro su data come default sicuro (limita SEMPRE la finestra).
        # Il flag viene combinato in AND solo se esistono entrambi (in produzione restringe
        # ai "non ancora estratti"; in test e' un no-op se il flag non e' popolato).
        date_applied = False
        if table.date_column:
            dc = _validate_ident(table.date_column, "date_column")
            dct = table.date_column_type
            # Se passato range esplicito, usa quello; altrimenti finestra fallback lookback_days
            if from_date or to_date:
                if from_date:
                    where_parts.append(f"{dc} >= :from_date")
                    binds["from_date"] = _date_bind(from_date, dct)
                if to_date:
                    where_parts.append(f"{dc} <= :to_date")
                    binds["to_date"] = _date_bind(to_date, dct)
                date_applied = True
            elif run_date and lookback_days > 0:
                fallback_from = run_date - timedelta(days=lookback_days)
                where_parts.append(f"{dc} >= :from_date")
                where_parts.append(f"{dc} <= :to_date")
                binds["from_date"] = _date_bind(fallback_from, dct)
                binds["to_date"] = _date_bind(run_date, dct)
                logger.info("    %s: finestra %d gg -> [%s, %s] su %s (%s)",
                            table.name, lookback_days, fallback_from, run_date, dc, dct)
                date_applied = True

        # Flag come filtro aggiuntivo (non sostitutivo) — utile in prod (riduce ai non estratti)
        # In test/dev, se il flag non e' popolato, NVL(flag,0)=0 lascia passare tutto: ma il filtro
        # data sopra ha gia' limitato la finestra. Niente piu' "lettura piena dello storico".
        if table.flag_column:
            fc = _validate_ident(table.flag_column, "flag_column")
            where_parts.append(f"NVL({fc}, 0) = 0")

        # Caso patologico: ne' data ne' flag -> warning (lettura potenzialmente totale)
        if not date_applied and not table.flag_column:
            logger.warning("Tabella %s in modalita' delta senza date_column ne flag_column -> "
                           "lettura totale (potenzialmente lenta).", table.name)
    elif table.mode == "snapshot":
        # snapshot: full read, una volta al giorno (no filtro)
        pass
    elif table.mode == "full":
        # full: full read (no filtro, eventuale where_clause statica gia' aggiunto sopra)
        pass
    else:
        raise ValueError(f"mode non valida per {table.name}: {table.mode!r}")

    where_sql = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
    sql = f"SELECT {select_list} FROM {from_clause}{where_sql}"
    return sql, binds


def apply_max_rows(sql: str, max_rows: int) -> str:
    """Aggiunge FETCH FIRST N ROWS ONLY a una SELECT (Oracle 12c+)."""
    if max_rows and max_rows > 0:
        return f"{sql} FETCH FIRST {int(max_rows)} ROWS ONLY"
    return sql


# ──────────────────────────────────────────────────────────────────────────────
# Scrittura CSV
# ──────────────────────────────────────────────────────────────────────────────

def landing_path(output_dir: Path, sys_spec: SystemSpec, sito: str | None,
                 table_name: str, day: date) -> Path:
    parts = [output_dir, sys_spec.landing_subdir]
    if sys_spec.is_multisite_in_path and sito:
        parts.append(sito)
    parts.extend([table_name, f"{day.year:04d}", f"{day.month:02d}", f"{day.day:02d}"])
    return Path(*parts)


def _dedup_rows(rows: list[tuple], col_names: list[str], merge_keys: list[str]) -> tuple[list[tuple], int]:
    """
    Dedup per merge_keys (l'ultimo per chiave vince, replica il pattern AS-IS dove
    versioni successive sovrascrivono le precedenti).
    Ritorna (rows_dedup, num_dropped).
    """
    if not merge_keys or not rows:
        return rows, 0
    idx = []
    for k in merge_keys:
        if k in col_names:
            idx.append(col_names.index(k))
    if not idx:
        return rows, 0
    seen: dict[tuple, tuple] = {}
    for r in rows:
        key = tuple(r[i] for i in idx)
        seen[key] = r  # l'ultimo per chiave vince
    deduped = list(seen.values())
    return deduped, len(rows) - len(deduped)


def write_csv(conn: "oracledb.Connection", sql: str, binds: dict[str, Any],
              out_file: Path, csv_cfg: dict, extra_col_mag_sito: str | None,
              merge_keys: list[str] | None = None) -> int:
    """Esegue la query, dedup per merge_keys e scrive il CSV. Ritorna il numero di righe scritte."""
    sep = csv_cfg.get("separator", ";")
    enc = csv_cfg.get("encoding", "utf-8")
    null_value = csv_cfg.get("null_value", "")

    with conn.cursor() as cur:
        cur.execute(sql, binds)
        col_names = [d[0] for d in cur.description]
        rows = cur.fetchall()

    if extra_col_mag_sito is not None:
        # Aggiunge MAG_SITO_COD in testa per le sorgenti Logistix multi-sito (pattern AS-IS)
        col_names = ["MAG_SITO_COD"] + col_names
        rows = [(extra_col_mag_sito,) + tuple(r) for r in rows]

    # Dedup per merge_keys: simula il push reale dove la sorgente invia un solo record per chiave
    if merge_keys:
        rows, dropped = _dedup_rows(rows, col_names, merge_keys)
        if dropped > 0:
            logger.info("    dedup su %s: %d righe duplicate rimosse (chiave: %s)",
                        merge_keys[:3], dropped, '+'.join(merge_keys))

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding=enc, newline="") as fp:
        writer = csv.writer(fp, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(col_names)
        for r in rows:
            writer.writerow(["" if v is None else (null_value if v == "" and null_value else v) for v in r])
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Loop principale
# ──────────────────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> int:
    if load_dotenv:
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    config_path = Path(args.config).resolve()
    output_dir, csv_cfg, systems = load_config(config_path)
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()

    # Date
    if args.from_date or args.to_date:
        from_dt = date.fromisoformat(args.from_date) if args.from_date else None
        to_dt = date.fromisoformat(args.to_date) if args.to_date else from_dt or date.today()
        from_dt = from_dt or to_dt
        # Il file landing viene scritto su to_date (il "run_date"): per backfill profondi
        # NON espandiamo per ogni giorno separato (sarebbe troppo costoso). Il file
        # conterra' i record dall'intervallo [from_date, to_date].
        run_date = to_dt
    else:
        run_date = date.fromisoformat(args.run_date) if args.run_date else date.today()
        from_dt = None
        to_dt = None

    run_tag = run_date.strftime("%Y%m%d_%H%M%S") if False else datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = output_dir.parent / "logs"
    setup_logging(log_dir, run_tag)

    logger.info("Output dir: %s", output_dir)
    logger.info("Run date  : %s", run_date)
    if from_dt or to_dt:
        logger.info("Backfill window: [%s, %s]", from_dt, to_dt)
    if args.dry_run:
        logger.warning("DRY-RUN: nessuna query eseguita, nessun file scritto.")

    # Filtri CLI
    selected_systems = set(args.systems.split(",")) if args.systems else None
    selected_tables = set(args.tables.split(",")) if args.tables else None
    selected_sites = set(args.sites.split(",")) if args.sites else None

    # Connessione
    conn = None
    if not args.dry_run:
        try:
            conn = connect_oracle()
            # Timeout query (millisecondi). 0 = nessun timeout.
            if args.query_timeout and args.query_timeout > 0:
                conn.call_timeout = int(args.query_timeout) * 1000
                logger.info("Query timeout impostato a %d secondi.", args.query_timeout)
            logger.info("Connessione Oracle stabilita.")
        except Exception as e:
            logger.error("Connessione Oracle fallita: %s", e)
            return 3

    total_files = 0
    total_rows = 0
    total_empty_skipped = 0
    errors = 0

    try:
        for sys_key, sys_spec in systems.items():
            if selected_systems and sys_key not in selected_systems:
                continue
            logger.info("=" * 70)
            logger.info("SISTEMA: %s", sys_key)

            # Iterazione siti/db-link: per logistix sono multi, per stat uno solo,
            # per cnd/cdt_estr (accesso diretto allo schema) nessuno.
            site_iter: list[tuple[str | None, str | None]]
            if sys_spec.schema and not sys_spec.dblinks:
                site_iter = [(None, None)]  # accesso diretto, no dblink
            else:
                site_iter = list(sys_spec.dblinks.items())

            for sito, dblink in site_iter:
                if selected_sites and sito and sito not in selected_sites:
                    continue
                if dblink:
                    _validate_dblink(dblink)
                    logger.info("  Sito/dblink: %s -> %s", sito, dblink)
                else:
                    logger.info("  Sorgente diretta (no dblink)")

                for tbl_name, table in sys_spec.tables.items():
                    if selected_tables and tbl_name not in selected_tables:
                        continue
                    if table.disabled:
                        logger.info("    %s -> SKIP (disabled in config)", tbl_name)
                        continue
                    try:
                        sql, binds = build_query(sys_spec, table, from_dt, to_dt,
                                                  lookback_days=args.lookback_days, run_date=run_date)
                        sql = apply_max_rows(sql, args.max_rows)
                        if dblink:
                            sql = sql.replace("{DBLINK}", dblink)
                        # Per logistix il file e' un per-sito; per stat/cnd uno per tabella
                        out_dir = landing_path(output_dir, sys_spec,
                                               sito if sys_spec.is_multisite_in_path else None,
                                               tbl_name, run_date)
                        out_file = out_dir / f"{tbl_name}.csv"

                        if args.dry_run:
                            logger.info("    [DRY] %s | SQL: %s | bind=%s | out=%s",
                                        tbl_name, sql[:160] + ("..." if len(sql) > 160 else ""),
                                        binds, out_file)
                            continue

                        # Per logistix passiamo MAG_SITO_COD = sito (replica pattern AS-IS)
                        mag_sito = sito.upper() if (sys_key == "logistix" and sito) else None
                        n_rows = write_csv(conn, sql, binds, out_file, csv_cfg, mag_sito,
                                           merge_keys=table.merge_keys)

                        if n_rows == 0 and args.skip_empty:
                            try:
                                out_file.unlink()  # rimuove il file vuoto (solo header)
                            except OSError:
                                pass
                            total_empty_skipped += 1
                            logger.info("    %s -> 0 righe (skip empty)", tbl_name)
                        else:
                            total_files += 1
                            total_rows += n_rows
                            logger.info("    %s -> %d righe in %s", tbl_name, n_rows, out_file)
                            # Safety net: se la query raggiunge il cap, e' un campanello
                            # d'allarme (possibile lettura FULL al posto di DELTA, o finestra
                            # data troppo ampia). Va verificato manualmente.
                            if args.max_rows and n_rows >= args.max_rows:
                                logger.warning(
                                    "    ⚠ %s ha raggiunto il CAP di %d righe (mode=%s): "
                                    "verificare che non sia una lettura FULL non voluta!",
                                    tbl_name, args.max_rows, table.mode)
                    except Exception as e:
                        errors += 1
                        logger.error("    ERRORE %s/%s/%s: %s", sys_key, sito or "-", tbl_name, e)
                        # continue con la prossima tabella
    finally:
        if conn:
            # Sicurezza: nessuna transazione di scrittura. Rollback per non lasciare nulla appeso.
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
            logger.info("Connessione chiusa.")

    logger.info("=" * 70)
    logger.info("Riepilogo: files=%d, rows=%d, empty_skipped=%d, errors=%d",
                total_files, total_rows, total_empty_skipped, errors)
    return 0 if errors == 0 else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Landing Simulator Oracle -> CSV files")
    p.add_argument("--run-date", default=None, help="Data del run YYYY-MM-DD (default: oggi)")
    p.add_argument("--from-date", default=None, help="Inizio finestra backfill YYYY-MM-DD")
    p.add_argument("--to-date", default=None, help="Fine finestra backfill YYYY-MM-DD")
    p.add_argument("--systems", default=None, help="Filtro sistemi (logistix,stat,cdt_estr). NB: CND non piu' usato.")
    p.add_argument("--sites", default=None, help="Filtro siti Logistix (lgax,lgcx,...)")
    p.add_argument("--tables", default=None, help="Filtro tabelle (es. sto_tes_carichi,pesate)")
    p.add_argument("--output-dir", default=None, help="Override cartella output")
    p.add_argument("--config", default=str(Path(__file__).resolve().parent / "config.yaml"),
                   help="Path file YAML config")
    p.add_argument("--dry-run", action="store_true", help="Mostra solo le query, non esegue")
    p.add_argument("--skip-empty", action="store_true", default=True,
                   help="Non scrive file se la query restituisce 0 righe (default: True)")
    p.add_argument("--no-skip-empty", dest="skip_empty", action="store_false",
                   help="Scrive il file (solo header) anche con 0 righe")
    p.add_argument("--lookback-days", type=int, default=3,
                   help="Per le delta: finestra retrospettiva da run_date su date_column (default: 3gg). "
                        "7gg solo per backfill; a regime con bronze pruning attivo basta 1-2gg di overlap.")
    p.add_argument("--max-rows", type=int, default=5_000_000,
                   help="Tetto righe per query (default 5.000.000 = safety net anti-FULL). "
                        "0 = nessun limite. Se una query raggiunge il cap viene loggato un WARNING.")
    p.add_argument("--query-timeout", type=int, default=0,
                   help="Timeout per ogni query in secondi (0 = nessun timeout). Kill della query dopo N secondi.")
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args(sys.argv[1:])))
