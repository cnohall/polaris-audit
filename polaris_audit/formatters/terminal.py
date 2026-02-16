"""Terminal output formatter with colored scores and progress bars."""

import sys
from typing import Dict, Any, List
from urllib.parse import urlparse


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if sys.platform == "win32":
        # Windows 10+ supports ANSI via virtual terminal processing
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(text: str, color: str) -> str:
    """Wrap text in color codes if terminal supports it."""
    if not _supports_color():
        return text
    return f"{color}{text}{Colors.RESET}"


def _score_color(score: int) -> str:
    """Get color for a score value."""
    if score >= 80:
        return Colors.BRIGHT_GREEN
    elif score >= 60:
        return Colors.BRIGHT_YELLOW
    else:
        return Colors.BRIGHT_RED


def _bar(score: int, width: int = 20) -> str:
    """Create a progress bar for a score."""
    filled = round(score / 100 * width)
    empty = width - filled
    color = _score_color(score)
    # Use ASCII-safe characters for Windows compatibility
    return _c("#" * filled, color) + _c("-" * empty, Colors.DIM)


def _severity_color(severity: str) -> str:
    """Get color for issue severity."""
    if severity == "critical":
        return Colors.BRIGHT_RED
    elif severity == "warning":
        return Colors.BRIGHT_YELLOW
    else:
        return Colors.CYAN


def _count_by_severity(issues: List[Dict]) -> Dict[str, int]:
    """Count issues by severity."""
    counts = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        sev = issue.get("severity", "info")
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1
    return counts


# Mapping from result["checks"] keys to human-readable labels, grouped by pillar
PASS_CHECKS = {
    "security": [
        ("security_uses_https", "HTTPS enabled"),
        ("security_http_redirects_to_https", "HTTP redirects to HTTPS"),
        ("security_ssl_valid", "SSL certificate valid"),
        ("security_strict-transport-security_present", "HSTS header present"),
        ("security_content-security-policy_present", "Content-Security-Policy present"),
        ("security_x-frame-options_present", "X-Frame-Options present"),
        ("security_x-content-type-options_present", "X-Content-Type-Options present"),
        ("security_referrer-policy_present", "Referrer-Policy present"),
        ("security_permissions-policy_present", "Permissions-Policy present"),
    ],
    "privacy": [
        ("privacy_policy_cookie_consent_found", "Cookie consent banner detected"),
        ("privacy_policy_cookie_policy_link_found", "Cookie policy link present"),
        ("privacy_policy_cookie_consent_withdrawal_found", "Consent withdrawal available"),
        ("privacy_policy_has_reject_button", "Cookie reject option available"),
        ("privacy_policy_granular_consent_found", "Granular consent options"),
        ("privacy_policy_data_subject_rights_found", "Data subject rights documented"),
        ("privacy_policy_data_retention_found", "Data retention policy found"),
        ("privacy_policy_lawful_basis_disclosed", "Lawful basis disclosed"),
    ],
    "accessibility": [
        ("accessibility_form_accessibility_score", None),  # numeric, skip
        ("accessibility_error_handling_present", "Form error handling present"),
    ],
    "performance": [],
}


def _get_passes(result: Dict[str, Any], category: str) -> List[str]:
    """Extract passing checks for a category from result['checks']."""
    checks = result.get("checks", {})
    passes = []

    for key, label in PASS_CHECKS.get(category, []):
        if label is None:
            continue
        value = checks.get(key)
        if value is True:
            passes.append(label)

    # Security: count zero mixed content and insecure forms as passes
    if category == "security":
        if checks.get("security_mixed_content_issues") == 0:
            passes.append("No mixed content")
        if checks.get("security_insecure_forms") == 0:
            passes.append("All forms use HTTPS")
        insecure = checks.get("security_insecure_cookies", 0)
        total = checks.get("security_total_cookies", 0)
        if total > 0 and insecure == 0:
            passes.append("All cookies have security flags")

    return passes


