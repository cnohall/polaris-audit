"""
Privacy compliance checker for Polaris Audit.

This module provides a unified interface for all privacy compliance checks (GDPR, CCPA, etc.).
It imports and coordinates specialized checkers for different aspects of privacy compliance.
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from requests import Response
from .base import BaseChecker
from .cookie import CookieChecker
from .privacy_policy import PrivacyPolicyChecker
from .consent import ConsentChecker
from .data_processing import DataProcessingChecker

logger = logging.getLogger(__name__)


class PrivacyChecker(BaseChecker):
    """Checks for privacy compliance indicators (GDPR, CCPA, etc.) with business-friendly reporting and reduced false flags."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the privacy checker with specialized modules."""
        super().__init__(config)
        self.cookie_checker = CookieChecker(self)
        self.privacy_policy_checker = PrivacyPolicyChecker(self)
        self.consent_checker = ConsentChecker(self)
        self.data_processing_checker = DataProcessingChecker(self)

    @property
    def name(self) -> str:
        return "privacy"

    def check(self, response: Response, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Perform privacy compliance checks (GDPR, CCPA, etc.) using specialized modules."""
        language = self.config.get("language", "en")
        phrases = self.config.get("phrases", {})

        if soup:
            # Assess data processing scope first to avoid false flags
            self.data_processing_checker.assess_data_processing_scope(soup, result)
            
            # Run full checks if we have parsed HTML
            self.privacy_policy_checker.check_privacy_policy_link(soup, phrases, language, result)
            self.privacy_policy_checker.check_privacy_policy_content(soup, result)
            self.privacy_policy_checker.check_privacy_policy_accessibility(soup, result)
            self.privacy_policy_checker.check_privacy_policy_language(soup, result)
            self.privacy_policy_checker.check_privacy_policy_updates(soup, result)
            
            self.cookie_checker.check_cookie_consent(soup, phrases, language, result)
            self.cookie_checker.check_cookie_banner_implementation(soup, result)
            self.cookie_checker.check_cookie_categories(result)
            self.cookie_checker.check_cookie_policy_link(soup, result)
            self.cookie_checker.check_cookie_consent_quality(soup, result)
            
            self.consent_checker.check_consent_quality(soup, result)
            self.consent_checker.check_consent_granularity(soup, result)
            self.consent_checker.check_consent_freely_given(soup, result)
            self.consent_checker.check_consent_specific(soup, result)
            self.consent_checker.check_consent_withdrawal_ease(soup, result)
            
            self.data_processing_checker.check_data_subject_rights(soup, result)
            self.data_processing_checker.check_data_retention_policies(soup, result)
            self.data_processing_checker.check_data_processing_lawfulness(soup, result)
            self.data_processing_checker.check_data_breach_procedures(soup, result)
        else:
            # If no HTML parsing, use cookie analysis results
            privacy_details = result.get("privacy_details", {})
            self.set_check_result(result, "privacy_policy_link_found", privacy_details.get("privacy_policy_found", False))
            self.set_check_result(result, "cookie_consent_found", privacy_details.get("cookie_banner_found", False))
            self.data_processing_checker.check_third_party_services(result)
        
        # Always check for cookie pre-consent violations (regardless of HTML parsing)
        self.cookie_checker.check_cookie_pre_consent_violation(result)
            
        # Score calculation is now handled by UnifiedScoringService
        # self._calculate_privacy_score(result)

    def _calculate_privacy_score(self, result: dict) -> None:
        """Calculate GDPR compliance score with context-aware penalties."""
        checks = result.get("checks", {})
        business_issues = result.get("business_issues", [])
        privacy_details = result.get("privacy_details", {})
        scope = checks.get("data_processing_scope", {})
        
        score = 100
        
        # Get comprehensive detection results
        privacy_policy_found = (
            checks.get("privacy_policy_link_found", False) or 
            privacy_details.get("privacy_policy_found", False)
        )
        
        cookie_consent_found = (
            checks.get("cookie_consent_found", False) or 
            privacy_details.get("cookie_banner_found", False)
        )
        
        # Context-aware penalties based on site complexity
        site_complexity = scope.get("site_complexity", "medium")
        gdpr_applies = scope.get("gdpr_likely_applies", True)
        
        if not gdpr_applies:
            # Minimal penalties for sites that don't process personal data
            logger.info("GDPR likely doesn't apply - minimal penalties")
            if not privacy_policy_found:
                score -= 10  # Minimal penalty
        else:
            # Apply penalties based on site complexity
            complexity_multiplier = {
                "simple": 0.5,
                "medium": 0.8, 
                "complex": 1.0
            }.get(site_complexity, 0.8)
            
            if not privacy_policy_found:
                penalty = int(12 * complexity_multiplier)  # Reduced from 25 to 12
                score -= penalty
                
            if not cookie_consent_found and scope.get("has_tracking", False):
                penalty = int(10 * complexity_multiplier)  # Reduced from 20 to 10
                score -= penalty
                
            # Major violation penalties (reduced)
            if privacy_details.get("cookies_before_consent", False):
                # Only full penalty for significant violations
                third_party_count = privacy_details.get("third_party_services_count", 0)
                if third_party_count > 1:  # More than basic analytics
                    score -= 12  # Reduced from 20
                else:
                    score -= 6  # Reduced from 10
            
            # Other compliance checks
            if not checks.get("data_subject_rights_found", False) and site_complexity != "simple":
                penalty = int(8 * complexity_multiplier)
                score -= penalty
                
            if checks.get("pre_ticked_consent_found", False):
                score -= 15  # Always full penalty for violations
                
            if not checks.get("consent_withdrawal_found", False) and cookie_consent_found and site_complexity != "simple":
                penalty = int(8 * complexity_multiplier)
                score -= penalty
                
            if not checks.get("data_retention_found", False) and site_complexity == "complex":
                score -= 5
        
        # Additional penalties for business issues (aligned with ImprovedScoreCalculationService)
        privacy_issues = [issue for issue in business_issues if issue["category"] == "privacy"]
        for issue in privacy_issues:
            priority_order = issue.get("priority", {}).get("order", 3)
            if priority_order == 1:  # must_fix
                score -= 8  # Aligned with ImprovedScoreCalculationService
            elif priority_order == 2:  # should_fix
                score -= 4  # Aligned with ImprovedScoreCalculationService
        
        # Apply positive scoring for excellent privacy practices
        bonus = 0
        if privacy_policy_found and checks.get("data_subject_rights_found", False):
            bonus += 5  # Comprehensive privacy policy bonus
        
        if cookie_consent_found and not checks.get("pre_ticked_consent_found", False):
            bonus += 5  # Granular consent bonus
        
        if checks.get("consent_withdrawal_found", False):
            bonus += 3  # Easy withdrawal bonus
        
        if not privacy_details.get("cookies_before_consent", False):
            bonus += 3  # No cookie violations bonus
        
        score = min(100, score + bonus)  # Apply bonus but cap at 100
        score = max(0, score)
        self.set_check_result(result, "privacy_score", score)
        result["privacy_score"] = score
        
        # Enhanced compliance level calculation
        if not gdpr_applies:
            compliance_level = "not_applicable"
        elif score >= 95:
            compliance_level = "excellent"
        elif score >= 85:
            compliance_level = "compliant"
        elif score >= 70:
            compliance_level = "mostly_compliant"
        elif score >= 50:
            compliance_level = "needs_work"
        else:
            compliance_level = "poor"
        
        # Update privacy_details with comprehensive results
        result["privacy_details"] = {
            **privacy_details,  # Preserve existing details
            "score": score,
            "compliance_level": compliance_level,
            "site_complexity": site_complexity,
            "gdpr_applies": gdpr_applies,
            "has_privacy_policy": privacy_policy_found,
            "has_cookie_consent": cookie_consent_found,
            "issues_found": len(privacy_issues),
            "critical_missing": len([i for i in privacy_issues if i.get("priority", {}).get("order", 3) == 1])
        }
        
        logger.info(f"GDPR Score: {score}/100 (complexity: {site_complexity}, applies: {gdpr_applies}, issues: {len(privacy_issues)})")