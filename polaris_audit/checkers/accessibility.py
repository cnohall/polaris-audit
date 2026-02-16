"""
Accessibility checker for Polaris Audit.

This module provides a unified interface for all accessibility checks.
It imports and coordinates specialized checkers for different aspects of accessibility.
"""

import re
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from requests import Response
from .base import BaseChecker
from .color_contrast import ColorContrastChecker
from .navigation import NavigationChecker
from .form import FormChecker
from .media import MediaChecker

logger = logging.getLogger(__name__)


class AccessibilityChecker(BaseChecker):
    """Improved accessibility checker with modular design."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the accessibility checker with specialized modules."""
        super().__init__(config)
        self.color_checker = ColorContrastChecker(self)
        self.navigation_checker = NavigationChecker(self)
        self.form_checker = FormChecker(self)
        self.media_checker = MediaChecker(self)

    @property
    def name(self) -> str:
        return "accessibility"

    def check(self, response: Response, soup: Optional[BeautifulSoup], result: dict) -> None:
        """Perform comprehensive accessibility checks using specialized modules."""
        if soup:
            # Core accessibility checks
            self._check_page_title(soup, result)
            self._check_html_lang(soup, result)
            
            # Navigation accessibility
            self.navigation_checker.check_landmarks(soup, result)
            self.navigation_checker.check_heading_structure(soup, result)
            self.navigation_checker.check_link_accessibility(soup, result)
            self.navigation_checker.check_keyboard_focus(soup, result)
            self.navigation_checker.check_skip_links(soup, result)
            self.navigation_checker.check_navigation_structure(soup, result)
            self.navigation_checker.check_breadcrumbs(soup, result)
            
            # Media accessibility
            self.media_checker.check_image_alt_text(soup, result)
            self.media_checker.check_video_accessibility(soup, result)
            self.media_checker.check_audio_accessibility(soup, result)
            self.media_checker.check_image_sizing(soup, result)
            self.media_checker.check_figure_captions(soup, result)
            self.media_checker.check_svg_accessibility(soup, result)
            
            # Form accessibility
            self.form_checker.check_form_accessibility(soup, result)
            self.form_checker.check_form_error_handling(soup, result)
            self.form_checker.check_form_fieldset_legends(soup, result)
            self.form_checker.check_form_autocomplete(soup, result)
            self.form_checker.check_form_validation(soup, result)
            self.form_checker.check_form_submit_buttons(soup, result)
            
            # Color accessibility
            self.color_checker.check_color_indicators(soup, result)
            
            # Additional checks
            self._check_table_accessibility(soup, result)
            self._check_color_dependency(soup, result)
        else:
            self._set_default_values(result)
            
        # Score calculation is now handled by UnifiedScoringService
        # self._calculate_accessibility_score(result)
        logger.info(f"Accessibility checker completed: {len(result.get('business_issues', []))} issues found")

    def _set_default_values(self, result: dict) -> None:
        """Set default values when HTML parsing fails."""
        defaults = {
            "page_title_present": False,
            "html_lang_present": False,
            "landmarks_present": False,
            "h1_count": 0,
            "heading_structure_issues": 0,
            "img_alt_missing_count": 0,
            "form_accessibility_score": 100,
            "link_issues_count": 0,
            "keyboard_focus_score": 100,
            "color_dependency_issues": 0,
            "table_issues_count": 0,
            "media_accessibility_issues": 0,
            "error_handling_present": False
        }
        for key, value in defaults.items():
            self.set_check_result(result, key, value)

    def _check_page_title(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for proper page title."""
        try:
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else ""
            
            self.set_check_result(result, "page_title_present", bool(title_text))
            self.set_check_result(result, "page_title", title_text)
            
            if not title_text:
                self.add_business_issue(
                    result,
                    title="Add a page title",
                    impact="Search engines and screen readers can't understand what your page is about",
                    priority="must_fix",
                    fix_time=5,
                    difficulty="easy",
                    category="accessibility",
                    technical_details="Missing <title> tag in document head",
                    fix_instructions="Add a descriptive title between <title> tags in your page's <head> section",
                    business_value="Improves SEO and helps users understand page content",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Add Page Title",
                            "code": "<head>\n    <title>Your Page Title - Company Name</title>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n</head>",
                            "language": "html"
                        }
                    ]
                )
            elif len(title_text) < 10:
                self.add_business_issue(
                    result,
                    title="Make your page title more descriptive",
                    impact="Your page title is too short to be helpful for search engines and users",
                    priority="nice_to_have",
                    fix_time=5,
                    difficulty="easy",
                    category="accessibility",
                    technical_details=f"Page title is only {len(title_text)} characters",
                    fix_instructions="Expand your page title to better describe the page content and purpose",
                    business_value="Better SEO and user experience",
                    recurring_check=True
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking page title: {str(e)}", "warning", "accessibility")

    def _check_html_lang(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for html lang attribute."""
        try:
            html = soup.find("html")
            lang_val = html.get("lang") or html.get("xml:lang") if html else None

            self.set_check_result(result, "html_lang_present", bool(lang_val))
            
            if not lang_val:
                self.add_business_issue(
                    result,
                    title="Set your website's language",
                    impact="Screen readers can't properly pronounce your content",
                    priority="must_fix",
                    fix_time=5,
                    difficulty="easy",
                    category="accessibility",
                    technical_details="Missing lang attribute on <html> element",
                    fix_instructions="Add lang='en' (or your language code) to your <html> tag",
                    business_value="Makes your site accessible to screen reader users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Set Language",
                            "code": "<html lang=\"en\">\n    <!-- Your page content -->\n</html>",
                            "language": "html"
                        }
                    ]
                )

        except Exception as e:
            self.add_issue(result, f"Error checking language: {str(e)}", "warning", "accessibility")

    def _check_table_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Simple table accessibility check."""
        try:
            tables = soup.find_all("table")
            issues = 0
            total_tables = len(tables)
            problematic_tables = []

            for i, table in enumerate(tables):
                table_problems = []

                # Check for headers
                if not table.find_all(["th"]):
                    table_problems.append("missing table headers (th elements)")

                # Check for caption on larger tables
                cell_count = len(table.find_all("td"))
                if not table.find("caption") and cell_count > 6:  # Only for larger tables
                    table_problems.append(f"missing caption for data table with {cell_count} cells")

                # Check for proper header scope
                headers = table.find_all("th")
                if headers:
                    headers_without_scope = [th for th in headers if not th.get("scope")]
                    if headers_without_scope:
                        table_problems.append(f"{len(headers_without_scope)} headers missing scope attribute")

                if table_problems:
                    issues += 1

                    # Try to identify the table content
                    first_row_text = ""
                    first_row = table.find("tr")
                    if first_row:
                        first_row_text = first_row.get_text(strip=True)[:50]

                    table_identifier = f"Table #{i+1}"
                    if first_row_text:
                        table_identifier += f" (starts with: '{first_row_text}')"

                    problems_text = " and ".join(table_problems)
                    problematic_tables.append(f"{table_identifier} - {problems_text} (screen readers can't navigate the data properly)")

            self.set_check_result(result, "table_issues_count", issues)

            if issues > 0:
                self.add_business_issue(
                    result,
                    title="Improve table accessibility",
                    impact=f"{issues} tables are difficult for screen readers to understand",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="accessibility",
                    count=issues,
                    examples=problematic_tables,
                    total_elements=total_tables,
                    element_type="tables",
                    technical_details="Tables need proper headers and descriptions",
                    fix_instructions="Add table headers (th) and captions for data tables",
                    business_value="Makes data tables understandable for screen reader users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Table",
                            "code": "<table>\n    <caption>Monthly Sales Report</caption>\n    <thead>\n        <tr>\n            <th scope=\"col\">Month</th>\n            <th scope=\"col\">Sales</th>\n        </tr>\n    </thead>\n    <tbody>\n        <tr>\n            <th scope=\"row\">January</th>\n            <td>$10,000</td>\n        </tr>\n    </tbody>\n</table>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.add_issue(result, f"Error checking tables: {str(e)}", "warning", "accessibility")

    def _check_color_dependency(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for elements that rely only on color to convey information."""
        try:
            problematic_elements = []
            issues = 0

            # Check for color-only error indicators
            error_elements = soup.find_all(class_=re.compile(r'error|invalid|danger|red'))
            for elem in error_elements:
                # Check if element only uses color (no text, icon, or other indicator)
                text_content = elem.get_text(strip=True)

                # Check if this element itself is an icon/svg OR contains icons
                is_icon_element = elem.name in ['i', 'svg'] or any('icon' in cls.lower() or 'lucide' in cls.lower() for cls in elem.get('class', []))
                has_icon = is_icon_element or elem.find(['i', 'svg']) or any('icon' in cls for cls in elem.get('class', []))

                if not text_content and not has_icon:
                    issues += 1
                    elem_tag = elem.name
                    elem_classes = ' '.join(elem.get('class', []))
                    problematic_elements.append(f"{elem_tag.upper()} element with class '{elem_classes}' - uses only color to show errors (add text or icons)")

            # Check for success indicators
            success_elements = soup.find_all(class_=re.compile(r'success|valid|green'))
            for elem in success_elements:
                text_content = elem.get_text(strip=True)

                # Check if this element itself is an icon/svg OR contains icons
                is_icon_element = elem.name in ['i', 'svg'] or any('icon' in cls.lower() or 'lucide' in cls.lower() for cls in elem.get('class', []))
                has_icon = is_icon_element or elem.find(['i', 'svg']) or any('icon' in cls for cls in elem.get('class', []))

                if not text_content and not has_icon:
                    issues += 1
                    elem_tag = elem.name
                    elem_classes = ' '.join(elem.get('class', []))
                    problematic_elements.append(f"{elem_tag.upper()} element with class '{elem_classes}' - uses only color to show success (add text or icons)")

            # Check for required field indicators that might only use color
            required_indicators = soup.find_all('span', class_=re.compile(r'required|mandatory'))
            for elem in required_indicators:
                text_content = elem.get_text(strip=True)
                if not text_content or text_content == '*':
                    # Check if parent has text indicating required
                    parent_text = elem.parent.get_text(strip=True) if elem.parent else ""
                    if 'required' not in parent_text.lower() and 'mandatory' not in parent_text.lower():
                        issues += 1
                        problematic_elements.append(f"Required field indicator '{text_content}' - add text like 'required' or use aria-required (colorblind users can't see red)")

            self.set_check_result(result, "color_dependency_issues", issues)

            if issues > 0:
                self.add_business_issue(
                    result,
                    title="Don't rely only on color for information",
                    impact=f"Found {issues} elements that use only color to convey important information",
                    priority="should_fix",
                    fix_time=25,
                    difficulty="easy",
                    category="accessibility",
                    count=issues,
                    examples=problematic_elements,
                    total_elements=len(error_elements) + len(success_elements) + len(required_indicators),
                    element_type="indicators",
                    technical_details="Elements should not rely solely on color to convey information",
                    fix_instructions="Add text labels, icons, or other visual indicators alongside color",
                    business_value="Makes important information visible to colorblind users (8% of men)",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Status Indicators",
                            "code": "<!-- Bad: Only color -->\n<span class=\"error\">Email field</span>\n\n<!-- Good: Color + text -->\n<span class=\"error\">\n    <span class=\"error-icon\">⚠️</span>\n    Error: Please enter a valid email\n</span>\n\n<!-- Good: Color + text for required -->\n<label for=\"email\">\n    Email Address <span class=\"required\">(required)</span>\n</label>",
                            "language": "html"
                        }
                    ]
                )

        except Exception as e:
            self.add_issue(result, f"Error checking color dependency: {str(e)}", "warning", "accessibility")

    def _calculate_accessibility_score(self, result: dict) -> None:
        """Calculate accessibility score based on issues found."""
        checks = result.get("checks", {})
        business_issues = result.get("business_issues", [])
        
        # Start with perfect score
        score = 100
        
        # Get accessibility issues
        accessibility_issues = [issue for issue in business_issues if issue["category"] == "accessibility"]
        
        # Deduct points based on priority (aligned with ImprovedScoreCalculationService)
        for issue in accessibility_issues:
            priority_order = issue.get("priority", {}).get("order", 3)
            if priority_order == 1:  # must_fix
                score -= 10  # Aligned with ImprovedScoreCalculationService
            elif priority_order == 2:  # should_fix
                score -= 5   # Aligned with ImprovedScoreCalculationService
            else:  # nice_to_have
                score -= 1   # Aligned with ImprovedScoreCalculationService
        
        # Additional critical checks - use the correct check names with accessibility_ prefix
        # Aligned with ImprovedScoreCalculationService penalties
        critical_penalties = {
            "accessibility_page_title_present": 5,   # Aligned with ImprovedScoreCalculationService
            "accessibility_html_lang_present": 5,    # Aligned with ImprovedScoreCalculationService
            "accessibility_main_landmark_present": 3, # Aligned with ImprovedScoreCalculationService
            "accessibility_h1_count": 4  # Aligned with ImprovedScoreCalculationService
        }
        
        for check, penalty in critical_penalties.items():
            value = checks.get(check, None)
            if check == "accessibility_h1_count":
                if value != 1:  # Should be exactly 1
                    score -= penalty
            elif not value:  # Should be True
                score -= penalty
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Set results
        self.set_check_result(result, "accessibility_score", score)
        result["accessibility_score"] = score
        
        # Create summary
        result["accessibility_summary"] = {
            "score": score,
            "issues_found": len(accessibility_issues),
            "critical_issues": len([i for i in accessibility_issues if i.get("priority", {}).get("order") == 1]),
            "should_fix_issues": len([i for i in accessibility_issues if i.get("priority", {}).get("order") == 2]),
            "nice_to_have_issues": len([i for i in accessibility_issues if i.get("priority", {}).get("order") == 3]),
            "quick_fixes": len([i for i in accessibility_issues if i.get("fix_time_minutes", 0) <= 15]),
            "status": self._get_status_from_score(score),
            "wcag_level": self._get_wcag_level(score)
        }
        
        logger.info(f"Accessibility score calculated: {score}/100 with {len(accessibility_issues)} issues")

    def _get_status_from_score(self, score: int) -> str:
        """Convert score to status message."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good" 
        elif score >= 60:
            return "needs_improvement"
        else:
            return "poor"

    def _get_wcag_level(self, score: int) -> str:
        """Estimate WCAG compliance level from score."""
        if score >= 85:
            return "AA (likely)"
        elif score >= 70:
            return "A (likely)"
        else:
            return "Below A"