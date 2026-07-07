#!/usr/bin/env bash
# SOCIETAS Clean Script (macOS / Linux)
# Removes build artifacts, caches, and virtual environments.

set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}→ Cleaning build artifacts...${NC}"

rm_if_exists() {
    if [ -e "$1" ]; then
        rm -rf "$1"
        echo -e "  ${YELLOW}Removed:${NC} $1"
    fi
}

# Python
rm_if_exists "simulation/.venv"
rm_if_exists "backend/.venv"

# Node
rm_if_exists "frontend/node_modules"
rm_if_exists "frontend/.next"
rm_if_exists "frontend/coverage"

# Coverage
rm_if_exists ".coverage"
rm_if_exists "htmlcov"
rm_if_exists ".pytest_cache"
rm_if_exists ".mypy_cache"
rm_if_exists ".ruff_cache"

# Docker
rm_if_exists "docker/.env"

# Simulation data
rm_if_exists "simulation/data"
rm_if_exists "simulation/output"
rm_if_exists "simulation/results"

# OS artifacts
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

echo -e "${GREEN}✔ Clean complete.${NC}"
