$ErrorActionPreference = 'Stop'

& ./infra/scripts/authorize-dataverse.ps1
uv run --project src --no-sync python scripts/setup_demo.py seed-policies
if ($LASTEXITCODE -ne 0) {
    throw "Failed to seed expense policies."
}
