# polaris_audit/scanner.py
import time
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from polaris_audit.checkers.security import SecurityChecker
from polaris_audit.checkers.privacy import PrivacyChecker
from polaris_audit.checkers.accessibility import AccessibilityChecker
from polaris_audit.checkers.performance import PerformanceChecker
from polaris_audit.utils.http_client import HTTPClient
from polaris_audit.utils.config import load_config

from polaris_audit.services.cookie_analysis import CookieAnalysisService
from polaris_audit.services.scoring import ScoringService
from polaris_audit.services.action_plan import ActionPlanService
from polaris_audit.services.privacy_summary import PrivacySummaryService
from polaris_audit.services.content import ContentService
from polaris_audit.result import ScanResultBuilder

logger = logging.getLogger(__name__)


class AssessmentScanner:
    """Website assessment scanner across four pillars: Privacy, Security, Accessibility, Performance."""

    def __init__(self, config_path: str = None, js: bool = False):
        """Initialize scanner with configuration file (optional).

        Args:
            config_path: Path to config.json. Uses defaults if not provided.
            js: Whether to use JavaScript rendering (requires Playwright).
        """
        self.config = load_config(config_path) if config_path else {}
        self.js = js
        self.http_client = HTTPClient(self.config)
        self.checkers = [
            SecurityChecker(self.config),
            PrivacyChecker(self.config),
            AccessibilityChecker(self.config),
            PerformanceChecker(self.config),
        ]

        self.cookie_service = CookieAnalysisService()
        self.score_service = ScoringService()
        self.action_plan_service = ActionPlanService()
        self.privacy_service = PrivacySummaryService()
        self.content_service = ContentService()
        self.result_builder = ScanResultBuilder()

    def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan a single URL and return structured results.

        Args:
            url: URL to scan

        Returns:
            Dictionary with scores, issues, and detailed check results.
        """
        start_time = time.time()
        result = self.result_builder.create_result_template(url)

        try:
            response, error = self.http_client.fetch_url(url)
            if error or response is None:
                self.result_builder.add_error_info(result, error, start_time)
                return result

            self.result_builder.add_http_info(result, response)

            # Parse HTML if applicable
            soup = None
            content_type = response.headers.get("Content-Type", "").lower()
            if self.content_service.should_parse_html(content_type):
                try:
                    if self.js:
                        soup = self.content_service.get_rendered_soup(url)
                    else:
                        soup = BeautifulSoup(response.text, 'html.parser')

                    cookie_analysis = self.cookie_service.analyze_cookies_and_tracking(response, soup)
                    result["privacy_details"] = cookie_analysis
                    result["third_party_services"] = cookie_analysis.get("third_party_services", [])
                except Exception as e:
                    result["issues"].append({
                        "message": f"HTML parsing failed: {str(e)}",
                        "severity": "warning",
                        "category": "parsing"
                    })

                    # Fallback to basic HTML parsing
                    try:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        basic_analysis = self.cookie_service.analyze_cookies_and_tracking(response, soup)
                        result["privacy_details"] = basic_analysis
                        result["third_party_services"] = basic_analysis.get("third_party_services", [])
                    except Exception as basic_error:
                        result["issues"].append({
                            "message": f"Basic HTML parsing failed: {str(basic_error)}",
                            "severity": "warning",
                            "category": "parsing"
                        })
                        result["privacy_details"] = {
                            "cookies_before_consent": False,
                            "cookie_banner_found": False,
                            "privacy_policy_found": False,
                            "third_party_services_count": 0,
                            "tracking_services": [],
                            "third_party_services": []
                        }
                        result["third_party_services"] = []

            # Run all checkers
            for checker in self.checkers:
                try:
                    checker.check(response, soup, result)
                except Exception as e:
                    result["issues"].append({
                        "message": f"Error in {checker.__class__.__name__}: {str(e)}",
                        "severity": "warning",
                        "category": "checker-error"
                    })

            # Calculate scores
            self.score_service.calculate_scores(result)
            self.privacy_service.build_privacy_summary(result)

            # Map SSL data
            ssl_days = result.get("checks", {}).get("security_ssl_days_until_expiry")
            if ssl_days is not None:
                result["ssl_expires_in_days"] = ssl_days

            # Enrich fix instructions (pro) and calculate action plan
            try:
                from polaris_audit_pro import enrich_fix_instructions
                enrich_fix_instructions(result)
            except ImportError:
                pass
            self.action_plan_service.calculate_action_plan_metrics(result)

        except Exception as e:
            result["issues"].append({
                "message": f"Scan failed: {str(e)}",
                "severity": "critical",
                "category": "scanner-error"
            })

        result["scan_time"] = time.time() - start_time
        return result
