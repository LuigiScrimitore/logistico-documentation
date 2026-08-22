"""
Iniezione mirata di normalize_sito nei Silver con SITO_COD.

Gestisce 2 pattern di creazione SITO_COD:
  A) F.col("<SRC>").cast("string").alias("SITO_COD")  (alias diretto)
  B) .withColumnRenamed("MAG_SITO_COD", "SITO_COD")    (rename)

Per ciascun file:
  - aggiunge import normalize_sito, get_sito_alias_map (se assente)
  - inietta _amap = get_sito_alias_map(spark, f"{BRONZE_CATALOG}.{SCHEMA}")
    una volta dentro il try (prima del primo uso) [solo se non gia' presente]
  - pattern A: F.col("X")...alias("SITO_COD") -> normalize_sito(F.col("X"), _amap).alias("SITO_COD")
  - pattern B: aggiunge .withColumn("MAG_SITO_COD", normalize_sito(F.col("MAG_SITO_COD"), _amap))
               prima del withColumnRenamed

Idempotente: se gia' contiene normalize_sito, salta.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# sorgenti sito note (alias diretto)
SITO_SRC = ("MAG_SITO_COD", "TEBO_SITO", "BOL_SITO", "RPLPR_SITO", "SP_SITO")

def transform(text: str) -> tuple[str, int]:
    if "normalize_sito" in text:
        return text, 0  # gia' fatto
    n = 0

    # Pattern A: F.col("<SRC>").cast("string").alias("SITO_COD")
    def repl_a(m):
        nonlocal n
        src = m.group(1)
        if src in SITO_SRC:
            n += 1
            return f'normalize_sito(F.col("{src}"), _amap).alias("SITO_COD")'
        return m.group(0)
    text = re.sub(r'F\.col\("([A-Z_]+)"\)\.cast\("string"\)\.alias\("SITO_COD"\)', repl_a, text)

    # Pattern B: .withColumnRenamed("MAG_SITO_COD", "SITO_COD")  (con spazi variabili)
    def repl_b(m):
        nonlocal n
        n += 1
        indent = m.group(1)
        return (f'{indent}.withColumn("MAG_SITO_COD", normalize_sito(F.col("MAG_SITO_COD"), _amap))'
                f'{m.group(0)}')
    text = re.sub(r'(\n[ \t]*)\.withColumnRenamed\("MAG_SITO_COD",\s*"SITO_COD"\)', repl_b, text)

    if n == 0:
        return text, 0

    # import (transform e' gia' uscita early se normalize_sito era presente)
    text = re.sub(r'from utils import ([^\n]+)',
                  lambda m: (f'from utils import {m.group(1)}, normalize_sito, get_sito_alias_map'
                             if 'normalize_sito' not in m.group(1) else m.group(0)),
                  text, count=1)

    # _amap injection: subito dopo 'logger.info(f"START' (dentro try) se non presente
    if "_amap =" not in text:
        text = re.sub(r'(\n[ \t]*)(logger\.info\(f?"START)',
                      r'\1_amap = get_sito_alias_map(spark, f"{BRONZE_CATALOG}.{SCHEMA}")\1\2',
                      text, count=1)
    return text, n


def main(argv):
    total = 0
    for fp in argv:
        p = Path(fp)
        txt = p.read_text(encoding="utf-8")
        new, n = transform(txt)
        if n > 0:
            p.write_text(new, encoding="utf-8")
            print(f"  {p.name}: {n} SITO_COD normalizzati")
            total += n
        else:
            print(f"  {p.name}: skip (gia' fatto o nessun pattern)")
    print(f"Totale: {total}")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
