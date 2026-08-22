# ─────────────────────────────────────────────────────────────────────────────
# Logistico 2.0 — Helper PowerShell per eseguire un Bronze notebook nel container.
#
# Uso:
#   .\run.ps1 <path-notebook-windows> [--extra-arg1] [--extra-arg2] ...
#
# Esempi:
#   .\run.ps1 notebooks\bronze\anagrafiche\bronze_tabgen.py
#   .\run.ps1 notebooks\bronze\carichi\bronze_carichi_testate.py --run-date 2026-06-09
#   .\run.ps1 notebooks\bronze\carichi\bronze_pesate.py --siti lgax
#
# Lo script:
#   1. Converte il path Windows (con backslash) in path Linux (con slash)
#   2. Lancia run_notebook.py dentro il container con i mount gia' configurati
#   3. Passa eventuali argomenti extra (--run-date, --siti, --set, ecc.)
# ─────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Notebook,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

# Verifica che il container sia attivo
$running = docker ps --filter "name=logistico-spark" --format "{{.Names}}"
if (-not $running) {
    Write-Host "[INFO] Container 'logistico-spark' non in esecuzione. Avvio con 'docker compose up -d'..." -ForegroundColor Yellow
    Push-Location $PSScriptRoot
    try { docker compose up -d } finally { Pop-Location }
}

# Converte path Windows (backslash) -> Linux (slash) e antepone /workspace/code
$notebookLinux = $Notebook.Replace('\', '/').TrimStart('/')
$notebookContainer = "/workspace/code/$notebookLinux"

# Costruisce gli argomenti per docker compose
$argsList = @(
    "compose"
    "-f"; (Join-Path $PSScriptRoot "docker-compose.yml")
    "exec"; "spark"
    "python"; "/workspace/code/tests/local_bronze/run_notebook.py"
    "--notebook"; $notebookContainer
    "--landing"; "/workspace/data/landing"
    "--warehouse"; "/workspace/data/warehouse"
)
if ($ExtraArgs) { $argsList += $ExtraArgs }

Write-Host "[INFO] Lancio: $($argsList -join ' ')" -ForegroundColor Cyan
& docker @argsList
exit $LASTEXITCODE
