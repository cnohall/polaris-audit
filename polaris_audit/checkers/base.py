# api/checkers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

PRIORITY_MAPPING = {
    "must_fix": {"color": "#ef4444", "label": "High Priority", "order": 1},
    "should_fix": {"color": "#f59e0b", "label": "Medium Priority", "order": 2}, 
    "nice_to_have": {"color": "#10b981", "label": "Low Priority", "order": 3}
}

# Ensure all priority objects have complete structure
def ensure_complete_priority(priority):
    """Ensure priority object has all required fields."""
    if isinstance(priority, dict):
        return {
            "color": priority.get("color", "#10b981"),
            "label": priority.get("label", "Unknown"),
            "order": priority.get("order", 3)
        }
    return {"color": "#10b981", "label": "Unknown", "order": 3}

DIFFICULTY_MAPPING = {
    "easy": {"level": "easy", "description": "Easy"},
    "medium": {"level": "medium", "description": "Medium"},
    "hard": {"level": "hard", "description": "Hard"}
}

class BaseChecker(ABC):
    """Base class for all website checkers with business-friendly reporting."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @property
    @abstractmethod 
    def name(self) -> str:
        """Return the checker name."""
        pass

    @abstractmethod
    def check(self, response, soup: Optional[Any], result: dict) -> None:
        """Perform the actual check."""
        pass

    def set_check_result(self, result: dict, key: str, value: Any) -> None:
        """Set a check result value."""
        if "checks" not in result:
            result["checks"] = {}
        result["checks"][f"{self.name}_{key}"] = value

    def add_issue(self, result: dict, message: str, severity: str, category: str, 
                  fix_suggestion: str = None) -> None:
        """Add a traditional issue (for backwards compatibility)."""
        if "issues" not in result:
            result["issues"] = []
            
        issue = {
            "message": message,
            "severity": severity,
            "category": category,
            "checker": self.name
        }
        if fix_suggestion:
            issue["fix_suggestion"] = fix_suggestion
            
        result["issues"].append(issue)

    def add_business_issue(self, result: dict, title: str, impact: str, priority: str,
                        fix_time: int, difficulty: str, category: str, difficulty_description: str = None, **kwargs) -> None:
        """Add business issue with score impact calculation."""
        
        # Ensure priority object is complete
        priority_obj = ensure_complete_priority(PRIORITY_MAPPING.get(priority, PRIORITY_MAPPING["should_fix"]))
        
        issue = {
            "id": f"{category}_{title.lower().replace(' ', '_')}",
            "title": title,
            "impact": impact,
            "status": "open",
            "checker": self.name,
            "category": category,
            "priority": priority_obj,
            "difficulty": {
                "level": difficulty,
                "description": difficulty_description or DIFFICULTY_MAPPING.get(difficulty, DIFFICULTY_MAPPING["medium"])["description"]
            },
            "fix_time_display": f"{fix_time} minutes",
            "fix_time_minutes": fix_time,
            "score_impact": self._calculate_score_impact(category, priority),
            **kwargs
        }
        
        result.setdefault("business_issues", []).append(issue)

    def _format_time(self, minutes: int) -> str:
        """Format time in a user-friendly way."""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            remaining_mins = minutes % 60
            if remaining_mins == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours}h {remaining_mins}m"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days != 1 else ''}"

    def generate_monthly_summary(self, current_result: dict, previous_result: dict = None) -> dict:
        """Generate summary for monthly reports."""
        current_issues = current_result.get("business_issues", [])
        previous_issues = previous_result.get("business_issues", []) if previous_result else []
        
        # Track changes
        new_issues = []
        resolved_issues = []
        ongoing_issues = []
        
        current_ids = {issue["id"] for issue in current_issues}
        previous_ids = {issue["id"] for issue in previous_issues}
        
        new_issues = [issue for issue in current_issues if issue["id"] not in previous_ids]
        resolved_issues = [issue for issue in previous_issues if issue["id"] not in current_ids]
        ongoing_issues = [issue for issue in current_issues if issue["id"] in previous_ids]
        
        return {
            "checker": self.name,
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(current_issues),
            "new_issues": len(new_issues),
            "resolved_issues": len(resolved_issues),
            "ongoing_issues": len(ongoing_issues),
            "new_issues_details": new_issues,
            "resolved_issues_details": resolved_issues,
            "priority_breakdown": self._get_priority_breakdown(current_issues),
            "estimated_total_fix_time": sum(issue["fix_time_minutes"] for issue in current_issues),
            "quick_wins": [issue for issue in current_issues if issue["fix_time_minutes"] <= 30],
            "needs_help": [issue for issue in current_issues if self._get_difficulty_level(issue["difficulty"]) == "hard"]
        }
    
    def _get_priority_breakdown(self, issues: List[dict]) -> dict:
        """Get breakdown of issues by priority."""
        breakdown = {"must_fix": 0, "should_fix": 0, "nice_to_have": 0}
        for issue in issues:
            priority = issue["priority"]
            if isinstance(priority, dict):
                # Find the key that matches the priority
                for key, value in breakdown.items():
                    if key in issue["priority"]:
                        breakdown[key] += 1
                        break
        return breakdown

    def _get_difficulty_level(self, difficulty) -> str:
        """Extract difficulty level from either string or dict format."""
        if isinstance(difficulty, dict):
            return difficulty.get("level", "medium")
        elif isinstance(difficulty, str):
            return difficulty
        else:
            return "medium"

    def _calculate_score_impact(self, category: str, priority: str) -> dict:
        """Calculate the actual penalty points deducted from the score and potential improvement."""
        # Actual penalty points deducted from the score (aligned with individual checkers)
        penalty_points = {
            "must_fix": {"security": 8, "privacy": 8, "accessibility": 10, "performance": 15},
            "should_fix": {"security": 4, "privacy": 4, "accessibility": 5, "performance": 8}, 
            "nice_to_have": {"security": 2, "privacy": 2, "accessibility": 1, "performance": 3}
        }
        
        # Potential improvement points (what you gain by fixing)
        improvement_points = {
            "must_fix": {"security": 8, "privacy": 8, "accessibility": 10, "performance": 15},
            "should_fix": {"security": 4, "privacy": 4, "accessibility": 5, "performance": 8}, 
            "nice_to_have": {"security": 2, "privacy": 2, "accessibility": 1, "performance": 3}
        }
        
        penalty = penalty_points.get(priority, {}).get(category, 5)
        improvement = improvement_points.get(priority, {}).get(category, 5)
        
        return {
            "score_impact": penalty,
            "message": f"This issue deducts {penalty} points from your {category} score. Fixing it could improve your score by {penalty} points"
        }