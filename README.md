# Daily PA

A small, secure service that checks your email and calendar every morning and produces a concise daily brief.

## Quickstart

1. Copy `.env.example` to `.env` and fill values.
2. Create a virtualenv and install dependencies:

```bash
make setup
```

3. Run once locally:

```bash
make run
```

4. Configure OAuth for Gmail (read-only) and Microsoft Graph (Calendars.Read). Tokens are cached under `config/` paths.

5. Schedule via cron or GitHub Actions. See `.github/workflows/daily-pa.yml` for CI template.

## Modules

- `src/config.py`: Pydantic settings and feature flags
- `src/gmail_client.py`: Gmail API client (read-only)
- `src/graph_client.py`: Microsoft Graph Calendar client
- `src/gcal_client.py`: Google Calendar client (alternative)
- `src/triage.py`: Email triage scoring and actionable detection
- `src/calendar_analyzer.py`: Calendar conflicts and gaps analysis
- `src/formatter.py`: Markdown renderer
- `src/deliver.py`: Email/Teams/webhook delivery, file save
- `src/main.py`: Entrypoint and orchestration

## Tests

Run:

```bash
make test
```

Tests cover triage, calendar analysis, and formatting.

## Security & Privacy

- Read-only scopes by default
- Secrets via `.env`/keychain only
- No secrets in logs; addresses redacted to domain where logged
