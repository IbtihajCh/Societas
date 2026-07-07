#!/usr/bin/env bash
# SOCIETAS Setup Script (macOS / Linux)
# One-command development environment bootstrap.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

step()  { echo -e "${CYAN}→${NC} $1"; }
done_msg() { echo -e "${GREEN}✓${NC} $1"; }

# ── Prerequisites ──
step "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ required"; exit 1; }
done_msg "Python: $(python3 --version)"

command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required"; exit 1; }
done_msg "Node.js: $(node --version)"

command -v git >/dev/null 2>&1 || { echo "Git required"; exit 1; }
done_msg "Git: $(git --version)"

# ── Simulation ──
step "Setting up simulation environment..."
cd simulation
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt
deactivate
cd ..
done_msg "Simulation environment ready"

# ── Backend ──
step "Setting up backend environment..."
cd backend
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet -r requirements-dev.txt
deactivate
cd ..
done_msg "Backend environment ready"

# ── Frontend ──
step "Setting up frontend environment..."
cd frontend
npm install --silent
cd ..
done_msg "Frontend dependencies installed"

# ── Pre-commit ──
step "Installing pre-commit hooks..."
pip install --quiet pre-commit
pre-commit install
done_msg "Pre-commit hooks installed"

# ── .env ──
step "Creating .env file..."
if [ ! -f docker/.env ]; then
    cp docker/.env.example docker/.env
    done_msg ".env created from template"
else
    done_msg ".env already exists, skipping"
fi

echo ""
echo -e "${GREEN}✔ Setup complete! Run ./scripts/test.sh to verify.${NC}"
