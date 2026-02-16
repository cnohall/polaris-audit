# Polaris

**A single CLI that audits your website across four pillars: Privacy, Security, Accessibility, and Performance.**

```bash
pip install polaris-audit
polaris scan https://example.com
```

```
  POLARIS SCAN REPORT — example.com
  ──────────────────────────────────────────────

  Privacy        72/100  ██████████████░░░░░░  3 issues
  Security       89/100  █████████████████░░░  1 issue
  Accessibility  61/100  ████████████░░░░░░░░  7 issues
  Performance    84/100  ████████████████░░░░  2 issues

  Overall        76/100

  Critical: 2  |  Warning: 8  |  Info: 3

  → Full report: polaris-report-example.com.json
```

Most audit tools do one thing. Lighthouse does performance. pa11y does accessibility. Various GDPR scanners check cookies. Polaris checks all four in one pass — because in practice, you need to know about all of them before you ship.

---

## What it actually checks

### Privacy & GDPR Compliance

- **Cookie consent detection** — finds consent banners, checks for pre-consent cookie violations (cookies set before the user clicks "accept")
- **Consent Management Platforms** — detects Cookiebot, OneTrust, CookiePro, TrustArc, Usercentrics, CookieYes, Klaro
- **Third-party service classification** — identifies 50+ services and categorizes them by GDPR consent requirements:
  - *Essential* (no consent needed): Cloudflare, CDNs, reCAPTCHA
  - *Analytics* (basic consent): Google Analytics, Plausible, Matomo, Hotjar, Clarity, FullStory
  - *Marketing* (explicit consent required): Facebook Pixel, Google Ads, LinkedIn Insight, Twitter Pixel, TikTok Pixel
  - *Fonts* (privacy concern — IP tracking): Google Fonts, Adobe Fonts
- **Privacy policy analysis** — detects privacy policy links in 8 languages, validates content for required GDPR elements (data retention, subject rights, processing basis)
- **Consent quality** — checks for pre-ticked boxes, withdrawal mechanisms, granularity of consent categories
- **Data subject rights** — detects implementation of right to erasure, data portability, rectification, access
- **Data processing scope** — identifies contact forms, login/registration, e-commerce, and assesses GDPR applicability

### Security

- **HTTPS & SSL** — validates certificate, checks expiry, detects TLS version, flags HTTP-to-HTTPS redirect issues
- **Security headers** — checks for Strict-Transport-Security (HSTS), Content-Security-Policy (CSP), X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- **Mixed content** — finds HTTP images, scripts, and stylesheets loaded on HTTPS pages
- **Cookie security** — validates Secure, HttpOnly, and SameSite flags on cookies
- **Form security** — detects forms POSTing sensitive data (passwords, emails) over HTTP

### Accessibility (WCAG)

- **Document structure** — page title, language attribute, heading hierarchy (skipped levels, multiple H1s)
- **Landmarks** — semantic HTML (`<main>`, `<nav>`, `<header>`, `<footer>`) and ARIA roles
- **Images** — missing or empty alt attributes on content images, SVG accessibility (`<title>`, `<desc>`)
- **Forms** — inputs without labels, missing ARIA labeling, required field indicators, fieldset/legend structure, autocomplete attributes
- **Media** — video without captions/controls, audio without transcripts, figures without figcaptions
- **Navigation** — skip links, keyboard focus management, breadcrumbs
- **Color** — color-only error/success indicators, contrast issues
- **Tables** — missing headers, scope attributes, captions

### Performance

- **Compression** — checks for gzip/brotli content encoding
- **Caching** — validates Cache-Control, Expires, ETag, Last-Modified headers on static resources
- **Images** — flags unoptimized formats (PNG/JPG without WebP/AVIF alternatives)
- **JavaScript** — counts render-blocking scripts (missing async/defer), detects unminified bundles
- **CSS** — flags excess stylesheets, unminified CSS, large inline styles
- **Resource hints** — checks for preload, prefetch, dns-prefetch on critical resources
- **Page weight** — measures total page size, flags pages over 500KB

---

## Usage

```bash
# Scan a single URL
polaris scan https://example.com

# Scan multiple URLs from a file
polaris scan --input urls.txt

# Choose output format
polaris scan https://example.com --format json
polaris scan https://example.com --format json -o report.json

# Enable JavaScript rendering (uses Playwright)
polaris scan https://example.com --js

# Verbose output with per-issue details
polaris scan https://example.com -v

# CI-friendly: exit with non-zero code if score is below threshold
polaris scan https://example.com --fail-under 80
```

## Output formats

**Terminal** (default) — colored summary with scores and top issues.

**JSON** — full structured report with every check, suitable for CI pipelines and custom dashboards.

## Installation

```bash
pip install polaris-audit
```

For JavaScript-rendered pages (SPAs, React apps, etc.):

```bash
pip install polaris-audit[js]
playwright install chromium
```

Requires Python 3.10+.

---

## Why this exists

I built a full SaaS platform around this scanner — authentication, billing, dashboards, the works. Then I realized the scanner itself was the most useful part. So I stripped everything else away and released it as a CLI.

The privacy/GDPR checker in particular fills a gap. Most tools either do surface-level keyword matching ("does the page mention GDPR?") or cost hundreds per month. Polaris actually classifies your third-party services by consent tier, detects pre-consent violations, and validates consent mechanisms — the stuff that actually matters for compliance.

## Non-goals

- **This is not a penetration testing tool.** The security checks cover headers, SSL, and common misconfigurations. It won't find SQL injection or XSS vulnerabilities.
- **This is not Lighthouse.** The performance checks are header and markup-based. It doesn't measure Core Web Vitals (LCP, FID, CLS) — use Lighthouse for that.
- **This is not a legal compliance certificate.** The GDPR checks are technical indicators, not legal advice.

---

## Use in CI/CD

```yaml
# GitHub Actions example
- name: Audit website
  run: |
    pip install polaris-audit
    polaris scan https://staging.example.com --fail-under 75 --format json -o audit.json
```

```yaml
# GitLab CI example
audit:
  script:
    - pip install polaris-audit
    - polaris scan $STAGING_URL --fail-under 75
  artifacts:
    paths:
      - polaris-report-*.json
```

---

## Development

```bash
git clone https://github.com/polaris-audit/polaris-audit.git
cd polaris-audit
pip install -e ".[dev]"
polaris scan https://example.com
```

## Contributing

Issues and PRs welcome. The checker architecture is modular — each pillar is a self-contained module, so adding new checks is straightforward.

## License

MIT
