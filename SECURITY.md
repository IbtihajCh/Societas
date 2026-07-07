# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

This project is a hackathon prototype and does not handle sensitive user data in production. However, if you discover a security vulnerability, please report it privately by contacting the project maintainers.

**Do not** report security vulnerabilities through public GitHub issues.

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested remediation (if known)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Scope

- The simulation engine runs locally only
- No production deployment is intended for the hackathon phase
- API endpoints are designed for local development only
- No authentication or user data storage is currently implemented

## AI Security

- Prompt injection is a known risk for the Gemma integration layer
- All LLM outputs are advisory only — the deterministic engine always retains decision authority
- Prompt validation is enforced through structured schemas defined in [docs/guides/coding-standards.md](docs/guides/coding-standards.md)
- LLM inputs are constrained to structured JSON; free-form text inputs are not accepted from untrusted sources
