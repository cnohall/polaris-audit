"""Polaris CLI — audit websites across Privacy, Security, Accessibility, and Performance."""

import sys
import importlib.resources
from pathlib import Path
from typing import Optional

import click

from polaris_audit import __version__
from polaris_audit.scanner import AssessmentScanner
from polaris_audit.utils.validation import validate_url
from polaris_audit.formatters import terminal as terminal_fmt
from polaris_audit.formatters import json as json_fmt
from polaris_audit.checks_registry import CHECKS


def _find_default_config() -> Optional[str]:
    """Find the bundled config.json shipped with the package."""
    # Check current working directory first
    cwd_config = Path.cwd() / "config.json"
    if cwd_config.exists():
        return str(cwd_config)

    # Check package directory
    try:
        ref = importlib.resources.files("polaris_audit") / "config.json"
        with importlib.resources.as_file(ref) as path:
            if path.exists():
                return str(path)
    except (FileNotFoundError, TypeError):
        pass

    return None


@click.group()
@click.version_option(version=__version__, prog_name="polaris")
def main():
    """Polaris - audit websites for Privacy, Security, Accessibility, and Performance.

    \b
    Quick start:
      polaris scan https://example.com          Run a scan
      polaris scan https://example.com -v       Detailed results
      polaris checks                            See what we check
    """
    pass


@main.command()
@click.option("--pillar", type=click.Choice(["security", "privacy", "accessibility", "performance"]),
              default=None, help="Show checks for a specific pillar only.")
@click.option("--format", "output_format", type=click.Choice(["terminal", "json"]), default="terminal",
              help="Output format.")
def checks(pillar, output_format):
    """List all 52 checks that Polaris runs during a scan.

    \b
    Covers four pillars:
      Security       HTTPS, headers, SSL, mixed content, cookies
      Privacy        GDPR, consent, cookies, third-party tracking
      Accessibility  WCAG, headings, forms, images, navigation
      Performance    Compression, caching, page weight, JS/CSS

    \b
    Examples:
      polaris checks                            All checks
      polaris checks --pillar security          Security only
      polaris checks --format json              Machine-readable
    """
    if output_format == "json":
        import json
        data = {pillar: CHECKS[pillar]} if pillar else CHECKS
        output = json.dumps(data, indent=2)
        sys.stdout.buffer.write(output.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()
        return

    pillars_to_show = [pillar] if pillar else list(CHECKS.keys())
    lines = []
    total = 0

    for p in pillars_to_show:
        info = CHECKS[p]
        lines.append("")
        lines.append(f"  {info['name']} ({len(info['checks'])} checks)")
        lines.append("  " + "-" * 46)
        for check in info["checks"]:
            lines.append(f"    {check['name']:<30} {check['description']}")
            total += 1
        lines.append("")

    lines.append(f"  Total: {total} checks across {len(pillars_to_show)} pillar{'s' if len(pillars_to_show) != 1 else ''}")
    lines.append("")

    output = "\n".join(lines)
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


@main.command()
@click.argument("url", required=False)
@click.option("--input", "input_file", type=click.Path(exists=True), help="File with URLs to scan (one per line, # comments ok).")
@click.option("--format", "output_format", type=click.Choice(["terminal", "json"]), default="terminal", help="Output format (default: terminal).")
@click.option("--config", "config_path", type=click.Path(exists=True), help="Custom config.json (uses built-in by default).")
@click.option("--js", is_flag=True, default=False, help="Render JavaScript with Playwright (slower, more accurate).")
@click.option("--fail-under", type=int, default=None, help="Exit code 1 if score below threshold (for CI).")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Show passing checks and detailed issues.")
@click.option("-o", "--output", "output_file", type=click.Path(), help="Write report to file instead of stdout.")
def scan(url, input_file, output_format, config_path, js, fail_under, verbose, output_file):
    """Scan a URL and score it across Privacy, Security, Accessibility, and Performance.

    Each pillar is scored 0-100. Issues are ranked by priority (must fix,
    should fix, nice to have) with actionable fix instructions.

    \b
    Examples:
      polaris scan https://example.com                Basic scan
      polaris scan https://example.com -v             With pass/fail details
      polaris scan https://example.com --js           JS rendering (SPAs)
      polaris scan https://example.com --format json  JSON output
      polaris scan --input urls.txt -o report.json    Batch scan to file
      polaris scan https://example.com --fail-under 80   CI gate
    """
    # Collect URLs
    urls = []
    if url:
        normalized, error = validate_url(url)
        if error:
            click.echo(f"Error: {error}", err=True)
            sys.exit(1)
        urls.append(normalized)

    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    normalized, error = validate_url(line)
                    if error:
                        click.echo(f"Skipping invalid URL '{line}': {error}", err=True)
                        continue
                    urls.append(normalized)

    if not urls:
        click.echo("Error: Provide a URL argument or --input file.", err=True)
        sys.exit(1)

    # Find config
    if not config_path:
        config_path = _find_default_config()

    # Initialize scanner
    scanner = AssessmentScanner(config_path=config_path, js=js)

    # Scan all URLs
    results = []
    for scan_url in urls:
        if output_format == "terminal" and len(urls) > 1:
            click.echo(f"Scanning {scan_url}...", err=True)
        result = scanner.scan_url(scan_url)
        results.append(result)

    # Format output
    if output_format == "json":
        if len(results) == 1:
            output = json_fmt.format_result(results[0])
        else:
            output = json_fmt.format_results(results)
    else:
        if len(results) == 1:
            output = terminal_fmt.format_result(results[0], verbose=verbose, js=js)
        else:
            output = terminal_fmt.format_results(results, verbose=verbose, js=js)

    # Write output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        if output_format == "terminal":
            click.echo(f"Report saved to {output_file}")
    else:
        # Write with proper encoding to handle Unicode on Windows
        sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
        sys.stdout.buffer.flush()

    # Check fail-under threshold
    if fail_under is not None:
        worst_score = min(r.get("overall_score", 0) for r in results)
        if worst_score < fail_under:
            click.echo(
                f"\nScore {worst_score} is below threshold {fail_under}.",
                err=True,
            )
            sys.exit(1)


if __name__ == "__main__":
    main()
