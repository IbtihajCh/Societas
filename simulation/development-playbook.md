# Simulation Development Playbook

Pitfalls and patterns learned during the v1.0 implementation. Read before dispatching subagents.

## 1. Shared Schema Changes Break Consumers

Changing enums, schemas, or type aliases in shared/ ripples to backend, DTOs, and tests.

**What to do:**
- After any shared/ change, grep for old values across the whole project
- Run backend tests immediately — shared/ has no CODEOWNER, changes affect all layers
- Check `shared/dto/` for hardcoded enum values (e.g. `WealthClass.WORKING` after a rename)

## 2. Python Test Environment Is Fragile

No pip install -e ., no PYTHONPATH set, namespace conflicts from test `__init__.py` files.

**What to do:**
- Always create venv: `python -m venv venv` then `venv\Scripts\python.exe -m pip install numpy pytest pytest-cov`
- Add `pythonpath = ["."]` to pyproject.toml `[tool.pytest.ini_options]`
- Never put `__init__.py` in test directories — creates namespace conflicts with `shared/`
- Run tests with `venv\Scripts\python.exe -m pytest`, not bare `pytest`

## 3. Subagent Specs Must Be Exhaustive

Fixer subagents fail silently or produce wrong code when specs are ambiguous.

**What to do:**
- Include exact class names, method signatures, import paths, and constant names in the spec
- Specify test coverage expectations (e.g. "23 test specs: 5 for basic functionality, 6 for edge cases...")
- Tell fixers which files already exist (import paths) and which they must create
- Always include the run command: `& ".\venv\Scripts\python.exe" -m pytest <test_file> -v --tb=short`
- Mention environment variables like `PYTHONPATH` if needed

## 4. Backend DB Pollutes Between Tests

SQLite DB file (`societas.db`) persists between runs. Tests that expect empty state fail when prior tests left data.

**What to do:**
- Before running test suites, delete the DB: `Remove-Item societas.db`
- Know which tests have isolation issues — `test_list_policies_empty` is a known offender
- Run problematic tests isolated first to verify they pass

## 5. Documentation Lags Without Explicit Tracking

After implementation phases, docs need updating: CHANGELOG, progress report, README, summary.

**What to do:**
- After each phase commit, update at minimum `docs/implementation-summary.md` and `docs/progress-report-simulation.md`
- Run `git status` before committing to catch untracked doc changes
- Keep audit trail entries dated and specific

## 6. Context Management During Long Sessions

Long implementation sessions exhaust context quickly.

**What to do:**
- Compress after every phase completion or ~30 messages
- Compress old exploration reads (file contents no longer needed) aggressively
- Dispatch fixers in parallel — never wait on one fixer to start the next
- Commit each phase immediately after verification to minimize WIP state
