#!/usr/bin/env bash
# SOCIETAS Test Script (macOS / Linux)
# Runs the full test suite across all subsystems.

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
step "Simulation tests..."
cd simulation
source .venv/bin/activate 2>/dev/null || true
pip install pytest pytest-cov --quiet 2>/dev/null
pytest --cov --cov-branch --cov-fail-under=90 --tb=short && pass "Simulation tests passed" || fail "Simulation tests failed"
deactivate 2>/dev/null || true
cd ..

# ── Backend ──
step "Backend tests..."
cd backend
source .venv/bin/activate 2>/dev/null || true
pip install pytest pytest-cov --quiet 2>/dev/null
pytest --cov --cov-fail-under=80 --tb=short && pass "Backend tests passed" || fail "Backend tests failed"
deactivate 2>/dev/null || true
cd ..

# ── Frontend ──
step "Frontend tests..."
cd frontend
npm test -- --coverage && pass "Frontend tests passed" || fail "Frontend tests failed"
cd ..

# ── Cross-cutting ──
step "Cross-cutting tests..."
pytest tests/ --tb=short && pass "Cross-cutting tests passed" || fail "Cross-cutting tests failed"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✔ All tests passed.${NC}"
else
    echo -e "\n${RED}✗ Some tests failed.${NC}"
fi
exit $EXIT_CODE
