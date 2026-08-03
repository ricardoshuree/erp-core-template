# [mcp-local harness] feature: dev-script | plano: 0437cb23 | 2026-08-03 16:41:28
# Script que abre backend e frontend em janelas PowerShell separadas com um comando
# dev.ps1 — sobe backend e frontend em paralelo para desenvolvimento local.
#
# Uso:
#   . .\activate.ps1   (primeira vez na sessao, ativa o venv)
#   .\dev.ps1
#
# O que faz:
#   - Abre o backend (FastAPI + uvicorn) em http://localhost:8000
#   - Abre o frontend (Vite + React) em http://localhost:5173
#   - Cada um roda em uma janela de terminal separada
#   - Fechar as janelas encerra os processos

$root = $PSScriptRoot

Write-Host "Subindo backend em http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; . .\activate.ps1; cd backend; uv run uvicorn app.main:app --reload --port 8000"
)

Write-Host "Subindo frontend em http://localhost:5173 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Ambiente de desenvolvimento iniciado:" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"      -ForegroundColor Green
Write-Host "  API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173"      -ForegroundColor Green
Write-Host ""
Write-Host "Feche as janelas abertas para encerrar os servidores." -ForegroundColor Yellow
