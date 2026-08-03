# activate.ps1 — ativa o venv do backend ao abrir o terminal no VS Code.
# Uso manual: . .\activate.ps1

$venvPath = Join-Path $PSScriptRoot "backend\.venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    . $venvPath
    Write-Host "venv do backend ativado: backend\.venv" -ForegroundColor Green
} else {
    Write-Host "venv nao encontrado em: $venvPath" -ForegroundColor Yellow
    Write-Host "Execute primeiro: cd backend && uv sync" -ForegroundColor Yellow
}
