# SOCIETAS Clean Script (Windows / PowerShell)
# Removes build artifacts, caches, and virtual environments.

$ErrorActionPreference = "Continue"

function Remove-IfExists($path) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
        Write-Host "  Removed: $path" -ForegroundColor DarkYellow
    }
}

Write-Host "→ Cleaning build artifacts..." -ForegroundColor Cyan

# Python
Remove-IfExists "simulation\.venv"
Remove-IfExists "simulation\__pycache__"
Remove-IfExists "backend\.venv"
Remove-IfExists "backend\__pycache__"
Remove-IfExists "tests\__pycache__"

# Node
Remove-IfExists "frontend\node_modules"
Remove-IfExists "frontend\.next"
Remove-IfExists "frontend\coverage"

# Coverage
Remove-IfExists ".coverage"
Remove-IfExists "htmlcov"
Remove-IfExists ".pytest_cache"
Remove-IfExists ".mypy_cache"
Remove-IfExists ".ruff_cache"

# Docker
Remove-IfExists "docker\.env"

# Simulation data
Remove-IfExists "simulation\data"
Remove-IfExists "simulation\output"
Remove-IfExists "simulation\results"

# OS artifacts
Get-ChildItem -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "*.pyc" -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter ".DS_Store" -File | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "Thumbs.db" -File | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "✔ Clean complete." -ForegroundColor Green
