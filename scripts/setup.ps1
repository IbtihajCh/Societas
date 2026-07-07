# SOCIETAS Setup Script (Windows / PowerShell)
# One-command development environment bootstrap.

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host "→ $msg" -ForegroundColor Cyan
}

function Write-Done($msg) {
    Write-Host "✓ $msg" -ForegroundColor Green
}

Write-Step "Checking prerequisites..."

# Python
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.11+ is required. Install from https://python.org"
    exit 1
}
Write-Done "Python: $pyVersion"

# Node
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Node.js 20+ is required. Install from https://nodejs.org"
    exit 1
}
Write-Done "Node.js: $nodeVersion"

# Git
$gitVersion = git --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Git is required. Install from https://git-scm.com"
    exit 1
}
Write-Done "Git: $gitVersion"

# ── Simulation ──
Write-Step "Setting up simulation environment..."
Push-Location simulation
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt
deactivate
Pop-Location
Write-Done "Simulation environment ready"

# ── Backend ──
Write-Step "Setting up backend environment..."
Push-Location backend
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt
deactivate
Pop-Location
Write-Done "Backend environment ready"

# ── Frontend ──
Write-Step "Setting up frontend environment..."
Push-Location frontend
npm install --silent
Pop-Location
Write-Done "Frontend dependencies installed"

# ── Pre-commit ──
Write-Step "Installing pre-commit hooks..."
pip install --quiet pre-commit
pre-commit install
Write-Done "Pre-commit hooks installed"

# ── .env ──
Write-Step "Creating .env file..."
if (-not (Test-Path "docker\.env")) {
    Copy-Item "docker\.env.example" "docker\.env"
    Write-Done ".env created from template"
} else {
    Write-Done ".env already exists, skipping"
}

Write-Host "`n✔ Setup complete! Run .\scripts\test.ps1 to verify." -ForegroundColor Green
