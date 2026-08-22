"""
Trasformazione mirata: sostituisce F.col("<COL_JULIAN>").cast("date")
con julian_to_date(F.col("<COL_JULIAN>")) SOLO per colonne con prefisso
Julian Day noto (sorgenti Logistix/STAT legacy).

Sicuro: non tocca cast("date") su colonne non-Julian (es. _bronze_load_date,
DATA_FOTO gia' convertite).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# Prefissi colonna che nel sorgente Oracle legacy sono Julian Day Number.
JULIAN_PREFIXES = (
    "STCAR_", "SRCAR_", "CE178_", "BOL_", "TEBO_", "RPLPR_",
    "ABT_", "CARTE_", "DTCRL_", "LSPRL_", "PSP_",
)

# F.col("PREFISSO...").cast("date")  -> julian_to_date(F.col("PREFISSO..."))
# cattura il nome colonna tra virgolette
PATTERN = re.compile(r'F\.col\(\s*"([A-Z0-9_]+)"\s*\)\.cast\(\s*"date"\s*\)')

def transform(text: str) -> tuple[str, int]:
    count = 0
    def repl(m):
        nonlocal count
        col = m.group(1)
        if col.startswith(JULIAN_PREFIXES):
            count += 1
            return f'julian_to_date(F.col("{col}"))'
        return m.group(0)  # lascia invariato
    new = PATTERN.sub(repl, text)
    return new, count

def main(argv):
    total = 0
    for fp in argv:
        p = Path(fp)
        txt = p.read_text(encoding="utf-8")
        new, n = transform(txt)
        if n > 0:
            # assicura import (idempotente): aggiungi julian_to_date se non gia' importato
            if "from utils import get_catalog, julian_to_date" not in new:
                new = new.replace("from utils import get_catalog",
                                  "from utils import get_catalog, julian_to_date", 1)
            p.write_text(new, encoding="utf-8")
            print(f"  {p.name}: {n} cast Julian convertiti")
            total += n
        else:
            print(f"  {p.name}: nessun cast Julian (skip)")
    print(f"Totale: {total} conversioni")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
