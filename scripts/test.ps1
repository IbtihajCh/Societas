# SOCIETAS Test Script (Windows / PowerShell)
# Runs the full test suite across all subsystems.

$ErrorActionPreference = "Stop"
$exitCode = 0

function Write-Step($msg) { Write-Host "→ $msg" -ForegroundColor Cyan }
function Write-Pass($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; $script:exitCode = 1 }

# ── Simulation ──
Write-Step "Simulation tests..."
Push-Location simulation
try {
    .\.venv\Scripts\Activate.ps1
    $result = pytest --cov --cov-branch --cov-fail-under=90 --tb=short 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Simulation tests passed"
    } else {
        Write-Fail "Simulation tests failed"
        Write-Host $result
    }
} catch {
    Write-Fail "Exception: $_"
}
deactivate 2>$null
Pop-Location

# ── Backend ──
Write-Step "Backend tests..."
Push-Location backend
try {
    .\.venv\Scripts\Activate.ps1
    $result = pytest --cov --cov-fail-under=80 --tb=short 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Backend tests passed"
    } else {
        Write-Fail "Backend tests failed"
        Write-Host $result
    }
} catch {
    Write-Fail "Exception: $_"
}
deactivate 2>$null
Pop-Location

# ── Frontend ──
Write-Step "Frontend tests..."
Push-Location frontend
try {
    $result = npm test -- --coverage 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Frontend tests passed"
    } else {
        Write-Fail "Frontend tests failed"
        Write-Host $result
    }
} catch {
    Write-Fail "Exception: $_"
}
Pop-Location

# ── Cross-cutting ──
Write-Step "Cross-cutting tests..."
Push-Location .
try {
    $result = pytest tests/ --tb=short 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Pass "Cross-cutting tests passed"
    } else {
        Write-Fail "Cross-cutting tests failed"
        Write-Host $result
    }
} catch {
    Write-Fail "Exception: $_"
}
Pop-Location

if ($exitCode -eq 0) {
    Write-Host "`n✔ All tests passed." -ForegroundColor Green
} else {
    Write-Host "`n✗ Some tests failed." -ForegroundColor Red
}
exit $exitCode