def format_result(result: Dict[str, Any], verbose: bool = False, js: bool = False) -> str:
    """Format a scan result for terminal output.

    Args:
        result: Scan result dictionary from AssessmentScanner.
        verbose: Whether to show detailed issue information.
        js: Whether JavaScript rendering was enabled.

    Returns:
        Formatted string for terminal display.
    """
    lines = []
    url = result.get("url", "unknown")
    domain = urlparse(url).netloc or url

    # Header
    lines.append("")
    lines.append(_c(f"  POLARIS SCAN REPORT - {domain}", Colors.BOLD))
    lines.append(_c("  " + "-" * 46, Colors.DIM))
    lines.append("")

    if not result.get("reachable", False):
        error_msgs = [i["message"] for i in result.get("issues", []) if i.get("severity") == "critical"]
        error_text = error_msgs[0] if error_msgs else "Could not reach URL"
        lines.append(_c(f"  Error: {error_text}", Colors.BRIGHT_RED))
        lines.append("")
        return "\n".join(lines)

    # Pillar scores
    pillars = [
        ("Privacy", result.get("privacy_score", 0), "privacy"),
        ("Security", result.get("security_score", 0), "security"),
        ("Accessibility", result.get("accessibility_score", 0), "accessibility"),
        ("Performance", result.get("performance_score", 0), "performance"),
    ]

    for name, score, category in pillars:
        issues = [i for i in result.get("business_issues", []) if i.get("category") == category]
        issue_count = len(issues)
        issue_text = f"{issue_count} issue{'s' if issue_count != 1 else ''}"

        score_str = _c(f"{score}/100", _score_color(score))
        lines.append(f"  {name:<15} {score_str}  {_bar(score)}  {_c(issue_text, Colors.DIM)}")

    lines.append("")

    # Overall score
    overall = result.get("overall_score", 0)
    lines.append(f"  {'Overall':<15} {_c(f'{overall}/100', Colors.BOLD + _score_color(overall))}")
    lines.append("")

    # Issue severity summary
    all_issues = result.get("business_issues", []) + result.get("issues", [])
    severity_counts = _count_by_severity(all_issues)
    parts = []
    if severity_counts["critical"]:
        parts.append(_c(f"Critical: {severity_counts['critical']}", Colors.BRIGHT_RED))
    if severity_counts["warning"]:
        parts.append(_c(f"Warning: {severity_counts['warning']}", Colors.BRIGHT_YELLOW))
    if severity_counts["info"]:
        parts.append(_c(f"Info: {severity_counts['info']}", Colors.CYAN))
    if parts:
        lines.append("  " + "  |  ".join(parts))
        lines.append("")

    # Verbose: show passing checks per pillar
    if verbose:
        has_passes = False
        for name, _score, category in pillars:
            passes = _get_passes(result, category)
            if passes:
                if not has_passes:
                    lines.append(_c("  Passed:", Colors.BOLD))
                    lines.append("")
                    has_passes = True
                for label in passes:
                    lines.append(f"  {_c('+', Colors.BRIGHT_GREEN)} [{category.upper()}] {label}")
        if has_passes:
            lines.append("")

    # Verbose: show individual issues
    if verbose and result.get("business_issues"):
        lines.append(_c("  Issues:", Colors.BOLD))
        lines.append("")

        for issue in sorted(result["business_issues"], key=lambda i: i.get("priority", {}).get("order", 99)):
            priority = issue.get("priority", {})
            order = priority.get("order", 3)
            if order == 1:
                marker = _c("!", Colors.BRIGHT_RED)
            elif order == 2:
                marker = _c("*", Colors.BRIGHT_YELLOW)
            else:
                marker = _c("-", Colors.CYAN)

            category = issue.get("category", "").upper()
            title = issue.get("title", "Unknown issue")
            lines.append(f"  {marker} [{category}] {title}")
            if issue.get("impact"):
                lines.append(_c(f"    {issue['impact']}", Colors.DIM))
            lines.append("")

    # Scan time
    scan_time = result.get("scan_time", 0)
    lines.append(_c(f"  Scanned in {scan_time:.1f}s", Colors.DIM))

    # JS tip
    if not js:
        lines.append(_c("  Tip: Use --js for JavaScript-heavy sites (SPAs, React, Vue, etc.)", Colors.DIM))

    lines.append("")

    return "\n".join(lines)


def format_results(results: List[Dict[str, Any]], verbose: bool = False, js: bool = False) -> str:
    """Format multiple scan results."""
    parts = []
    for result in results:
        parts.append(format_result(result, verbose=verbose, js=js))
    return "\n".join(parts)
