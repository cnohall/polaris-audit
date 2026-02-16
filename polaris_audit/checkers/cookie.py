"""
Cookie compliance checker.

This module handles all cookie-related GDPR compliance checks including
cookie consent detection, pre-consent violations, and cookie banner quality.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CookieChecker:
    """Handles cookie compliance checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_cookie_consent(self, soup: BeautifulSoup, phrases: Dict, language: str, result: dict) -> None:
        """Check for cookie consent mechanisms with better false flag prevention."""
        
        try:
            # Check data processing scope first
            scope = result.get("checks", {}).get("data_processing_scope", {})
            has_tracking = scope.get("has_tracking", False)
            
            # Enhanced cookie consent detection
            cookie_consent_indicators = [
                'cookie consent', 'cookie banner', 'cookie notice', 'cookie policy',
                'accept cookies', 'decline cookies', 'cookie preferences', 'cookie settings',
                'manage cookies', 'gdpr', 'data protection', 'privacy settings'
            ]
            
            cookie_consent_found = False
            
            # Check HTML content for consent-related text
            html_content = str(soup)
            html_lower = html_content.lower()
            
            # More specific detection - look for actual consent mechanisms
            for indicator in cookie_consent_indicators:
                if indicator in html_lower:
                    cookie_consent_found = True
                    logger.info(f"Cookie consent found via indicator: {indicator}")
                    break
            
            # Check for consent management platform scripts
            consent_scripts = soup.find_all("script", src=True)
            consent_platforms = [
                "cookiebot", "onetrust", "cookiepro", "trustarc", 
                "cookie-consent", "gdpr-consent", "usercentrics",
                "cookieyes", "cookie-law", "cookie-notice", "klaro"
            ]
            
            for script in consent_scripts:
                src = script.get("src", "").lower()
                if any(platform in src for platform in consent_platforms):
                    cookie_consent_found = True
                    logger.info(f"Cookie consent found via script: {src}")
                    break

            # Check for consent-related buttons and forms
            if not cookie_consent_found:
                consent_buttons = soup.find_all(['button', 'a'], 
                                               string=re.compile(r'accept.*cookie|decline.*cookie|cookie.*setting|manage.*cookie', re.I))
                if consent_buttons:
                    cookie_consent_found = True
                    logger.info("Cookie consent found via consent buttons")

            self.base_checker.set_check_result(result, "cookie_consent_found", cookie_consent_found)

            # Only flag missing consent if site has tracking AND significant data processing
            privacy_details = result.get("privacy_details", {})
            third_party_count = privacy_details.get("third_party_services_count", 0)
            site_complexity = scope.get("site_complexity", "simple")
            
            should_flag_missing_consent = (
                not cookie_consent_found and 
                has_tracking and 
                third_party_count > 1 and  # More than just basic analytics
                site_complexity != "simple"
            )
            
            if should_flag_missing_consent:
                self.base_checker.add_business_issue(
                    result,
                    title="Add cookie consent banner",
                    impact=f"Required by GDPR - detected {third_party_count} tracking services without consent mechanism",
                    priority="must_fix", 
                    fix_time=60,
                    difficulty="easy",
                    category="privacy",
                    technical_details=f"Detected tracking services: {third_party_count}, but no cookie consent mechanism found",
                    fix_instructions="Install a cookie consent management platform like Cookiebot or implement a custom consent banner.",
                    business_value="Protects from GDPR fines and shows customers you respect their privacy",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Cookiebot Integration",
                            "code": "<script id=\"Cookiebot\" src=\"https://consent.cookiebot.com/uc.js\" data-cbid=\"YOUR-COOKIEBOT-ID\" type=\"text/javascript\" async></script>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Visit your website and look for a cookie consent banner",
                        "Verify tracking is blocked until consent is given",
                        "Test both Accept and Reject options"
                    ],
                    resources=[
                        {
                            "label": "Cookiebot - Cookie Consent Management",
                            "url": "https://www.cookiebot.com/"
                        }
                    ]
                )
            elif not cookie_consent_found and (not has_tracking or third_party_count <= 1):
                logger.info(f"No cookie consent found, but minimal tracking detected ({third_party_count} services) - no issue added")
            else:
                logger.info("Cookie consent found or not required - no issue added")

        except Exception as e:
            logger.error(f"Exception in cookie consent check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie consent: {str(e)}", "warning", "privacy")

    def check_cookie_pre_consent_violation(self, result: dict) -> None:
        """Check for cookie pre-consent violations with improved categorization."""
        try:
            privacy_details = result.get("privacy_details", {})
            scope = result.get("checks", {}).get("data_processing_scope", {})
            
            # Get categorized services from the improved analysis
            marketing_services = privacy_details.get("marketing_services", [])
            ux_services = privacy_details.get("ux_services", [])
            analytics_services = privacy_details.get("analytics_services", [])
            essential_services = privacy_details.get("essential_services", [])
            
            # Only flag services that actually require consent
            consent_required_services = []
            
            # Marketing services always require consent
            for service in marketing_services:
                if service.get("consent_required", True):
                    consent_required_services.append(service)
            
            # UX services typically require consent
            for service in ux_services:
                if service.get("consent_required", True):
                    consent_required_services.append(service)
            
            # Some analytics services may require consent (but not basic ones)
            for service in analytics_services:
                if service.get("consent_required", True):
                    consent_required_services.append(service)
            
            # Essential services never require consent - don't flag them
            logger.info(f"Service categorization: {len(essential_services)} essential, {len(analytics_services)} analytics, {len(marketing_services)} marketing, {len(ux_services)} UX")
            
            # Only flag if we have services that actually require consent
            if consent_required_services:
                detected_cookies = []
                for service in consent_required_services:
                    detected_cookies.append({
                        "name": service.get("name", "Unknown Service"),
                        "type": service.get("type", "other"),
                        "category": service.get("category", "unknown"),
                        "consent_required": service.get("consent_required", True),
                        "pattern_matched": service.get("pattern_matched", "")
                    })
                
                technical_details = f"Detected {len(consent_required_services)} services requiring consent:\n"
                for cookie in detected_cookies:
                    technical_details += f"• {cookie['name']} ({cookie['category']}) - {cookie['type']}\n"
                
                # Cookie consent is critical for GDPR compliance
                priority = "must_fix"
                
                self.base_checker.add_business_issue(
                    result,
                    title="Fix cookie pre-consent violation",
                    impact=f"Website sets {len(consent_required_services)} non-essential cookies before consent - GDPR violation",
                    priority=priority,
                    fix_time=180 if has_marketing else 120,
                    difficulty="hard",
                    category="privacy",
                    technical_details=technical_details,
                    fix_instructions="Block non-essential cookies until explicit user consent. Essential cookies for site functionality are allowed.",
                    business_value="Prevents GDPR fines and builds customer trust by respecting privacy rights",
                    recurring_check=True,
                    detected_cookies=detected_cookies,
                    code_snippets=[
                        {
                            "title": "Cookiebot Implementation",
                            "code": "<!-- Block tracking scripts until consent -->\n<script type=\"text/plain\" data-cookieconsent=\"statistics\">\n  // Google Analytics code here\n</script>\n<script type=\"text/plain\" data-cookieconsent=\"marketing\">\n  // Facebook Pixel or other marketing code here\n</script>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Clear browser cookies and visit your site",
                        "Check Developer Tools > Application > Cookies",
                        "Verify only essential cookies are set before consent",
                        "Accept cookies and verify tracking cookies then appear"
                    ],
                    resources=[
                        {
                            "label": "GDPR Cookie Compliance Guide",
                            "url": "https://gdpr.eu/cookies/"
                        }
                    ]
                )
                logger.info(f"Added cookie pre-consent violation - {len(consent_required_services)} services requiring consent")
            else:
                logger.info("No services requiring consent detected - no pre-consent violation")

        except Exception as e:
            logger.error(f"Exception in cookie pre-consent check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie pre-consent: {str(e)}", "warning", "privacy")

    def check_cookie_banner_implementation(self, soup: BeautifulSoup, result: dict) -> None:
        """Check quality of cookie banner implementation."""
        try:
            if not result.get("checks", {}).get("cookie_consent_found", False):
                return
                
            accept_keywords = re.compile(r"\b(accept|agree|ok|allow|yes|enable)\b", re.IGNORECASE)
            reject_keywords = re.compile(
                r"\b(reject|decline|deny|refuse|no|disable|necessary only|essential only|manage|settings)\b", 
                re.IGNORECASE
            )

            accept_buttons = []
            reject_buttons = []

            for tag in soup.find_all(["button", "a", "input"]):
                label = tag.get_text(strip=True)
                
                if accept_keywords.search(label):
                    accept_buttons.append(tag)
                if reject_keywords.search(label):
                    reject_buttons.append(tag)

            self.base_checker.set_check_result(result, "has_accept_button", len(accept_buttons) > 0)
            self.base_checker.set_check_result(result, "has_reject_button", len(reject_buttons) > 0)

            # Only flag if there's a clear accept without reject - avoid false flags on settings pages
            if accept_buttons and not reject_buttons and len(accept_buttons) < 3:  # Not a settings page with many buttons
                self.base_checker.add_business_issue(
                    result,
                    title="Cookie banner needs reject option",
                    impact="GDPR requires equal prominence for accept/reject options",
                    priority="should_fix",
                    fix_time=60,
                    difficulty="easy", 
                    category="privacy",
                    technical_details="Cookie banner has accept button but no clear reject option with equal prominence",
                    fix_instructions="Add a 'Reject All' or 'Essential Only' button that's as prominent as the Accept button.",
                    business_value="Ensures GDPR compliance and avoids potential fines",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "GDPR Compliant Cookie Banner",
                            "code": "<div class=\"cookie-banner\">\n    <p>We use cookies to improve your experience.</p>\n    <div class=\"cookie-buttons\">\n        <button class=\"btn-accept\">Accept All</button>\n        <button class=\"btn-reject\">Reject All</button>\n        <button class=\"btn-settings\">Customize</button>\n    </div>\n</div>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Verify both Accept and Reject buttons are equally visible",
                        "Test that Reject actually blocks non-essential cookies",
                        "Check that choices are remembered across page visits"
                    ]
                )

        except Exception as e:
            logger.error(f"Exception in cookie banner implementation check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie banner implementation: {str(e)}", "warning", "privacy")

    def check_cookie_categories(self, result: dict) -> None:
        """Check for proper cookie categorization and disclosure."""
        try:
            privacy_details = result.get("privacy_details", {})
            
            # Get categorized services
            analytics_services = privacy_details.get("analytics_services", [])
            marketing_services = privacy_details.get("marketing_services", [])
            ux_services = privacy_details.get("ux_services", [])
            essential_services = privacy_details.get("essential_services", [])
            
            total_services = len(analytics_services) + len(marketing_services) + len(ux_services) + len(essential_services)
            
            if total_services == 0:
                return
            
            # Check if cookie categories are properly disclosed
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)
            
            if cookie_consent_found and total_services > 3:
                # Check if there are multiple categories that should be disclosed
                categories_found = []
                if analytics_services:
                    categories_found.append("analytics")
                if marketing_services:
                    categories_found.append("marketing")
                if ux_services:
                    categories_found.append("user experience")
                if essential_services:
                    categories_found.append("essential")
                
                if len(categories_found) > 2:  # Multiple categories should be disclosed
                    self.base_checker.add_business_issue(
                        result,
                        title="Disclose cookie categories",
                        impact=f"GDPR requires clear disclosure of cookie categories: {', '.join(categories_found)}",
                        priority="should_fix",
                        fix_time=45,
                        difficulty="medium",
                        category="privacy",
                        technical_details=f"Found {len(categories_found)} cookie categories that should be disclosed to users",
                        fix_instructions="Provide clear information about different cookie categories and allow users to choose which categories to accept",
                        business_value="Ensures transparency and gives users control over their data",
                        recurring_check=True,
                        code_snippets=[
                            {
                                "title": "Cookie Categories Disclosure",
                                "code": "<div class=\"cookie-categories\">\n    <h3>Cookie Categories</h3>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"essential\" checked disabled>\n        <label for=\"essential\">Essential (Required for site function)</label>\n    </div>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"analytics\">\n        <label for=\"analytics\">Analytics (Help us improve the site)</label>\n    </div>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"marketing\">\n        <label for=\"marketing\">Marketing (Personalized ads)</label>\n    </div>\n</div>",
                                "language": "html"
                            }
                        ]
                    )
                
        except Exception as e:
            logger.error(f"Exception in cookie categories check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie categories: {str(e)}", "warning", "privacy")

    def check_cookie_policy_link(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for cookie policy link in consent mechanisms."""
        try:
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)
            
            if not cookie_consent_found:
                return
            
            # Look for cookie policy links
            cookie_policy_patterns = [
                r'\bcookie\s+policy\b',
                r'\bcookie\s+notice\b',
                r'\bcookie\s+information\b',
                r'\bmore\s+about\s+cookies\b',
                r'\blearn\s+more\b'
            ]
            
            cookie_policy_found = False
            all_links = soup.find_all("a", href=True)
            
            for link in all_links:
                link_text = link.get_text(strip=True).lower()
                for pattern in cookie_policy_patterns:
                    if re.search(pattern, link_text, re.IGNORECASE):
                        cookie_policy_found = True
                        break
                if cookie_policy_found:
                    break
            
            self.base_checker.set_check_result(result, "cookie_policy_link_found", cookie_policy_found)
            
            if not cookie_policy_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Add cookie policy link to consent banner",
                    impact="GDPR requires easy access to detailed cookie information",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Cookie consent banner found but no link to detailed cookie policy",
                    fix_instructions="Add a 'Learn more' or 'Cookie Policy' link to your consent banner",
                    business_value="Improves transparency and helps users make informed decisions",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Cookie Banner with Policy Link",
                            "code": "<div class=\"cookie-banner\">\n    <p>We use cookies to improve your experience. <a href=\"/cookie-policy\">Learn more</a></p>\n    <div class=\"cookie-buttons\">\n        <button class=\"btn-accept\">Accept All</button>\n        <button class=\"btn-reject\">Reject All</button>\n    </div>\n</div>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in cookie policy link check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie policy link: {str(e)}", "warning", "privacy")

    def check_cookie_consent_quality(self, soup: BeautifulSoup, result: dict) -> None:
        """Check overall quality of cookie consent implementation."""
        try:
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)
            
            if not cookie_consent_found:
                return
            
            # Check for consent withdrawal mechanism
            withdrawal_patterns = [
                r'\bmanage\s+cookies\b',
                r'\bcookie\s+settings\b',
                r'\bchange\s+cookie\s+preferences\b',
                r'\bupdate\s+consent\b'
            ]
            
            withdrawal_found = False
            all_text = soup.get_text().lower()
            
            for pattern in withdrawal_patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    withdrawal_found = True
                    break
            
            # Also check for withdrawal links
            if not withdrawal_found:
                withdrawal_links = soup.find_all('a', href=re.compile(r'cookie.*setting|manage.*cookie|consent.*setting', re.I))
                if withdrawal_links:
                    withdrawal_found = True
            
            self.base_checker.set_check_result(result, "cookie_consent_withdrawal_found", withdrawal_found)
            
            if not withdrawal_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Add cookie consent withdrawal mechanism",
                    impact="GDPR requires users to easily change their cookie preferences",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Cookie consent found but no mechanism for users to change their preferences",
                    fix_instructions="Add a 'Cookie Settings' or 'Manage Cookies' link that allows users to change their consent choices",
                    business_value="Ensures ongoing compliance and respects user privacy choices",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Cookie Settings Link",
                            "code": "<footer>\n    <a href=\"/cookie-settings\">Cookie Settings</a>\n    <a href=\"/privacy-policy\">Privacy Policy</a>\n</footer>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in cookie consent quality check: {e}")
            self.base_checker.add_issue(result, f"Error checking cookie consent quality: {str(e)}", "warning", "privacy")
