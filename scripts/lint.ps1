# SOCIETAS Lint Script (Windows / PowerShell)
# Runs all linters across the project. Exits non-zero on any failure.

$ErrorActionPreference = "Stop"
$exitCode = 0

function Write-Step($msg) { Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; $script:exitCode = 1 }

# ── Simulation ──
Write-Step "Simulation (ruff + mypy)..."
Push-Location simulation
try {
    $null = .\.venv\Scripts\Activate.ps1
    $r = pip install ruff mypy --quiet 2>&1
    $result = ruff check . 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Pass "ruff passed" } else { Write-Fail "ruff failed"; Write-Host $result }
    $result = mypy . --strict 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Pass "mypy passed" } else { Write-Fail "mypy failed"; Write-Host $result }
} catch {
    Write-Fail "Exception: $_"
}
deactivate 2>$null
Pop-Location

# ── Backend ──
Write-Step "Backend (ruff + mypy)..."
Push-Location backend
try {
    .\.venv\Scripts\Activate.ps1
    $r = pip install ruff mypy --quiet 2>&1
    $result = ruff check . 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Pass "ruff passed" } else { Write-Fail "ruff failed"; Write-Host $result }
    $result = mypy . 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Pass "mypy passed" } else { Write-Fail "mypy failed"; Write-Host $result }
} catch {
    Write-Fail "Exception: $_"
}
deactivate 2>$null
Pop-Location

# ── Frontend ──
Write-Step "Frontend (ESLint + TypeScript)..."
Push-Location frontend
try {
    $result = npm run lint 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Pass "ESLint passed" } else { Write-Fail "ESLint failed"; Write-Host $result }
    $result = npm run typecheck 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Pass "TypeScript passed" } else { Write-Fail "TypeScript failed"; Write-Host $result }
} catch {
    Write-Fail "Exception: $_"
}
Pop-Location

if ($exitCode -eq 0) {
    Write-Host "`n✔ All linters passed." -ForegroundColor Green
} else {
    Write-Host "`n✗ Some linters failed." -ForegroundColor Red
}
exit $exitCode
