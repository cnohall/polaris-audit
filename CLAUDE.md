# CLAUDE.md

## Project Overview

**Polaris Audit** is a CLI tool that audits websites across four pillars: Privacy, Security, Accessibility, and Performance.

## Technology Stack

- **Language**: Python 3.10+
- **CLI Framework**: Click
- **HTML Parsing**: BeautifulSoup4 + lxml
- **HTTP Client**: Requests
- **JS Rendering**: Playwright (optional)
- **Packaging**: pyproject.toml with setuptools

## Project Structure

```
polaris_audit/
├── cli.py              # Click CLI entry point
├── scanner.py          # AssessmentScanner — orchestrates all checks
├── result.py           # ScanResultBuilder
├── checkers/           # Assessment modules (one per pillar)
│   ├── base.py         # BaseChecker abstract class
│   ├── security.py     # SecurityChecker
│   ├── privacy.py      # PrivacyChecker (coordinates sub-checkers)
│   ├── accessibility.py# AccessibilityChecker (coordinates sub-checkers)
│   └── performance.py  # PerformanceChecker
├── services/           # Supporting services
│   ├── scoring.py      # Score calculation
│   ├── fix_instructions.py  # Fix recommendations
│   └── ...
├── utils/              # HTTP client, config loader, validation
└── formatters/         # Terminal and JSON output formatters
```

## Essential Commands

```bash
pip install -e ".[dev]"          # Install in development mode
polaris scan https://example.com  # Scan a URL
polaris scan https://example.com --format json  # JSON output
polaris scan https://example.com -v  # Verbose
pytest                            # Run tests
```

## Development Guidelines

- Keep the scanner engine independent — no web framework dependencies
- Each checker is a self-contained module inheriting from BaseChecker
- Use `polaris_audit.*` absolute imports throughout
- Test with `pytest`
