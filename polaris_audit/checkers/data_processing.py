"""
Data processing compliance checker.

This module handles data processing-related GDPR compliance checks including
data subject rights, retention policies, and third-party services.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DataProcessingChecker:
    """Handles data processing compliance checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def assess_data_processing_scope(self, soup: BeautifulSoup, result: dict) -> None:
        """Assess the scope of data processing to avoid false flags on simple sites."""
        try:
            # Check for data collection indicators
            data_collection_indicators = [
                # Forms that collect personal data
                'email', 'name', 'phone', 'address', 'newsletter', 'subscribe',
                'contact', 'registration', 'signup', 'login', 'account',
                # E-commerce indicators
                'cart', 'checkout', 'payment', 'order', 'purchase', 'shop',
                # Analytics and tracking
                'analytics', 'tracking', 'remarketing', 'advertising',
                # User accounts and profiles
                'profile', 'dashboard', 'settings', 'preferences'
            ]
            
            # Check forms for personal data collection
            forms = soup.find_all('form')
            collects_personal_data = False
            has_user_accounts = False
            has_ecommerce = False
            
            for form in forms:
                form_text = form.get_text().lower()
                form_html = str(form).lower()
                
                # Check for email/personal data inputs
                if (form.find('input', type='email') or 
                    re.search(r'(email|name|phone|address)', form_html) or
                    any(indicator in form_text for indicator in ['email', 'name', 'phone', 'address', 'newsletter'])):
                    collects_personal_data = True
                
                # Check for account-related forms
                if any(indicator in form_text for indicator in ['login', 'register', 'signup', 'account']):
                    has_user_accounts = True
                
                # Check for e-commerce forms
                if any(indicator in form_text for indicator in ['cart', 'checkout', 'payment', 'order']):
                    has_ecommerce = True
            
            # Check page content for business type indicators
            page_text = soup.get_text().lower()
            
            # E-commerce indicators
            ecommerce_terms = ['buy now', 'add to cart', 'checkout', 'price', 'product', 'shop']
            if any(term in page_text for term in ecommerce_terms):
                has_ecommerce = True
            
            # User account indicators
            account_terms = ['my account', 'dashboard', 'profile', 'login', 'sign up']
            if any(term in page_text for term in account_terms):
                has_user_accounts = True
            
            # Check for third-party tracking services (from privacy_details)
            privacy_details = result.get("privacy_details", {})
            has_tracking = privacy_details.get("third_party_services_count", 0) > 0
            
            # Determine site complexity and GDPR applicability
            site_complexity = "simple"
            if has_ecommerce or has_user_accounts:
                site_complexity = "complex"
            elif collects_personal_data or has_tracking:
                site_complexity = "medium"
            
            # Store assessment results
            self.base_checker.set_check_result(result, "data_processing_scope", {
                "collects_personal_data": collects_personal_data,
                "has_user_accounts": has_user_accounts,
                "has_ecommerce": has_ecommerce,
                "has_tracking": has_tracking,
                "site_complexity": site_complexity,
                "gdpr_likely_applies": collects_personal_data or has_tracking or has_user_accounts or has_ecommerce
            })
            
            logger.info(f"Data processing scope: {site_complexity}, GDPR applies: {collects_personal_data or has_tracking}")

        except Exception as e:
            logger.error(f"Exception in data processing scope assessment: {e}")
            # Default to assuming GDPR applies to avoid missing real issues
            self.base_checker.set_check_result(result, "data_processing_scope", {
                "collects_personal_data": True,
                "has_user_accounts": False,
                "has_ecommerce": False,
                "has_tracking": True,
                "site_complexity": "medium",
                "gdpr_likely_applies": True
            })

    def check_data_subject_rights(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for data subject rights implementation with context awareness."""
        try:
            # Only check for complex sites that clearly process personal data
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            collects_personal_data = scope.get("collects_personal_data", False)
            
            if site_complexity == "simple" and not collects_personal_data:
                logger.info("Simple site with no personal data collection - skipping data subject rights check")
                return

            # Look for data subject rights terms
            rights_patterns = [
                r'\bright\s+to\s+be\s+forgotten\b',
                r'\bright\s+to\s+erasure\b',
                r'\bright\s+to\s+data\s+portability\b',
                r'\bright\s+to\s+rectification\b',
                r'\bright\s+to\s+access\b',
                r'\bdata\s+subject\s+rights\b',
                r'\bdelete\s+my\s+(data|account)\b',
                r'\bexport\s+my\s+data\b',
                r'\brequest\s+my\s+data\b'
            ]
            
            rights_found = False
            rights_forms_found = False
            
            # Check for rights mentions
            all_text = soup.get_text().lower()
            for pattern in rights_patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    rights_found = True
                    break
            
            # Look for contact methods for data requests (more lenient)
            if rights_found or collects_personal_data:
                # Check for forms or contact methods
                contact_methods = (
                    soup.find_all('a', href=re.compile(r'mailto:')) or
                    soup.find_all(['form', 'button'], string=re.compile(r'contact|request|email', re.I)) or
                    soup.find_all(string=re.compile(r'contact us|email us|privacy@|data@', re.I))
                )
                if contact_methods:
                    rights_forms_found = True
            
            self.base_checker.set_check_result(result, "data_subject_rights_found", rights_found)
            self.base_checker.set_check_result(result, "data_subject_rights_forms_found", rights_forms_found)
            
            # Only flag missing rights for sites that clearly need them
            needs_rights_info = (
                site_complexity in ["medium", "complex"] or
                scope.get("has_user_accounts", False) or
                scope.get("has_ecommerce", False)
            )
            
            if not rights_found and needs_rights_info:
                priority = "should_fix" if site_complexity == "medium" else "must_fix"
                
                self.base_checker.add_business_issue(
                    result,
                    title="Add data subject rights information",
                    impact="GDPR requires clear information about user data rights for sites processing personal data",
                    priority=priority,
                    fix_time=45,
                    difficulty="easy",
                    category="privacy",
                    technical_details=f"Site appears to process personal data ({site_complexity} complexity) but no data subject rights information found",
                    fix_instructions="Add a section explaining data subject rights in your privacy policy with contact information for requests.",
                    business_value="Ensures GDPR compliance and builds trust by showing users their rights",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Data Subject Rights Section",
                            "code": "<h3>Your Data Rights</h3>\n<p>You have the right to:</p>\n<ul>\n  <li>Access your personal data</li>\n  <li>Correct inaccurate data</li>\n  <li>Request deletion of your data</li>\n  <li>Export your data</li>\n</ul>\n<p>Contact: <a href=\"mailto:privacy@company.com\">privacy@company.com</a></p>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Add data rights information to your privacy policy",
                        "Provide clear contact method for requests",
                        "Test that contact method works"
                    ],
                    resources=[
                        {
                            "label": "GDPR Data Subject Rights Guide",
                            "url": "https://gdpr.eu/data-subject-rights/"
                        }
                    ]
                )

        except Exception as e:
            logger.error(f"Exception in data subject rights check: {e}")
            self.base_checker.add_issue(result, f"Error checking data subject rights: {str(e)}", "warning", "privacy")

    def check_data_retention_policies(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for data retention period disclosures with context awareness."""
        try:
            # Only check for sites that clearly process personal data long-term
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            has_user_accounts = scope.get("has_user_accounts", False)
            has_ecommerce = scope.get("has_ecommerce", False)
            
            if site_complexity == "simple" and not has_user_accounts and not has_ecommerce:
                logger.info("Simple site without long-term data storage - skipping retention policy check")
                return

            # Look for data retention terms
            retention_patterns = [
                r'\bdata\s+retention\b',
                r'\bretention\s+period\b',
                r'\bhow\s+long\s+we\s+(keep|store|retain)\b',
                r'\bstorage\s+period\b',
                r'\bdelete\s+data\s+after\b',
                r'\bpurge\s+data\b'
            ]
            
            retention_found = False
            specific_periods_found = False
            
            all_text = soup.get_text().lower()
            for pattern in retention_patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    retention_found = True
                    break
            
            # Look for specific time periods near retention context
            if retention_found:
                time_period_pattern = r'\b(\d+)\s*(days?|weeks?|months?|years?)\b'
                context_window = 200  # characters around retention mentions
                
                for pattern in retention_patterns:
                    matches = re.finditer(pattern, all_text, re.IGNORECASE)
                    for match in matches:
                        start = max(0, match.start() - context_window)
                        end = min(len(all_text), match.end() + context_window)
                        context = all_text[start:end]
                        
                        if re.search(time_period_pattern, context):
                            specific_periods_found = True
                            break
                    if specific_periods_found:
                        break
            
            self.base_checker.set_check_result(result, "data_retention_found", retention_found)
            self.base_checker.set_check_result(result, "data_retention_periods_found", specific_periods_found)
            
            # Only flag for sites that likely need retention policies
            needs_retention_policy = (
                has_user_accounts or 
                has_ecommerce or 
                site_complexity == "complex"
            )
            
            if not retention_found and needs_retention_policy:
                priority = "should_fix" if site_complexity == "medium" else "must_fix"
                
                self.base_checker.add_business_issue(
                    result,
                    title="Add data retention policy",
                    impact="GDPR requires transparency about how long personal data is kept",
                    priority=priority,
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details=f"Site processes personal data ({site_complexity} complexity) but no retention policy found",
                    fix_instructions="Add information about how long you keep different types of data in your privacy policy.",
                    business_value="Ensures GDPR transparency and builds trust with users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Data Retention Section",
                            "code": "<h3>Data Retention</h3>\n<ul>\n  <li>Account data: Until account deletion</li>\n  <li>Analytics data: 26 months maximum</li>\n  <li>Support data: 1 year after resolution</li>\n</ul>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Define retention periods for different data types",
                        "Add retention information to privacy policy",
                        "Implement automatic data deletion where possible"
                    ]
                )

        except Exception as e:
            logger.error(f"Exception in data retention check: {e}")
            self.base_checker.add_issue(result, f"Error checking data retention policies: {str(e)}", "warning", "privacy")

    def check_third_party_services(self, result: dict) -> None:
        """Check for third-party services that require GDPR compliance."""
        try:
            privacy_details = result.get("privacy_details", {})
            third_party_services = privacy_details.get("third_party_services", [])
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            
            if not third_party_services:
                return
            
            # Categorize services by type
            analytics_services = privacy_details.get("analytics_services", [])
            marketing_services = privacy_details.get("marketing_services", [])
            ux_services = privacy_details.get("ux_services", [])
            
            # Check if consent is required for these services
            consent_required_services = marketing_services + ux_services
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)
            
            if consent_required_services and not cookie_consent_found:
                # Determine priority based on number of services and site complexity
                service_count = len(consent_required_services)
                if service_count > 3 or site_complexity == "complex":
                    priority = "must_fix"
                elif service_count > 1:
                    priority = "should_fix"
                else:
                    priority = "nice_to_have"
                
                # Create service list for display
                service_names = [service.get("name", "Unknown") for service in consent_required_services]
                service_list = ", ".join(service_names)
                
                self.base_checker.add_business_issue(
                    result,
                    title=f"Third-party services require cookie consent ({len(consent_required_services)} services detected)",
                    impact=f"GDPR requires explicit consent for tracking services: {service_list}",
                    priority=priority,
                    fix_time=60 if service_count > 3 else 30,
                    difficulty="medium",
                    category="privacy",
                    technical_details=f"Detected {len(consent_required_services)} third-party services that require user consent under GDPR",
                    fix_instructions="Implement a cookie consent banner that allows users to opt-in to non-essential services before they load",
                    business_value="Prevents GDPR fines and ensures legal compliance for data processing",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Basic cookie consent implementation",
                            "code": "<!-- Cookie consent banner -->\n<div id=\"cookie-banner\" class=\"cookie-banner\">\n  <p>We use cookies to improve your experience. <a href=\"/privacy-policy\">Learn more</a></p>\n  <button onclick=\"acceptCookies()\">Accept All</button>\n  <button onclick=\"manageCookies()\">Manage Preferences</button>\n</div>\n\n<script>\nfunction acceptCookies() {\n  // Load all third-party services\n  loadAnalytics();\n  loadMarketing();\n  document.getElementById('cookie-banner').style.display = 'none';\n}\n</script>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Check that cookie banner appears on first visit",
                        "Verify users can accept or decline cookies",
                        "Test that third-party services only load after consent",
                        "Ensure consent preferences are remembered"
                    ],
                    resources=[
                        {
                            "label": "GDPR Cookie Consent Guide",
                            "url": "https://gdpr.eu/cookies/"
                        },
                        {
                            "label": "Cookie Consent Examples",
                            "url": "https://www.cookiepro.com/knowledge/what-is-cookie-consent/"
                        }
                    ],
                    services_detected=consent_required_services
                )
                
                logger.info(f"Third-party services issue added: {len(consent_required_services)} services requiring consent")
            else:
                logger.info(f"Third-party services found but consent already implemented or not required")
                
            # Specific check for Google Fonts privacy issue
            self._check_google_fonts_privacy(third_party_services, result)

        except Exception as e:
            logger.error(f"Exception in third-party services check: {e}")
            self.base_checker.add_issue(result, f"Error checking third-party services: {str(e)}", "warning", "privacy")

    def check_data_processing_lawfulness(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for lawful basis of data processing disclosure."""
        try:
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            
            if site_complexity == "simple":
                return
            
            # Look for lawful basis mentions
            lawful_basis_patterns = [
                r'\blawful\s+basis\b',
                r'\blegal\s+basis\b',
                r'\bconsent\s+as\s+legal\s+basis\b',
                r'\blegitimate\s+interest\b',
                r'\bcontract\s+performance\b',
                r'\blegal\s+obligation\b'
            ]
            
            all_text = soup.get_text().lower()
            lawful_basis_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in lawful_basis_patterns
            )
            
            self.base_checker.set_check_result(result, "lawful_basis_disclosed", lawful_basis_found)
            
            if not lawful_basis_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Disclose lawful basis for data processing",
                    impact="GDPR requires clear disclosure of the legal basis for processing personal data",
                    priority="nice_to_have",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="No information found about the lawful basis for data processing",
                    fix_instructions="Add information about your legal basis for processing personal data (consent, legitimate interest, etc.)",
                    business_value="Ensures GDPR compliance and transparency",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Lawful Basis Disclosure",
                            "code": "<h3>Legal Basis for Processing</h3>\n<ul>\n  <li>Consent: For marketing emails and analytics</li>\n  <li>Legitimate Interest: For website security and fraud prevention</li>\n  <li>Contract Performance: For order processing and customer service</li>\n</ul>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in data processing lawfulness check: {e}")
            self.base_checker.add_issue(result, f"Error checking data processing lawfulness: {str(e)}", "warning", "privacy")

    def check_data_breach_procedures(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for data breach notification procedures."""
        try:
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            
            if site_complexity == "simple":
                return
            
            # Look for data breach procedures
            breach_patterns = [
                r'\bdata\s+breach\b',
                r'\bsecurity\s+incident\b',
                r'\bbreach\s+notification\b',
                r'\bdata\s+protection\s+incident\b'
            ]
            
            all_text = soup.get_text().lower()
            breach_procedures_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in breach_patterns
            )
            
            self.base_checker.set_check_result(result, "breach_procedures_disclosed", breach_procedures_found)
            
            if not breach_procedures_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Add data breach notification procedures",
                    impact="GDPR requires procedures for handling and notifying about data breaches",
                    priority="nice_to_have",
                    fix_time=45,
                    difficulty="medium",
                    category="privacy",
                    technical_details="No information found about data breach procedures",
                    fix_instructions="Add information about how you handle data breaches and notify affected users",
                    business_value="Ensures GDPR compliance and shows preparedness",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Data Breach Procedures",
                            "code": "<h3>Data Breach Procedures</h3>\n<p>In the event of a data breach, we will:</p>\n<ul>\n  <li>Notify the relevant supervisory authority within 72 hours</li>\n  <li>Inform affected individuals without undue delay</li>\n  <li>Document all breaches and remedial actions taken</li>\n</ul>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in data breach procedures check: {e}")
            self.base_checker.add_issue(result, f"Error checking data breach procedures: {str(e)}", "warning", "privacy")

    def _check_google_fonts_privacy(self, third_party_services: list, result: dict) -> None:
        """Check for Google Fonts privacy issues specifically."""
        try:
            # Find Google Fonts usage
            google_fonts_services = [
                service for service in third_party_services
                if service.get("name") == "google_fonts"
            ]

            if not google_fonts_services:
                return

            # Google Fonts specifically shares IP addresses with Google
            # This has been ruled illegal in some EU courts without consent
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)

            if not cookie_consent_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Google Fonts loads without user consent",
                    impact="Google Fonts shares user IP addresses with Google, requiring GDPR consent. Some EU courts have ruled this illegal without user consent.",
                    priority="should_fix",
                    fix_time=45,
                    difficulty={
                        "level": "medium",
                        "description": "Requires implementing consent management or self-hosting fonts"
                    },
                    category="privacy",
                    technical_details="Google Fonts API (fonts.googleapis.com) shares visitor IP addresses with Google, creating a privacy concern under GDPR Article 6",
                    fix_instructions="Either implement cookie consent before loading Google Fonts, or self-host the fonts to avoid third-party data sharing",
                    business_value="Ensures GDPR compliance and avoids potential fines. EU courts have established legal precedent for GDPR violations via Google Fonts. While initial fines start at €100+, this creates liability for larger penalties and legal costs",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Self-host Google Fonts (recommended)",
                            "code": "/* Download fonts locally and serve from your domain */\n@font-face {\n  font-family: 'Open Sans';\n  src: url('/fonts/opensans-regular.woff2') format('woff2'),\n       url('/fonts/opensans-regular.woff') format('woff');\n  font-display: swap;\n}\n\nbody {\n  font-family: 'Open Sans', Arial, sans-serif;\n}",
                            "language": "css"
                        },
                        {
                            "title": "Load Google Fonts with consent",
                            "code": "function loadGoogleFonts() {\n  if (userHasConsented()) {\n    const link = document.createElement('link');\n    link.href = 'https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap';\n    link.rel = 'stylesheet';\n    document.head.appendChild(link);\n  }\n}\n\n// Only call after user consents\ndocument.addEventListener('cookieConsentGiven', loadGoogleFonts);",
                            "language": "javascript"
                        }
                    ],
                    testing_steps=[
                        "Check network tab for requests to fonts.googleapis.com or fonts.gstatic.com",
                        "Verify fonts only load after user consent",
                        "Test that website still works with fallback fonts if consent is denied",
                        "Validate font-display: swap is used for performance"
                    ],
                    resources=[
                        {
                            "label": "Google Fonts Privacy Guide",
                            "url": "https://developers.google.com/fonts/docs/getting_started#privacy"
                        },
                        {
                            "label": "EU Court Ruling on Google Fonts",
                            "url": "https://www.dr-privacy.com/google-fonts-and-gdpr-update/"
                        },
                        {
                            "label": "Font Loading Best Practices",
                            "url": "https://web.dev/font-best-practices/"
                        }
                    ]
                )
                logger.info("Google Fonts privacy issue added")

        except Exception as e:
            logger.error(f"Exception in Google Fonts privacy check: {e}")
