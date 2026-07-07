#!/usr/bin/env bash
# SOCIETAS Lint Script (macOS / Linux)
# Runs all linters across the project. Exits non-zero on any failure.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

EXIT_CODE=0

step() { echo -e "${CYAN}→${NC} $1"; }
pass() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; EXIT_CODE=1; }

# ── Simulation ──
step "Simulation (ruff + mypy)..."
cd simulation
source .venv/bin/activate 2>/dev/null || true
pip install ruff mypy --quiet 2>/dev/null
ruff check . && pass "ruff passed" || fail "ruff failed"
mypy . --strict && pass "mypy passed" || fail "mypy failed"
deactivate 2>/dev/null || true
cd ..

# ── Backend ──
step "Backend (ruff + mypy)..."
cd backend
source .venv/bin/activate 2>/dev/null || true
pip install ruff mypy --quiet 2>/dev/null
ruff check . && pass "ruff passed" || fail "ruff failed"
mypy . && pass "mypy passed" || fail "mypy failed"
deactivate 2>/dev/null || true
cd ..

# ── Frontend ──
step "Frontend (ESLint + TypeScript)..."
cd frontend
npm run lint && pass "ESLint passed" || fail "ESLint failed"
npm run typecheck && pass "TypeScript passed" || fail "TypeScript failed"
cd ..

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✔ All linters passed.${NC}"
else
    echo -e "\n${RED}✗ Some linters failed.${NC}"
fi
exit $EXIT_CODE
