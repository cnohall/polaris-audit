from typing import Dict, Any, List


class PrivacySummaryService:
    """Handles privacy summary building and next steps."""

    def build_privacy_summary(self, result: Dict[str, Any]) -> None:
        """Build comprehensive privacy summary."""
        checks = result.get("checks", {})
        privacy_details = result.get("privacy_details", {})

        # Use cookie analysis results as primary source, fallback to privacy checker results
        privacy_policy_found = (
            privacy_details.get("privacy_policy_found", False) or
            checks.get("gdpr_privacy_policy_link_found", False)
        )

        cookie_banner_found = (
            privacy_details.get("cookie_banner_found", False) or
            checks.get("gdpr_cookie_consent_found", False)
        )

        result["privacy_summary"] = {
            "cookies_before_consent": privacy_details.get("cookies_before_consent", False),
            "privacy_policy_found": privacy_policy_found,
            "cookie_banner_found": cookie_banner_found,
            "third_party_count": len(result.get("third_party_services", [])),
            "compliance_status": self._get_privacy_status_message(result.get("privacy_score", 0)),
            "next_steps": self._get_privacy_next_steps(result)
        }

    def _get_privacy_status_message(self, score: int) -> str:
        """Get user-friendly privacy status message."""
        if score >= 90:
            return "You're in great shape for privacy compliance"
        elif score >= 70:
            return "Good progress, just a few items to address"
        elif score >= 50:
            return "Some important items need attention"
        else:
            return "Several critical items need immediate attention"

    def _get_privacy_next_steps(self, result: Dict[str, Any]) -> List[str]:
        """Get prioritized next steps for privacy."""
        steps = []
        privacy_issues = [i for i in result.get("business_issues", []) if i["category"] == "privacy"]

        high_priority = [i for i in privacy_issues if i["priority"]["order"] == 1]
        if high_priority:
            steps.append(f"Fix {len(high_priority)} critical privacy issue(s) first")

        medium_priority = [i for i in privacy_issues if i["priority"]["order"] == 2]
        if medium_priority:
            steps.append(f"Then address {len(medium_priority)} important item(s)")

        return steps