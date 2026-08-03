# [mcp-local harness] feature: vscode-venv-auto | plano: 0fc9e92e | 2026-08-03 14:35:33
# Corrige caminho do venv para a raiz do projeto (workspace uv)
# activate.ps1
# Ativa o ambiente virtual do projeto (gerado na raiz pelo uv workspace).
# Uso manual: . .\activate.ps1
# Configurado automaticamente via .vscode/settings.json como shell profile.

$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    . $venvPath
    Write-Host "venv ativado: .venv" -ForegroundColor Green
} else {
    Write-Host "venv nao encontrado em: $venvPath" -ForegroundColor Yellow
    Write-Host "Execute na raiz do projeto: uv sync" -ForegroundColor Yellow
}
