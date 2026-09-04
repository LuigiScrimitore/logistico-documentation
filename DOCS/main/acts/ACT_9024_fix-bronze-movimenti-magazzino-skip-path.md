# ACT_9024 · Fix bronze_movimenti_magazzino — skip del sito senza file (LL-021)

**Status**: done
**Type**: fix
**Origin**: emerged (run E2E giacenze in DEV, [[ACT_CND-01]])
**Sprint**: fuori-sprint (emergente)
**Fase / Wave**: FASE 3 — Wave B Giacenze
**Gg (stima)**: <0.5
**Blocco**: nessuno
**Created**: 2026-09-03   **Closed**: 2026-09-03
**Dipende da**: —   **Blocca**: run E2E `logistica_giacenze` (bronze_movimenti_magazzino a monte)
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Al run E2E giacenze in DEV, `bronze_movimenti_magazzino` (legge `imbfmovim` da `logistix-landing`, multi-sito)
è fallito con `[PATH_NOT_FOUND] .../lccx/imbfmovim/2026/09/02/*.csv` → `AnalysisException` → downstream skippati →
job FAILED. Il sito **lccx** ha 0 righe `imbfmovim` (→ `skip_empty` nel seed → nessun file). Il notebook aveva un
`try/except AnalysisException` ma **non lo intercettava**: `spark.read.csv(...)` è **lazy**, l'eccezione scattava a
valle (union/azione), fuori dal try — è il pattern [[LL-021]] (path assente letto lazy sfugge al try/except).

## Obiettivo
Un sito senza file viene **skippato** (processando gli altri), non fa fallire il job. `bronze_movimenti_magazzino`
robusto come gli altri bronze multi-sito già fixati (es. `bronze_catena`).

## Analisi tecnica
Applicato il pattern di `bronze_catena`: forzare la risoluzione **EAGER** del path dentro il `try` con `df.columns`
(materializza lo schema → se il path manca l'eccezione scatta lì e viene catturata) + `except Exception` (generico,
non solo `AnalysisException`). Nessuna generazione di header a 0 righe (si mantiene `skip_empty` dell'extractor).

```python
for p in landing_paths():
    try:
        df = read_one(p)
        df.columns  # LL-021: risoluzione eager del path
        frames.append(df)
    except Exception as _e:
        logger.warning(f"Path non trovato/illeggibile: {p} — skip ({type(_e).__name__})")
```

## Verifica
Ri-run `logistica_giacenze` in DEV (run_date 2026-09-02): `bronze_movimenti_magazzino` completa skippando `lccx`,
i downstream (`silver_prep_giacenze` → `gold_f_giacenze_daily`) proseguono. (Da eseguire dopo il merge.)

## Esito
Fix applicato in `notebooks/bronze/giacenze/bronze_movimenti_magazzino.py` (PR #4, mergiato `73351f7`→main).
**Validato E2E** (2026-09-03, ri-run `logistica_giacenze` DEV): `bronze_movimenti_magazzino` non è più il blocco
(prima falliva `PATH_NOT_FOUND` su `lccx`), la catena arriva a `silver.catena_unificata` (44.094 righe). Il run
giacenze resta KO più a valle per un problema **indipendente** di mapping sito (`silver_t_stock`=0, vedi OP-TRA-1).

## Lezioni
- Applica [[LL-021]] (path mancante lazy → forzare risoluzione eager nel try). Nessuna lezione nuova.

## Follow-up
- Verificare se altri bronze multi-sito hanno ancora il `try/except` senza forzatura eager (stesso rischio).
