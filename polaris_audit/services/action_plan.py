from typing import Dict, Any, List


class ActionPlanService:
    """Handles action plan metrics and prioritization."""
    
    def calculate_action_plan_metrics(self, result: Dict[str, Any]) -> None:
        """Calculate action plan metrics like quick wins and must-fix counts."""
        business_issues = result.get("business_issues", [])
        
        # Count issues by priority AND fix time
        quick_wins = 0
        must_fix = 0
        quick_fixes = 0
        
        for issue in business_issues:
            priority = issue.get("priority", {})
            priority_order = priority.get("order", 0)
            fix_time = issue.get("fix_time_minutes", 0)
            
            # Must fix: High priority issues
            if priority_order == 1:
                must_fix += 1
            
            # Quick wins: Issues that can be fixed quickly (≤30 minutes) regardless of priority
            if fix_time <= 30:
                quick_fixes += 1
                
            # Legacy quick_wins: Medium and low priority (for backwards compatibility)
            if priority_order in [2, 3]:
                quick_wins += 1
        
        # Store both metrics
        result["quick_wins_count"] = quick_wins  # Legacy: medium/low priority
        result["quick_fixes_count"] = quick_fixes  # New: actual quick fixes by time
        result["must_fix_count"] = must_fix
        
        # Calculate estimated fix time
        total_fix_time = sum(
            issue.get("fix_time_minutes", 0) 
            for issue in business_issues
        )
        result["estimated_fix_time_minutes"] = total_fix_time
        
        # Add success messages for good scores
        success_messages = self._get_success_messages(result)
        result["success_messages"] = success_messages
        
        # Add business insights
        result["action_plan_insights"] = self._get_action_plan_insights(result, business_issues)

    def _get_success_messages(self, result: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate success messages for good scores."""
        success_messages = []
        
        if result.get("security_score", 0) >= 90:
            success_messages.append({
                "category": "security",
                "message": "Your website security is excellent!",
                "icon": "shield-check"
            })
        
        if result.get("privacy_score", 0) >= 90:
            success_messages.append({
                "category": "privacy", 
                "message": "Your GDPR compliance looks great!",
                "icon": "check-circle"
            })
            
        if result.get("accessibility_score", 0) >= 80:
            success_messages.append({
                "category": "accessibility",
                "message": "Your site is accessible to most users!",
                "icon": "users"
            })

        return success_messages

    def _get_action_plan_insights(self, result: Dict[str, Any], business_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate actionable insights for the action plan."""
        quick_fixes = [issue for issue in business_issues if issue.get("fix_time_minutes", 0) <= 30]
        high_impact_quick_wins = [issue for issue in quick_fixes if issue.get("priority", {}).get("order", 0) == 1]
        
        insights = {
            "total_issues": len(business_issues),
            "quick_fixes_available": len(quick_fixes),
            "high_impact_quick_wins": len(high_impact_quick_wins),
            "estimated_total_time": result.get("estimated_fix_time_minutes", 0),
            "recommended_start": self._get_recommended_start_order(business_issues),
            "quick_win_examples": self._get_quick_win_examples(quick_fixes),
            "priority_breakdown": self._get_priority_breakdown(business_issues)
        }
        
        return insights
    
    def _get_recommended_start_order(self, business_issues: List[Dict[str, Any]]) -> List[str]:
        """Get recommended order to tackle issues."""
        recommendations = []
        
        # Start with high-priority quick fixes
        high_priority_quick = [i for i in business_issues 
                              if i.get("priority", {}).get("order", 0) == 1 
                              and i.get("fix_time_minutes", 0) <= 30]
        
        if high_priority_quick:
            recommendations.append(f"Start with {len(high_priority_quick)} high-priority quick fixes")
        
        # Then other high-priority issues
        high_priority_other = [i for i in business_issues 
                              if i.get("priority", {}).get("order", 0) == 1 
                              and i.get("fix_time_minutes", 0) > 30]
        
        if high_priority_other:
            recommendations.append(f"Then tackle {len(high_priority_other)} high-priority complex issues")
        
        # Finally, quick wins for score improvement
        medium_quick = [i for i in business_issues 
                       if i.get("priority", {}).get("order", 0) == 2 
                       and i.get("fix_time_minutes", 0) <= 30]
        
        if medium_quick:
            recommendations.append(f"Improve scores with {len(medium_quick)} medium-priority quick fixes")
        
        return recommendations
    
    def _get_quick_win_examples(self, quick_fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get examples of quick fixes for motivation."""
        examples = []
        
        for issue in quick_fixes[:3]:  # Show up to 3 examples
            examples.append({
                "title": issue.get("title", "Unknown issue"),
                "fix_time": issue.get("fix_time_display", "Unknown time"),
                "impact": issue.get("impact", "Unknown impact"),
                "category": issue.get("category", "general")
            })
        
        return examples
    
    def _get_priority_breakdown(self, business_issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of issues by priority."""
        breakdown = {"must_fix": 0, "should_fix": 0, "nice_to_have": 0}
        
        for issue in business_issues:
            priority_order = issue.get("priority", {}).get("order", 0)
            if priority_order == 1:
                breakdown["must_fix"] += 1
            elif priority_order == 2:
                breakdown["should_fix"] += 1
            elif priority_order == 3:
                breakdown["nice_to_have"] += 1
        
        return breakdown
