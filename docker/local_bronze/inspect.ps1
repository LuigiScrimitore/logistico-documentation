# ─────────────────────────────────────────────────────────────────────────────
# Helper PowerShell per ispezionare le Delta tables nel warehouse del container.
#
# Uso:
#   .\inspect.ps1                                # lista tutto bronze_dev/silver_dev/gold_prod
#   .\inspect.ps1 --database bronze_dev          # solo bronze
#   .\inspect.ps1 --database bronze_dev --table sto_tes_carichi --schema --show 5
# ─────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

$argsList = @(
    "compose"
    "-f"; (Join-Path $PSScriptRoot "docker-compose.yml")
    "exec"; "spark"
    "python"; "/workspace/code/tests/local_bronze/inspect_delta.py"
    "--warehouse"; "/workspace/data/warehouse"
)
if ($ExtraArgs) { $argsList += $ExtraArgs }

& docker @argsList
exit $LASTEXITCODE
