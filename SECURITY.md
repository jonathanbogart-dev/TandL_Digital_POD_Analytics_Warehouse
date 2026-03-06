# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `main` branch | ✅ Active |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, **do not open a public GitHub issue**.

Instead, please report it by emailing the maintainers directly. Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested remediation (optional)

We will acknowledge your report within 48 hours and aim to release a fix within 7 days for critical issues.

## Security Practices

### Secrets Management
- API keys, database credentials, and tokens are **never committed to git**
- All secrets are stored in `.env` (gitignored) or a secrets manager in production
- `.env.example` contains only placeholder values — never real credentials

### API Security
- The FastAPI backend validates all inputs via Pydantic models
- SQL queries use parameterized statements (SQLAlchemy `text()` with bound params) — no string interpolation
- CORS is restricted to the known dashboard origin

### Dependencies
- Dependencies are pinned in `pyproject.toml`
- Run `pip audit` or `safety check` regularly to detect vulnerable packages

### Data Access
- The warehouse contains business-sensitive order and revenue data
- Database access should be restricted by IP allowlist in production
- API endpoints return aggregated data only — no PII is exposed via the API

## Known Limitations

- The static dashboard site (`docs/`) is served publicly via GitHub Pages. It contains only pre-aggregated sample KPI data — no real customer PII or order details.
