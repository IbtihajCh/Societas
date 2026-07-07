# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Repository structure and folder hierarchy
- GitHub configuration (issue/PR templates, CODEOWNERS, CI/CD)
- Documentation system (ADRs, guides, templates, standards)
- Docker environment with multi-service orchestration
- Obsidian vault as version-controlled knowledge base
- Prompt management system organized by purpose
- Development workflow and branching strategy
- Coding standards and testing requirements
- AI agent operational rules
- Architecture Decision Record system
- Engineering operating system foundation

### Changed

### Deprecated

### Removed

- CI push triggers on `main` (temporarily disabled — skeleton phase)
  - `.github/workflows/ci.yml`: removed push trigger, PR-only now
  - `.github/workflows/docker.yml`: removed push trigger, PR-only now
  - **Re-enable when:** implementation reaches Phase 1 (working simulation + backend code)

### Fixed

### Security

---

## [0.1.0] — 2026-07-07

### Added

- Project initialization
- Master Context & Architecture Decisions v2.0
- Competition strategy (AMD + Gemma dual-track)
- Three-layer system architecture design
- Dual-process cognitive architecture (System 1 / System 2)
- Escalation threshold and hybrid decision fusion design
- AI responsibility matrix and model routing design
- Feature prioritization
- Team role definitions

[Unreleased]: https://github.com/societas/societas/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/societas/societas/releases/tag/v0.1.0
