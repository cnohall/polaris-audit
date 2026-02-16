"""
Simple Scoring Service
One source of truth for all website scoring.
"""

from typing import Dict, Any


class ScoringService:
    """Simple, clear scoring service with transparent math."""
    
    def __init__(self):
        # Category weights for overall score
        self.weights = {
            "security": 0.35,
            "privacy": 0.25,
            "accessibility": 0.25,
            "performance": 0.15
        }
        
        # Penalty points deducted from 100 for each issue type
        self.penalties = {
            "security": {
                "must_fix": 8,
                "should_fix": 4,
                "nice_to_have": 2,
                "missing_https": 15,
                "invalid_ssl": 10,
                "ssl_expires_soon": 5,
                "missing_headers": 5,
                "invalid_headers": 3,
                "mixed_content": 2,
                "insecure_forms": 8,
            },
            "accessibility": {
                "must_fix": 10,
                "should_fix": 5,
                "nice_to_have": 1,
                "missing_page_title": 5,
                "missing_html_lang": 5,
                "missing_main_landmark": 3,
                "h1_count_issue": 4,
            },
            "privacy": {
                "must_fix": 8,
                "should_fix": 4,
                "nice_to_have": 2,
                "missing_privacy_policy": 15,
                "missing_cookie_consent": 10,
                "cookies_before_consent": 12,
            },
            "performance": {
                "must_fix": 15,
                "should_fix": 8,
                "nice_to_have": 3,
                "unoptimized_images": 10,
                "caching_issues": 8,
                "compression_issues": 10,
                "large_page_size": 15,
            }
        }
    
    def calculate_scores(self, result: Dict[str, Any]) -> None:
        """Calculate all scores using simple penalty-based methodology."""
        # Clean up priority objects to ensure they're complete
        self._cleanup_priority_objects(result)
        
        # Calculate individual category scores
        security_score = self._calculate_security_score(result)
        privacy_score = self._calculate_privacy_score(result)
        accessibility_score = self._calculate_accessibility_score(result)
        performance_score = self._calculate_performance_score(result)
        
        # Calculate weighted overall score
        overall_score = round(
            security_score * self.weights["security"] +
            privacy_score * self.weights["privacy"] +
            accessibility_score * self.weights["accessibility"] +
            performance_score * self.weights["performance"]
        )
        
        # Set the ONLY scores (no duplicates)
        result["overall_score"] = overall_score
        result["security_score"] = security_score
        result["privacy_score"] = privacy_score
        result["accessibility_score"] = accessibility_score
        result["performance_score"] = performance_score
        
        # Add simple score breakdown
        result["score_breakdown"] = {
            "overall": overall_score,
            "security": security_score,
            "privacy": privacy_score,
            "accessibility": accessibility_score,
            "performance": performance_score,
            "calculation_method": "penalty_from_100",
            "weights": self.weights
        }
    
    def _calculate_security_score(self, result: Dict[str, Any]) -> int:
        """Calculate security score starting from 100 and deducting penalties."""
        business_issues = result.get("business_issues", [])
        
        score = 100
        
        # Business issues penalties (these handle all security issues including infrastructure)
        security_issues = [issue for issue in business_issues if issue["category"] == "security"]
        for issue in security_issues:
            priority = issue.get("priority", {})
            if isinstance(priority, dict):
                if priority.get("order") == 1:  # must_fix
                    score -= self.penalties["security"]["must_fix"]
                elif priority.get("order") == 2:  # should_fix
                    score -= self.penalties["security"]["should_fix"]
                else:  # nice_to_have
                    score -= self.penalties["security"]["nice_to_have"]
        
        return max(0, score)
    
    def _cleanup_priority_objects(self, result: Dict[str, Any]) -> None:
        """Ensure all priority objects have complete structure."""
        business_issues = result.get("business_issues", [])
        
        for issue in business_issues:
            if "priority" in issue and isinstance(issue["priority"], dict):
                priority = issue["priority"]
                # Ensure all required fields are present
                issue["priority"] = {
                    "color": priority.get("color", "#10b981"),
                    "label": priority.get("label", "Unknown"),
                    "order": priority.get("order", 3)
                }
    
    def _calculate_privacy_score(self, result: Dict[str, Any]) -> int:
        """Calculate privacy score starting from 100 and deducting penalties."""
        business_issues = result.get("business_issues", [])
        
        score = 100
        
        # Business issues penalties (these handle all privacy issues including infrastructure)
        privacy_issues = [issue for issue in business_issues if issue["category"] == "privacy"]
        for issue in privacy_issues:
            priority = issue.get("priority", {})
            if isinstance(priority, dict):
                if priority.get("order") == 1:  # must_fix
                    score -= self.penalties["privacy"]["must_fix"]
                elif priority.get("order") == 2:  # should_fix
                    score -= self.penalties["privacy"]["should_fix"]
                else:  # nice_to_have
                    score -= self.penalties["privacy"]["nice_to_have"]
        
        return max(0, score)
    
    def _calculate_accessibility_score(self, result: Dict[str, Any]) -> int:
        """Calculate accessibility score starting from 100 and deducting penalties."""
        checks = result.get("checks", {})
        business_issues = result.get("business_issues", [])
        
        score = 100
        
        # Critical accessibility checks
        if not checks.get("accessibility_page_title_present", False):
            score -= self.penalties["accessibility"]["missing_page_title"]
        
        if not checks.get("accessibility_html_lang_present", False):
            score -= self.penalties["accessibility"]["missing_html_lang"]
        
        if not checks.get("accessibility_main_landmark_present", False):
            score -= self.penalties["accessibility"]["missing_main_landmark"]
        
        # H1 count check
        h1_count = checks.get("accessibility_h1_count", 0)
        if h1_count != 1:
            score -= self.penalties["accessibility"]["h1_count_issue"]
        
        # Business issues penalties
        accessibility_issues = [issue for issue in business_issues if issue["category"] == "accessibility"]
        for issue in accessibility_issues:
            priority = issue.get("priority", {})
            if isinstance(priority, dict):
                if priority.get("order") == 1:  # must_fix
                    score -= self.penalties["accessibility"]["must_fix"]
                elif priority.get("order") == 2:  # should_fix
                    score -= self.penalties["accessibility"]["should_fix"]
                else:  # nice_to_have
                    score -= self.penalties["accessibility"]["nice_to_have"]
        
        return max(0, score)
    
    def _calculate_performance_score(self, result: Dict[str, Any]) -> int:
        """Calculate performance score starting from 100 and deducting penalties from business issues only."""
        business_issues = result.get("business_issues", [])

        score = 100

        # Only use business issues penalties (no double counting from checks)
        # The performance checker creates business issues that represent all performance problems
        performance_issues = [issue for issue in business_issues if issue["category"] == "performance"]
        for issue in performance_issues:
            priority = issue.get("priority", {})
            if isinstance(priority, dict):
                if priority.get("order") == 1:  # must_fix
                    score -= self.penalties["performance"]["must_fix"]
                elif priority.get("order") == 2:  # should_fix
                    score -= self.penalties["performance"]["should_fix"]
                else:  # nice_to_have
                    score -= self.penalties["performance"]["nice_to_have"]

        return max(0, score)
