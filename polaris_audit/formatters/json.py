"""JSON output formatter for scan results."""

import json
from typing import Dict, Any, List


def format_result(result: Dict[str, Any]) -> str:
    """Format a single scan result as JSON."""
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


def format_results(results: List[Dict[str, Any]]) -> str:
    """Format multiple scan results as JSON."""
    output = {
        "results": results,
        "summary": _build_summary(results),
    }
    return json.dumps(output, indent=2, ensure_ascii=False, default=str)


def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a summary across all scanned URLs."""
    if not results:
        return {}

    total = len(results)
    reachable = sum(1 for r in results if r.get("reachable"))

    avg = lambda key: round(sum(r.get(key, 0) for r in results) / total) if total else 0

    return {
        "urls_scanned": total,
        "urls_reachable": reachable,
        "average_overall_score": avg("overall_score"),
        "average_privacy_score": avg("privacy_score"),
        "average_security_score": avg("security_score"),
        "average_accessibility_score": avg("accessibility_score"),
        "average_performance_score": avg("performance_score"),
    }
