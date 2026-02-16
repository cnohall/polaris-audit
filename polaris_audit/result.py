from typing import Dict, Any
import time


class ScanResultBuilder:
    """Builds scan result objects."""
    
    @staticmethod
    def create_result_template(url: str) -> Dict[str, Any]:
        """Create a new scan result template."""
        return {
            "url": url,
            "reachable": False,
            "final_url": None,
            "http_status": None,
            "overall_score": 0,
            "accessibility_score": 0,
            "privacy_score": 0,
            "security_score": 0,
            "compliance_score": 0.0,  # Legacy
            "issues": [],
            "business_issues": [],
            "checks": {},
            "privacy_details": {},
            "cookies_found": [],
            "third_party_services": [],
            "scan_time": 0.0,
            "ssl_expires_in_days": None,
            "estimated_fix_time_minutes": 0,
            "quick_wins_count": 0,
            "must_fix_count": 0,
        }
    
    @staticmethod
    def add_http_info(result: Dict[str, Any], response) -> None:
        """Add HTTP response information to result."""
        result["reachable"] = True
        result["final_url"] = response.url
        result["http_status"] = response.status_code
    
    @staticmethod
    def add_error_info(result: Dict[str, Any], error: str, start_time: float) -> None:
        """Add error information to result."""
        result["issues"].append({
            "message": f"Fetch error: {error}",
            "severity": "critical",
            "category": "network"
        })
        result["scan_time"] = result.get("scan_time", 0) + (time.time() - start_time)
