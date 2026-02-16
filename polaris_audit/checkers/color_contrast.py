"""
Color contrast and color accessibility checker.

This module handles all color-related accessibility checks including
color contrast ratios, color-only indicators, and color dependency issues.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ColorContrastChecker:
    """Handles color contrast and color accessibility checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_color_indicators(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for color-only indicators and color contrast issues with specific locations."""
        try:
            # Check for color-only indicators
            color_dependent_patterns = 0
            color_dependent_locations = []
            
            # Check for form validation that might use only color
            error_elements = soup.find_all(class_=re.compile(r'error|invalid|danger'))
            success_elements = soup.find_all(class_=re.compile(r'success|valid|good'))
            
            for elem in error_elements + success_elements:
                text = elem.get_text(strip=True)
                # If element has color class but no descriptive text or icons
                if len(text) < 3 and not elem.find(["i", "span", "svg"]):
                    color_dependent_patterns += 1
                    location = self._get_element_location(elem)
                    color_dependent_locations.append(location)
            
            # Check for color contrast issues
            contrast_issues = self._check_color_contrast(soup)
            
            self.base_checker.set_check_result(result, "color_dependency_issues", color_dependent_patterns)
            self.base_checker.set_check_result(result, "color_contrast_issues", len(contrast_issues))
            
            # Report color-only indicators
            if color_dependent_patterns > 0:
                locations_text = "\n".join([f"• {loc}" for loc in color_dependent_locations])
                
                self.base_checker.add_business_issue(
                    result,
                    title="Don't rely only on color for information",
                    impact=f"Found {color_dependent_patterns} places where color is the only way to understand information",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="medium",
                    category="accessibility",
                    technical_details=f"Color-only indicators found in:\n{locations_text}",
                    fix_instructions="Add text, icons, or patterns alongside color indicators",
                    business_value="Makes your site usable by color-blind users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Color Plus Text/Icons",
                            "code": "<!-- Good: Color + text -->\n<div class=\"error\">\n    <span class=\"error-icon\">⚠</span>\n    Error: Please enter a valid email\n</div>\n\n<!-- Good: Color + pattern -->\n<div class=\"success\" style=\"border-left: 4px solid green;\">\n    ✓ Form submitted successfully\n</div>",
                            "language": "html"
                        }
                    ]
                )
            
            # Report color contrast issues
            if contrast_issues:
                self._report_contrast_issues(result, contrast_issues)
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking color indicators: {str(e)}", "warning", "accessibility")

    def _check_color_contrast(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Check for color contrast issues with specific element locations."""
        contrast_issues = []
        
        try:
            # Look for elements with inline styles or common contrast problem patterns
            elements_to_check = []
            
            # Check elements with inline color styles
            elements_with_color = soup.find_all(attrs={"style": re.compile(r'color\s*:', re.I)})
            elements_to_check.extend(elements_with_color)
            
            # Check elements with background color
            elements_with_bg = soup.find_all(attrs={"style": re.compile(r'background.*color\s*:', re.I)})
            elements_to_check.extend(elements_with_bg)
            
            # Check common text elements that might have contrast issues
            text_elements = soup.find_all(['p', 'span', 'div', 'a', 'button', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            elements_to_check.extend(text_elements)
            
            # Check for common problematic color combinations
            problematic_patterns = [
                # Light text on light backgrounds
                (r'color\s*:\s*#(fff|ffffff|f0f0f0|e0e0e0)', r'background.*color\s*:\s*#(fff|ffffff|f0f0f0|e0e0e0)'),
                (r'color\s*:\s*white', r'background.*color\s*:\s*white'),
                (r'color\s*:\s*#(ccc|cccccc)', r'background.*color\s*:\s*#(fff|ffffff)'),
                
                # Dark text on dark backgrounds  
                (r'color\s*:\s*#(000|000000|333|333333)', r'background.*color\s*:\s*#(000|000000|333|333333)'),
                (r'color\s*:\s*black', r'background.*color\s*:\s*black'),
                
                # Red text on red backgrounds
                (r'color\s*:\s*red', r'background.*color\s*:\s*red'),
                (r'color\s*:\s*#(f00|ff0000)', r'background.*color\s*:\s*#(f00|ff0000)'),
            ]
            
            for element in elements_to_check:
                style = element.get('style', '').lower()
                text = element.get_text(strip=True)
                
                # Skip empty elements
                if not text or len(text) < 2:
                    continue
                
                # Check for problematic patterns
                for text_pattern, bg_pattern in problematic_patterns:
                    if re.search(text_pattern, style) and re.search(bg_pattern, style):
                        location = self._get_element_location(element)
                        contrast_issues.append({
                            'element': element,
                            'location': location,
                            'text': text[:50] + "..." if len(text) > 50 else text,
                            'style': style,
                            'issue_type': 'low_contrast',
                            'suggestion': self._get_contrast_suggestion(text_pattern, bg_pattern)
                        })
                        break
                
                # Check for very light or very dark text without background
                if re.search(r'color\s*:\s*#(ccc|cccccc|ddd|dddddd|eee|eeeeee)', style):
                    location = self._get_element_location(element)
                    contrast_issues.append({
                        'element': element,
                        'location': location,
                        'text': text[:50] + "..." if len(text) > 50 else text,
                        'style': style,
                        'issue_type': 'light_text',
                        'suggestion': 'Consider using darker text color for better readability'
                    })
                
                if re.search(r'color\s*:\s*#(333|333333|444|444444|555|555555)', style) and not re.search(r'background.*color', style):
                    location = self._get_element_location(element)
                    contrast_issues.append({
                        'element': element,
                        'location': location,
                        'text': text[:50] + "..." if len(text) > 50 else text,
                        'style': style,
                        'issue_type': 'dark_text_no_bg',
                        'suggestion': 'Consider adding a light background or using lighter text'
                    })
            
        except Exception as e:
            logger.error(f"Error checking color contrast: {e}")
        
        return contrast_issues

    def _get_element_location(self, element) -> str:
        """Get a descriptive location for an element."""
        try:
            # Get element tag and attributes
            tag_name = element.name
            element_id = element.get('id', '')
            element_class = element.get('class', [])
            
            # Build location description
            location_parts = [f"<{tag_name}>"]
            
            if element_id:
                location_parts.append(f"id='{element_id}'")
            
            if element_class:
                class_str = ' '.join(element_class[:3])  # Show first 3 classes
                if len(element_class) > 3:
                    class_str += f" (+{len(element_class) - 3} more)"
                location_parts.append(f"class='{class_str}'")
            
            # Add parent context if available
            parent = element.parent
            if parent and parent.name:
                parent_tag = parent.name
                parent_id = parent.get('id', '')
                if parent_id:
                    location_parts.append(f"inside <{parent_tag} id='{parent_id}'>")
                else:
                    location_parts.append(f"inside <{parent_tag}>")
            
            return " ".join(location_parts)
            
        except Exception:
            return f"<{element.name}> element"

    def _get_contrast_suggestion(self, text_pattern: str, bg_pattern: str) -> str:
        """Get a suggestion for improving contrast based on the patterns found."""
        if 'white' in text_pattern or '#fff' in text_pattern:
            return "Use darker text color (e.g., #333333) or add a dark background"
        elif 'black' in text_pattern or '#000' in text_pattern:
            return "Use lighter text color (e.g., #ffffff) or add a light background"
        elif 'red' in text_pattern or '#f00' in text_pattern:
            return "Avoid red text on red background - use contrasting colors"
        else:
            return "Ensure sufficient contrast between text and background colors"

    def _report_contrast_issues(self, result: dict, contrast_issues: List[Dict[str, Any]]) -> None:
        """Report color contrast issues with specific locations."""
        # Group issues by type
        issue_groups = {}
        for issue in contrast_issues:
            issue_type = issue['issue_type']
            if issue_type not in issue_groups:
                issue_groups[issue_type] = []
            issue_groups[issue_type].append(issue)
        
        # Report each type of issue
        for issue_type, issues in issue_groups.items():
            if issue_type == 'low_contrast':
                self._report_low_contrast_issues(result, issues)
            elif issue_type == 'light_text':
                self._report_light_text_issues(result, issues)
            elif issue_type == 'dark_text_no_bg':
                self._report_dark_text_issues(result, issues)

    def _report_low_contrast_issues(self, result: dict, issues: List[Dict[str, Any]]) -> None:
        """Report low contrast issues with specific locations."""
        locations_text = "\n".join([f"• {issue['location']}: '{issue['text']}'" for issue in issues])
        
        self.base_checker.add_business_issue(
            result,
            title="Fix low color contrast",
            impact=f"Found {len(issues)} elements with poor color contrast that may be hard to read",
            priority="should_fix",
            fix_time=30,
            difficulty="easy",
            category="accessibility",
            technical_details=f"Low contrast elements found in:\n{locations_text}",
            fix_instructions="Increase contrast between text and background colors. Use tools like WebAIM Contrast Checker to verify ratios meet WCAG standards.",
            business_value="Makes your content readable for users with visual impairments",
            recurring_check=True,
            code_snippets=[
                {
                    "title": "Good Contrast Examples",
                    "code": "/* Good contrast ratios */\n.dark-text {\n    color: #333333;\n    background-color: #ffffff;\n}\n\n.light-text {\n    color: #ffffff;\n    background-color: #333333;\n}\n\n/* Use WebAIM Contrast Checker to verify ratios */",
                    "language": "css"
                }
            ],
            testing_steps=[
                "Use browser developer tools to inspect each flagged element",
                "Check contrast ratio using WebAIM Contrast Checker",
                "Ensure text meets WCAG AA standards (4.5:1 for normal text, 3:1 for large text)"
            ],
            resources=[
                {
                    "label": "WebAIM Contrast Checker",
                    "url": "https://webaim.org/resources/contrastchecker/"
                },
                {
                    "label": "WCAG Color Contrast Guidelines",
                    "url": "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"
                }
            ]
        )

    def _report_light_text_issues(self, result: dict, issues: List[Dict[str, Any]]) -> None:
        """Report light text issues with specific locations."""
        locations_text = "\n".join([f"• {issue['location']}: '{issue['text']}'" for issue in issues])
        
        self.base_checker.add_business_issue(
            result,
            title="Fix light text color",
            impact=f"Found {len(issues)} elements with very light text that may be hard to read",
            priority="should_fix",
            fix_time=15,
            difficulty="easy",
            category="accessibility",
            technical_details=f"Light text elements found in:\n{locations_text}",
            fix_instructions="Use darker text colors for better readability. Light gray text (#ccc, #ddd) is often too light.",
            business_value="Improves readability for all users, especially those with visual impairments",
            recurring_check=True,
            code_snippets=[
                {
                    "title": "Better Text Colors",
                    "code": "/* Instead of very light text */\n.light-text {\n    color: #666666; /* Better than #cccccc */\n}\n\n.medium-text {\n    color: #333333; /* Even better contrast */\n}",
                    "language": "css"
                }
            ]
        )

    def _report_dark_text_issues(self, result: dict, issues: List[Dict[str, Any]]) -> None:
        """Report dark text without background issues with specific locations."""
        locations_text = "\n".join([f"• {issue['location']}: '{issue['text']}'" for issue in issues])
        
        self.base_checker.add_business_issue(
            result,
            title="Add background for dark text",
            impact=f"Found {len(issues)} elements with dark text that may need background colors",
            priority="nice_to_have",
            fix_time=20,
            difficulty="easy",
            category="accessibility",
            technical_details=f"Dark text elements found in:\n{locations_text}",
            fix_instructions="Consider adding light background colors to ensure good contrast, especially if the page background might change.",
            business_value="Ensures consistent readability across different contexts",
            recurring_check=True,
            code_snippets=[
                {
                    "title": "Adding Backgrounds",
                    "code": "/* Add light background for dark text */\n.dark-text {\n    color: #333333;\n    background-color: #f8f9fa; /* Light background */\n    padding: 8px 12px; /* Add some padding */\n    border-radius: 4px; /* Optional: rounded corners */\n}",
                    "language": "css"
                }
            ]
        )

    def check_color_contrast_ratio(self, text_color: str, background_color: str) -> float:
        """
        Calculate color contrast ratio between text and background.
        
        Args:
            text_color: Text color in hex format (e.g., '#ffffff')
            background_color: Background color in hex format (e.g., '#000000')
            
        Returns:
            float: Contrast ratio (1.0 to 21.0)
        """
        try:
            # Convert hex to RGB
            text_rgb = self._hex_to_rgb(text_color)
            bg_rgb = self._hex_to_rgb(background_color)
            
            if not text_rgb or not bg_rgb:
                return 1.0
            
            # Calculate relative luminance
            text_luminance = self._get_relative_luminance(text_rgb)
            bg_luminance = self._get_relative_luminance(bg_rgb)
            
            # Calculate contrast ratio
            lighter = max(text_luminance, bg_luminance)
            darker = min(text_luminance, bg_luminance)
            
            if darker == 0:
                return 21.0  # Maximum contrast
            
            return (lighter + 0.05) / (darker + 0.05)
            
        except Exception as e:
            logger.error(f"Error calculating contrast ratio: {e}")
            return 1.0

    def _hex_to_rgb(self, hex_color: str) -> Optional[tuple]:
        """Convert hex color to RGB tuple."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return None

    def _get_relative_luminance(self, rgb: tuple) -> float:
        """Calculate relative luminance of RGB color."""
        r, g, b = rgb
        
        # Normalize RGB values
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0
        
        # Apply gamma correction
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        # Calculate relative luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def is_contrast_sufficient(self, text_color: str, background_color: str, level: str = "AA") -> bool:
        """
        Check if contrast ratio meets WCAG standards.
        
        Args:
            text_color: Text color in hex format
            background_color: Background color in hex format
            level: WCAG level ("A", "AA", or "AAA")
            
        Returns:
            bool: True if contrast meets the specified level
        """
        ratio = self.check_color_contrast_ratio(text_color, background_color)
        
        if level == "A":
            return ratio >= 3.0
        elif level == "AA":
            return ratio >= 4.5
        elif level == "AAA":
            return ratio >= 7.0
        else:
            return ratio >= 4.5  # Default to AA
