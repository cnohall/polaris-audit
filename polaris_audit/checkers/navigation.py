"""
Navigation accessibility checker.

This module handles navigation-related accessibility checks including
landmarks, heading structure, link accessibility, and keyboard navigation.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NavigationChecker:
    """Handles navigation accessibility checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_landmarks(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for ARIA landmarks and semantic HTML."""
        try:
            # Check for semantic HTML5 elements
            landmarks = soup.find_all(['main', 'nav', 'header', 'footer', 'aside', 'section'])
            
            # Also check for ARIA landmarks
            aria_landmarks = soup.find_all(attrs={"role": re.compile(r'(main|navigation|banner|contentinfo|complementary)')})
            
            has_landmarks = len(landmarks) > 0 or len(aria_landmarks) > 0
            has_main = soup.find('main') or soup.find(attrs={"role": "main"})
            
            self.base_checker.set_check_result(result, "landmarks_present", has_landmarks)
            self.base_checker.set_check_result(result, "main_landmark_present", bool(has_main))
            
            if not has_main:
                self.base_checker.add_business_issue(
                    result,
                    title="Mark your main content area",
                    impact="Screen reader users can't quickly jump to your main content",
                    priority="should_fix",
                    fix_time=10,
                    difficulty="easy",
                    difficulty_description="Add a simple HTML tag",
                    category="accessibility",
                    technical_details="No main landmark found",
                    fix_instructions="Wrap your main content in a <main> tag or add role='main' to your content container",
                    business_value="Improves navigation for assistive technology users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Add Main Landmark",
                            "code": "<header>\n    <nav><!-- Navigation --></nav>\n</header>\n\n<main>\n    <h1>Page Title</h1>\n    <!-- Your main content here -->\n</main>\n\n<footer>\n    <!-- Footer content -->\n</footer>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking landmarks: {str(e)}", "warning", "accessibility")

    def check_heading_structure(self, soup: BeautifulSoup, result: dict) -> None:
        """Check heading hierarchy and structure."""
        try:
            headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            h1_elements = soup.find_all("h1")
            h1_count = len(h1_elements)

            self.base_checker.set_check_result(result, "h1_count", h1_count)
            self.base_checker.set_check_result(result, "total_headings", len(headings))

            # Check heading hierarchy and collect problematic elements
            hierarchy_issues = 0
            problematic_headings = []

            if headings:
                prev_level = 0
                for heading in headings:
                    current_level = int(heading.name[1])
                    if prev_level > 0 and current_level > prev_level + 1:
                        hierarchy_issues += 1
                        heading_text = heading.get_text(strip=True)[:50]  # First 50 chars
                        problematic_headings.append(f"Heading: {heading.name.upper()} '{heading_text}' - skips levels (should be H{prev_level + 1})")
                    prev_level = current_level

            self.base_checker.set_check_result(result, "heading_structure_issues", hierarchy_issues)

            # Missing H1
            if h1_count == 0 and len(headings) > 0:
                # Show what headings exist without H1
                existing_headings = [f"Found {heading.name.upper()}: '{heading.get_text(strip=True)[:50]}'" for heading in headings]

                self.base_checker.add_business_issue(
                    result,
                    title="Add a main heading (H1)",
                    impact="Your page structure is unclear to search engines and screen readers",
                    priority="should_fix",
                    fix_time=10,
                    difficulty="easy",
                    category="accessibility",
                    count=1,
                    examples=["Missing H1 heading - page has other headings but no main title"] + existing_headings,
                    total_elements=len(headings) + 1,  # All existing headings + the missing H1
                    element_type="headings",
                    technical_details="No H1 heading found",
                    fix_instructions="Add one main H1 heading that describes what this page is about",
                    business_value="Improves SEO and accessibility",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Add H1 Heading",
                            "code": "<main>\n    <h1>Your Page Title</h1>\n    <p>Page content...</p>\n</main>",
                            "language": "html"
                        }
                    ]
                )
            
            # Multiple H1s
            elif h1_count > 1:
                h1_texts = [f"H1: '{h1.get_text(strip=True)[:50]}'" for h1 in h1_elements]
                self.base_checker.add_business_issue(
                    result,
                    title="Use only one H1 per page",
                    impact="Multiple main headings confuse search engines and screen readers",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="accessibility",
                    count=h1_count,
                    examples=h1_texts,
                    total_headings=len(headings),
                    element_type="headings",
                    technical_details=f"Found {h1_count} H1 headings",
                    fix_instructions="Change extra H1 headings to H2 or H3 as appropriate",
                    business_value="Clearer page structure for SEO and accessibility",
                    recurring_check=True
                )
            
            # Hierarchy issues
            if hierarchy_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Fix heading hierarchy",
                    impact="Headings skip levels, making content structure confusing",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="easy",
                    count=hierarchy_issues,
                    examples=problematic_headings,
                    total_headings=len(headings),
                    element_type="headings",
                    category="accessibility",
                    technical_details=f"Found {hierarchy_issues} heading level jumps",
                    fix_instructions="Don't skip heading levels (H1 → H2 → H3, not H1 → H3)",
                    business_value="Better content structure and navigation",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Good Heading Hierarchy",
                            "code": "<h1>Main Title</h1>\n<h2>Section Title</h2>\n<h3>Subsection</h3>\n<h3>Another Subsection</h3>\n<h2>Another Section</h2>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking headings: {str(e)}", "warning", "accessibility")

    def check_link_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check link accessibility and context."""
        try:
            links = soup.find_all("a")
            issues = 0
            problematic_links = []
            total_links = len(links)
            
            for link in links:
                link_text = link.get_text(strip=True)
                href = link.get("href", "")
                
                # Empty link text
                if not link_text and not link.get("aria-label"):
                    issues += 1
                    problematic_links.append(f"Link to '{href}' - has no visible text (users can't tell what it does)")
                # Generic link text
                elif link_text.lower() in ["click here", "read more", "here", "link", "more"]:
                    issues += 1
                    problematic_links.append(f"Link '{link_text}' → '{href}' - text doesn't explain where it goes")
                # Links that open new windows without warning
                elif link.get("target") == "_blank" and "external" not in link.get("class", []):
                    issues += 1
                    problematic_links.append(f"Link '{link_text}' → '{href}' - opens new tab without warning users")
            
            self.base_checker.set_check_result(result, "link_issues_count", issues)
            
            if issues > 0:
                priority = "should_fix" if issues > 5 else "nice_to_have"
                
                self.base_checker.add_business_issue(
                    result,
                    title="Improve link descriptions",
                    impact=f"{issues} links are unclear for screen reader users",
                    priority=priority,
                    fix_time=issues * 3,
                    difficulty="easy",
                    category="accessibility",
                    count=issues,
                    examples=problematic_links,  # Show all examples
                    total_links=total_links,
                    element_type="links",
                    technical_details=f"Found {issues} problematic links",
                    fix_instructions="Make link text descriptive and warn about links opening new windows",
                    business_value="Better user experience for all visitors",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Good Link Text",
                            "code": "<!-- Good: Descriptive link text -->\n<a href=\"/products\">View our product catalog</a>\n\n<!-- Good: External link with warning -->\n<a href=\"https://example.com\" target=\"_blank\" rel=\"noopener\">\n    External website (opens in new tab)\n</a>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking links: {str(e)}", "warning", "accessibility")

    def check_keyboard_focus(self, soup: BeautifulSoup, result: dict) -> None:
        """Check keyboard and focus management."""
        try:
            # Check for focus trap issues
            interactive_elements = soup.find_all(["button", "a", "input", "select", "textarea"])
            focus_issues = []

            # Check for elements that remove focus indicators
            style_content = ""
            for style in soup.find_all("style"):
                style_content += style.get_text() or ""

            # Simple check for outline removal without replacement
            if ":focus" in style_content and ("outline: none" in style_content or "outline: 0" in style_content):
                if "box-shadow" not in style_content and "border" not in style_content:
                    focus_issues.append("CSS removes focus indicators (:focus { outline: none }) without providing alternative visual indicators")

            # Check for interactive elements without proper tabindex
            for elem in interactive_elements:
                if elem.name == "a" and not elem.get("href"):
                    text = elem.get_text(strip=True)[:30]
                    location = self._get_element_location(elem)
                    focus_issues.append(f"Link without href at {location}: '{text}' - not keyboard accessible")
                elif elem.get("tabindex") == "-1" and not elem.get("aria-hidden"):
                    text = elem.get_text(strip=True)[:30]
                    location = self._get_element_location(elem)
                    focus_issues.append(f"Interactive element with tabindex='-1' at {location}: '{text}' - removed from keyboard navigation")

            score = max(0, 100 - (len(focus_issues) * 15))
            self.base_checker.set_check_result(result, "keyboard_focus_score", score)
            
            if len(focus_issues) > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Fix keyboard navigation",
                    impact="Users navigating with keyboard cannot see or reach elements properly",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="medium",
                    difficulty_description="Requires CSS focus styles and HTML testing",
                    category="accessibility",
                    count=len(focus_issues),
                    examples=focus_issues,
                    total_elements=len(interactive_elements),
                    element_type="interactive elements",
                    technical_details=f"Found {len(focus_issues)} keyboard navigation issues",
                    fix_instructions="Ensure all interactive elements are keyboard accessible with visible focus indicators",
                    business_value="Essential for users who cannot use a mouse",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Keyboard Focus Styling",
                            "code": "/* Ensure visible focus indicators */\nbutton:focus, a:focus, input:focus {\n    outline: 2px solid #007bff;\n    outline-offset: 2px;\n}\n\n/* Custom focus style */\n.custom-focus:focus {\n    outline: none;\n    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.5);\n}",
                            "language": "css"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking keyboard focus: {str(e)}", "warning", "accessibility")

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
                class_str = ' '.join(element_class[:2])  # Show first 2 classes
                if len(element_class) > 2:
                    class_str += "..."
                location_parts.append(f"class='{class_str}'")

            return " ".join(location_parts)
        except Exception:
            return "unknown location"

    def check_skip_links(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for skip navigation links."""
        try:
            skip_links = soup.find_all("a", href=re.compile(r'#(main|content|navigation|skip)', re.I))
            skip_links.extend(soup.find_all("a", class_=re.compile(r'skip', re.I)))

            has_skip_links = len(skip_links) > 0

            self.base_checker.set_check_result(result, "skip_links_present", has_skip_links)

            if not has_skip_links:
                # Analyze what skip links should be added based on page structure
                missing_elements = []

                # Check for main content area
                main_elements = soup.find_all(['main']) or soup.find_all(attrs={"role": "main"})
                if main_elements:
                    missing_elements.append("Skip to main content link - would help users bypass navigation")

                # Check for navigation
                nav_elements = soup.find_all(['nav']) or soup.find_all(attrs={"role": "navigation"})
                if nav_elements:
                    missing_elements.append("Skip to navigation link - would help users find site menu")

                # Check for search
                search_elements = soup.find_all(['input'], type='search') or soup.find_all(attrs={"role": "search"})
                if search_elements:
                    missing_elements.append("Skip to search link - would help users find search quickly")

                if not missing_elements:
                    missing_elements.append("Skip navigation links - page structure unclear but would improve keyboard accessibility")

                self.base_checker.add_business_issue(
                    result,
                    title="Add skip navigation links",
                    impact="Keyboard users must tab through all navigation to reach main content",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="accessibility",
                    count=len(missing_elements),
                    examples=missing_elements,
                    total_elements=1,  # One page that needs skip links
                    element_type="navigation",
                    technical_details="No skip navigation links found",
                    fix_instructions="Add skip links at the top of the page to allow keyboard users to jump to main content",
                    business_value="Improves keyboard navigation efficiency",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Skip Navigation Links",
                            "code": "<body>\n    <a href=\"#main\" class=\"skip-link\">Skip to main content</a>\n    <a href=\"#navigation\" class=\"skip-link\">Skip to navigation</a>\n    \n    <header>\n        <nav id=\"navigation\"><!-- Navigation --></nav>\n    </header>\n    \n    <main id=\"main\">\n        <!-- Main content -->\n    </main>\n</body>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking skip links: {str(e)}", "warning", "accessibility")

    def check_navigation_structure(self, soup: BeautifulSoup, result: dict) -> None:
        """Check overall navigation structure and consistency."""
        try:
            nav_elements = soup.find_all(['nav', 'ul', 'ol'])
            nav_issues = 0
            
            for nav in nav_elements:
                # Check for proper list structure in navigation
                if nav.name == 'nav':
                    list_items = nav.find_all(['ul', 'ol'])
                    if not list_items:
                        nav_issues += 1
                    else:
                        # Check for proper list item structure
                        for ul in list_items:
                            if not ul.find_all('li'):
                                nav_issues += 1
            
            self.base_checker.set_check_result(result, "navigation_structure_issues", nav_issues)
            
            if nav_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve navigation structure",
                    impact="Navigation is not properly structured for screen readers - they can't understand menu relationships and hierarchies",
                    priority="should_fix",
                    fix_time=20,
                    difficulty="easy",
                    difficulty_description="Simple HTML structure changes",
                    category="accessibility",
                    count=nav_issues,
                    examples=[f"Found {nav_issues} navigation elements that need proper list structure (ul/li) for screen reader accessibility"],
                    element_type="navigation elements",
                    total_elements=nav_issues,
                    technical_details=f"Navigation elements lack proper semantic list structure. Screen readers expect nav elements to contain ul/ol with li items to understand menu hierarchies and provide proper navigation shortcuts.",
                    fix_instructions="""WHAT IS PROPER NAVIGATION STRUCTURE?

Think of navigation like a table of contents in a book: Screen readers need clear structure to understand what's a main section, what's a subsection, and how items relate to each other. Using proper HTML lists (ul/li) provides this structure.

REAL-WORLD IMPACT:
- **Without proper structure**: Screen reader says "link, link, link" (confusing)
- **With proper structure**: Screen reader says "list with 3 items: Home, About, Contact" (clear)
- **Result**: Users can navigate efficiently using screen reader shortcuts

WHY THIS MATTERS FOR YOUR BUSINESS:
- **Legal Compliance**: Helps meet WCAG 2.1 AA standards and ADA requirements
- **User Experience**: 15% of web users rely on keyboard/screen reader navigation
- **SEO Benefits**: Search engines understand site structure better
- **Brand Reputation**: Shows commitment to inclusive design

STEP-BY-STEP FIX GUIDE:

🔧 METHOD 1: BASIC NAVIGATION STRUCTURE (5-10 MINUTES)

**For React/JSX Components**:
```jsx
// BEFORE (problematic):
<nav>
  <Link to="/">Home</Link>
  <Link to="/about">About</Link>
  <Link to="/contact">Contact</Link>
</nav>

// AFTER (accessible):
<nav aria-label="Main navigation">
  <ul>
    <li><Link to="/">Home</Link></li>
    <li><Link to="/about">About</Link></li>
    <li><Link to="/contact">Contact</Link></li>
  </ul>
</nav>
```

**For HTML Templates**:
```html
<!-- BEFORE (problematic): -->
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
</nav>

<!-- AFTER (accessible): -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</nav>
```

🔧 METHOD 2: ADVANCED NAVIGATION WITH SUBMENUS (15-20 MINUTES)

**Multi-level Navigation**:
```html
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li>
      <a href="/products" aria-expanded="false" aria-haspopup="true">Products</a>
      <ul>
        <li><a href="/products/software">Software</a></li>
        <li><a href="/products/hardware">Hardware</a></li>
      </ul>
    </li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</nav>
```

🔧 METHOD 3: MOBILE NAVIGATION IMPROVEMENTS

**Responsive Navigation with Proper Structure**:
```html
<nav aria-label="Main navigation">
  <button aria-expanded="false" aria-controls="main-menu" aria-label="Toggle navigation menu">
    Menu
  </button>
  <ul id="main-menu" class="hidden md:flex">
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</nav>
```

CSS TO MAINTAIN VISUAL DESIGN:

```css
/* Remove default list styling while keeping structure */
nav ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex; /* or your preferred layout */
}

nav li {
  margin: 0;
  padding: 0;
}

/* Maintain your existing link styles */
nav a {
  /* Your existing styles */
}
```

TESTING YOUR CHANGES:

1. **Screen Reader Test**:
   - Use NVDA (free) or JAWS
   - Navigate to your site and press Tab
   - Should announce "list with X items" for navigation

2. **Keyboard Navigation Test**:
   - Use Tab key to navigate
   - Arrow keys should work in some screen readers to navigate within lists
   - Ensure all items are reachable

3. **Automated Testing**:
   - Use axe-core browser extension
   - Run Lighthouse accessibility audit
   - Check for "Navigation should use lists" violations

COMMON MISTAKES TO AVOID:

❌ **Removing list styling completely**:
```css
/* Wrong - breaks semantics */
nav ul { display: contents; }
```

✅ **Keeping structure, changing appearance**:
```css
/* Right - maintains semantics */
nav ul { list-style: none; display: flex; }
```

❌ **Forgetting aria-labels**:
```html
<!-- Missing context -->
<nav><ul>...</ul></nav>
```

✅ **Providing clear labels**:
```html
<!-- Clear purpose -->
<nav aria-label="Main navigation"><ul>...</ul></nav>
```

WHY THIS PROTECTS YOUR USERS:
Screen readers and other assistive technologies rely on proper HTML structure to create mental maps of your site. When navigation lacks proper list structure, users with disabilities can't efficiently understand or navigate your content, potentially losing customers and creating legal liability.""",
                    business_value="Essential for inclusive design and legal compliance - makes navigation efficient for 15% of web users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Basic Navigation Structure (HTML)",
                            "code": "<nav aria-label=\"Main navigation\">\n  <ul>\n    <li><a href=\"/\">Home</a></li>\n    <li><a href=\"/about\">About</a></li>\n    <li><a href=\"/contact\">Contact</a></li>\n  </ul>\n</nav>",
                            "language": "html"
                        },
                        {
                            "title": "React/JSX Navigation Structure",
                            "code": "<nav aria-label=\"Main navigation\">\n  <ul className=\"flex space-x-4 list-none\">\n    <li><Link to=\"/\">Home</Link></li>\n    <li><Link to=\"/about\">About</Link></li>\n    <li><Link to=\"/contact\">Contact</Link></li>\n  </ul>\n</nav>",
                            "language": "jsx"
                        },
                        {
                            "title": "CSS to maintain visual design",
                            "code": "/* Remove default list styling while keeping semantics */\nnav ul {\n  list-style: none;\n  margin: 0;\n  padding: 0;\n  display: flex;\n}\n\nnav li {\n  margin: 0;\n  padding: 0;\n}",
                            "language": "css"
                        },
                        {
                            "title": "Advanced navigation with dropdown",
                            "code": "<nav aria-label=\"Main navigation\">\n  <ul>\n    <li><a href=\"/\">Home</a></li>\n    <li>\n      <a href=\"/products\" aria-expanded=\"false\" aria-haspopup=\"true\">Products</a>\n      <ul>\n        <li><a href=\"/products/web\">Web</a></li>\n        <li><a href=\"/products/mobile\">Mobile</a></li>\n      </ul>\n    </li>\n  </ul>\n</nav>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking navigation structure: {str(e)}", "warning", "accessibility")

    def check_breadcrumbs(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for breadcrumb navigation."""
        try:
            # Look for common breadcrumb patterns
            breadcrumb_patterns = [
                soup.find_all(class_=re.compile(r'breadcrumb', re.I)),
                soup.find_all(attrs={"aria-label": re.compile(r'breadcrumb', re.I)}),
                soup.find_all(attrs={"role": "navigation"}),
            ]
            
            breadcrumbs = []
            for pattern in breadcrumb_patterns:
                breadcrumbs.extend(pattern)
            
            has_breadcrumbs = len(breadcrumbs) > 0
            
            self.base_checker.set_check_result(result, "breadcrumbs_present", has_breadcrumbs)
            
            if not has_breadcrumbs and len(soup.find_all(['h1', 'h2', 'h3'])) > 3:
                # Only suggest breadcrumbs for pages with multiple sections
                # Analyze what breadcrumb structure would be beneficial
                missing_elements = []

                # Check for main content area
                main_elements = soup.find_all(['main']) or soup.find_all(attrs={"role": "main"})
                if main_elements:
                    missing_elements.append("Breadcrumb navigation - would help users understand their location in the site hierarchy")

                # Check for navigation
                nav_elements = soup.find_all(['nav']) or soup.find_all(attrs={"role": "navigation"})
                if nav_elements:
                    missing_elements.append("Location indicators - would show users how they arrived at this page")

                if not missing_elements:
                    missing_elements.append("Breadcrumb navigation - page structure suggests users would benefit from location awareness")
                self.base_checker.add_business_issue(
                    result,
                    title="Consider adding breadcrumb navigation",
                    impact="Users may lose track of their location within your site, reducing navigation efficiency and user experience",
                    priority="nice_to_have",
                    fix_time=30,
                    difficulty="medium",
                    difficulty_description="Requires understanding of site structure and route hierarchy",
                    category="accessibility",
                    count=len(missing_elements),
                    examples=missing_elements,
                    element_type="navigation",
                    total_elements=1,
                    technical_details="No breadcrumb navigation found on pages with complex structure. Breadcrumbs help users understand their location in the site hierarchy and provide quick navigation back to parent pages.",
                    fix_instructions="Add breadcrumb navigation to show users their location in your site hierarchy. Use <nav aria-label='Breadcrumb'><ol> with links for parent pages and plain text for current page.",
                    business_value="Improves user orientation, reduces navigation confusion, and enhances overall user experience - particularly valuable for complex sites",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Basic HTML Breadcrumb Structure",
                            "code": "<nav aria-label=\"Breadcrumb\" role=\"navigation\">\n  <ol class=\"breadcrumb-list\">\n    <li class=\"breadcrumb-item\">\n      <a href=\"/\">Home</a>\n    </li>\n    <li class=\"breadcrumb-item\">\n      <a href=\"/blog\">Blog</a>\n    </li>\n    <li class=\"breadcrumb-item active\" aria-current=\"page\">\n      Current Article\n    </li>\n  </ol>\n</nav>",
                            "language": "html"
                        },
                        {
                            "title": "CSS Styling for Breadcrumbs",
                            "code": ".breadcrumb-list {\n  display: flex;\n  list-style: none;\n  margin: 0;\n  padding: 0;\n  font-size: 14px;\n}\n\n.breadcrumb-item:not(:last-child)::after {\n  content: \"/\";\n  margin: 0 8px;\n  color: #666;\n}\n\n.breadcrumb-item a {\n  color: #0066cc;\n  text-decoration: none;\n}\n\n.breadcrumb-item.active {\n  color: #333;\n  font-weight: 500;\n}",
                            "language": "css"
                        },
                        {
                            "title": "React Dynamic Breadcrumbs",
                            "code": "import { useLocation, Link } from 'react-router-dom';\n\nconst Breadcrumbs = () => {\n  const location = useLocation();\n  const pathSegments = location.pathname.split('/').filter(Boolean);\n  \n  const generateBreadcrumbs = () => {\n    const crumbs = [{ label: 'Home', path: '/' }];\n    \n    let currentPath = '';\n    pathSegments.forEach((segment, index) => {\n      currentPath += `/${segment}`;\n      if (index < pathSegments.length - 1) {\n        crumbs.push({\n          label: formatSegment(segment),\n          path: currentPath\n        });\n      }\n    });\n    \n    return crumbs;\n  };\n  \n  return (\n    <nav aria-label=\"Breadcrumb\">\n      <ol className=\"flex space-x-2 text-sm\">\n        {generateBreadcrumbs().map((crumb, index) => (\n          <li key={crumb.path}>\n            {index > 0 && <span>/</span>}\n            <Link to={crumb.path}>{crumb.label}</Link>\n          </li>\n        ))}\n        <li><span>/</span><span>Current Page</span></li>\n      </ol>\n    </nav>\n  );\n};",
                            "language": "jsx"
                        },
                        {
                            "title": "WordPress Breadcrumbs (Yoast SEO)",
                            "code": "<?php\n// Add to your theme's header.php or page template\nif ( function_exists('yoast_breadcrumb') ) {\n  yoast_breadcrumb('<nav id=\"breadcrumbs\" aria-label=\"Breadcrumb\">','</nav>');\n}\n?>",
                            "language": "php"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking breadcrumbs: {str(e)}", "warning", "accessibility")
