"""
Privacy policy validation checker.

This module handles privacy policy detection, validation, and content analysis
for GDPR compliance requirements.
"""

import re
import logging
import string
import difflib
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PrivacyPolicyChecker:
    """Handles privacy policy validation checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_privacy_policy_link(self, soup, phrases, language, result, render_js=False):
        """Check for privacy policy link with context awareness to reduce false flags."""

        try:
            # Check if GDPR likely applies before flagging missing policy
            scope = result.get("checks", {}).get("data_processing_scope", {})
            gdpr_likely_applies = scope.get("gdpr_likely_applies", True)

            def normalize(s):
                if not s:
                    return ""
                s = s.replace("\xa0", " ")
                s = s.strip().lower()
                s = s.translate(str.maketrans("", "", string.punctuation))
                s = re.sub(r"\s+", " ", s)
                return s

            # Enhanced multilingual patterns
            multilingual_patterns = [
                r"\bprivacy\b", r"privacy\s*policy", r"privacy\s*notice", r"data\s*protection",
                r"gdpr", r"dataskydd", r"personuppgift",  # Swedish
                r"politique\s+de\s+confidentialite", r"confidentialité",  # French
                r"política\s+de\s+privacidad", r"privacidad",            # Spanish
                r"informativa\s+sulla\s+privacy", r"privacy",             # Italian
                r"datenschutzerklärung", r"datenschutz",                  # German
                r"개인정보처리방침", r"개인정보",                           # Korean
                r"политика\s+конфиденциальности", r"конфиденциальность"   # Russian
            ]

            raw_patterns = phrases.get(language, {}).get("privacy", multilingual_patterns)
            if not raw_patterns:
                raw_patterns = multilingual_patterns

            patterns = [re.compile(p, re.IGNORECASE) for p in raw_patterns]

            if render_js and hasattr(self, "get_rendered_soup"):
                soup = self.get_rendered_soup(result.get("final_url", result.get("url")))

            privacy_links = []
            all_links = soup.find_all("a", href=True)

            for link in all_links:
                raw_text = link.get_text(" ", strip=True) or ""
                raw_href = link.get("href") or ""
                text = normalize(raw_text)
                href = normalize(raw_href)

                matched = False
                for pattern in patterns:
                    if pattern.search(text) or pattern.search(href):
                        matched = True
                        break

                # More conservative fuzzy matching
                if not matched:
                    keywords = ["privacy", "privacidad", "confidentialite", "datenschutz"]
                    for kw in keywords:
                        if difflib.SequenceMatcher(None, text, kw).ratio() > 0.85:  # Increased threshold
                            matched = True
                            break

                if matched:
                    privacy_links.append({"text": raw_text, "href": raw_href})

            privacy_link_found = len(privacy_links) > 0
            self.base_checker.set_check_result(result, "privacy_policy_link_found", privacy_link_found)
            self.base_checker.set_check_result(result, "privacy_policy_links", privacy_links)

            # Only add business issue if GDPR likely applies AND policy is missing
            if not privacy_link_found and gdpr_likely_applies:
                # Privacy policy is critical for GDPR compliance
                priority = "must_fix"
                
                self.base_checker.add_business_issue(
                    result,
                    title="Add a Privacy Policy link",
                    impact=f"Required by GDPR law for sites processing personal data - potential fines without one",
                    priority=priority,
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="No privacy policy link detected on website that appears to process personal data",
                    fix_instructions="Add a 'Privacy Policy' link in your website footer or main menu that explains how you handle personal data.",
                    business_value="Protects your business from GDPR fines and builds customer trust",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Footer link example",
                            "code": "<footer>\n  <div class=\"footer-links\">\n    <a href=\"/privacy-policy\">Privacy Policy</a>\n    <a href=\"/terms-of-service\">Terms of Service</a>\n    <a href=\"/contact\">Contact</a>\n  </div>\n</footer>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Look for 'Privacy Policy' or similar text on your website",
                        "Check that the link works and leads to a privacy policy page",
                        "Verify the privacy policy covers your actual data processing activities"
                    ],
                    resources=[
                        {
                            "label": "GDPR Privacy Policy Template",
                            "url": "https://gdpr.eu/privacy-policy-template/"
                        }
                    ]
                )
            elif not privacy_link_found and not gdpr_likely_applies:
                logger.info("No privacy policy found, but site appears to have minimal data processing - no issue added")
            else:
                logger.info("Privacy policy link found, no issue added")

        except Exception as e:
            logger.error(f"Exception in privacy policy check: {e}")
            self.base_checker.add_issue(result, f"Error checking privacy policy links: {str(e)}", "warning", "privacy")

    def check_privacy_policy_content(self, soup: BeautifulSoup, result: dict) -> None:
        """Check privacy policy content for required GDPR elements."""
        try:
            privacy_links = result.get("checks", {}).get("privacy_policy_links", [])
            
            if not privacy_links:
                return
            
            # Look for required GDPR elements in privacy policy content
            required_elements = {
                "data_collection": [
                    r'\bwhat\s+data\s+we\s+collect\b',
                    r'\bpersonal\s+data\s+collection\b',
                    r'\binformation\s+we\s+gather\b'
                ],
                "data_usage": [
                    r'\bhow\s+we\s+use\s+your\s+data\b',
                    r'\bdata\s+processing\s+purposes\b',
                    r'\bwhy\s+we\s+collect\s+data\b'
                ],
                "data_sharing": [
                    r'\bdata\s+sharing\b',
                    r'\bthird\s+party\s+sharing\b',
                    r'\bwho\s+we\s+share\s+with\b'
                ],
                "data_retention": [
                    r'\bdata\s+retention\b',
                    r'\bhow\s+long\s+we\s+keep\b',
                    r'\bstorage\s+period\b'
                ],
                "user_rights": [
                    r'\bdata\s+subject\s+rights\b',
                    r'\byour\s+rights\b',
                    r'\baccess\s+your\s+data\b'
                ],
                "contact_info": [
                    r'\bcontact\s+us\b',
                    r'\bprivacy\s+officer\b',
                    r'\bdata\s+protection\s+officer\b'
                ]
            }
            
            # Get all text content
            all_text = soup.get_text().lower()
            
            found_elements = {}
            for element, patterns in required_elements.items():
                found_elements[element] = any(
                    re.search(pattern, all_text, re.IGNORECASE) 
                    for pattern in patterns
                )
            
            missing_elements = [k for k, v in found_elements.items() if not v]
            
            self.base_checker.set_check_result(result, "privacy_policy_elements_found", found_elements)
            self.base_checker.set_check_result(result, "privacy_policy_missing_elements", missing_elements)
            
            if missing_elements:
                element_descriptions = {
                    "data_collection": "what data you collect",
                    "data_usage": "how you use the data",
                    "data_sharing": "who you share data with",
                    "data_retention": "how long you keep data",
                    "user_rights": "user rights and how to exercise them",
                    "contact_info": "contact information for privacy inquiries"
                }
                
                missing_descriptions = [element_descriptions.get(elem, elem) for elem in missing_elements]
                
                self.base_checker.add_business_issue(
                    result,
                    title="Improve privacy policy content",
                    impact=f"Privacy policy missing key GDPR elements: {', '.join(missing_descriptions)}",
                    priority="should_fix",
                    fix_time=60,
                    difficulty="medium",
                    category="privacy",
                    technical_details=f"Missing elements: {', '.join(missing_elements)}",
                    fix_instructions="Add comprehensive information about data collection, usage, sharing, retention, user rights, and contact information",
                    business_value="Ensures full GDPR compliance and builds user trust",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Privacy Policy Structure",
                            "code": "<h2>What Data We Collect</h2>\n<p>We collect...</p>\n\n<h2>How We Use Your Data</h2>\n<p>We use your data to...</p>\n\n<h2>Data Sharing</h2>\n<p>We share data with...</p>\n\n<h2>Data Retention</h2>\n<p>We keep data for...</p>\n\n<h2>Your Rights</h2>\n<p>You have the right to...</p>\n\n<h2>Contact Us</h2>\n<p>For privacy questions: privacy@company.com</p>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in privacy policy content check: {e}")
            self.base_checker.add_issue(result, f"Error checking privacy policy content: {str(e)}", "warning", "privacy")

    def check_privacy_policy_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if privacy policy is easily accessible."""
        try:
            privacy_links = result.get("checks", {}).get("privacy_policy_links", [])
            
            if not privacy_links:
                return
            
            # Check if privacy policy link is in footer or main navigation
            footer_links = soup.find_all("footer")
            nav_links = soup.find_all(["nav", "ul", "ol"], class_=re.compile(r"nav|menu", re.I))
            
            footer_found = False
            nav_found = False
            
            for link in privacy_links:
                href = link.get("href", "")
                
                # Check if link is in footer
                for footer in footer_links:
                    if footer.find("a", href=href):
                        footer_found = True
                        break
                
                # Check if link is in navigation
                for nav in nav_links:
                    if nav.find("a", href=href):
                        nav_found = True
                        break
            
            self.base_checker.set_check_result(result, "privacy_policy_in_footer", footer_found)
            self.base_checker.set_check_result(result, "privacy_policy_in_nav", nav_found)
            
            if not footer_found and not nav_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Make privacy policy more accessible",
                    impact="Privacy policy should be easily findable in footer or main navigation",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Privacy policy link found but not in footer or main navigation",
                    fix_instructions="Move privacy policy link to website footer or main navigation menu",
                    business_value="Improves user experience and ensures easy access to privacy information",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Footer Placement",
                            "code": "<footer>\n    <div class=\"footer-links\">\n        <a href=\"/privacy-policy\">Privacy Policy</a>\n        <a href=\"/terms\">Terms of Service</a>\n        <a href=\"/contact\">Contact</a>\n    </div>\n</footer>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in privacy policy accessibility check: {e}")
            self.base_checker.add_issue(result, f"Error checking privacy policy accessibility: {str(e)}", "warning", "privacy")

    def check_privacy_policy_language(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if privacy policy is in clear, understandable language."""
        try:
            privacy_links = result.get("checks", {}).get("privacy_policy_links", [])
            
            if not privacy_links:
                return
            
            # Look for complex legal language that might be hard to understand
            complex_terms = [
                r'\bnotwithstanding\b',
                r'\bherein\b',
                r'\baforesaid\b',
                r'\bwhereas\b',
                r'\bheretofore\b',
                r'\bhereinafter\b'
            ]
            
            all_text = soup.get_text().lower()
            complex_terms_found = sum(
                1 for term in complex_terms 
                if re.search(term, all_text, re.IGNORECASE)
            )
            
            self.base_checker.set_check_result(result, "privacy_policy_complex_terms", complex_terms_found)
            
            if complex_terms_found > 3:
                self.base_checker.add_business_issue(
                    result,
                    title="Simplify privacy policy language",
                    impact="GDPR requires privacy policies to be clear and understandable",
                    priority="nice_to_have",
                    fix_time=45,
                    difficulty="medium",
                    category="privacy",
                    technical_details=f"Found {complex_terms_found} complex legal terms that may be hard to understand",
                    fix_instructions="Rewrite privacy policy in plain language that users can easily understand",
                    business_value="Improves user trust and ensures GDPR compliance",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Plain Language Example",
                            "code": "<!-- Instead of complex legal language -->\n<p>Notwithstanding the foregoing, the data controller shall...</p>\n\n<!-- Use clear, simple language -->\n<p>We will use your email address to send you updates about our service.</p>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in privacy policy language check: {e}")
            self.base_checker.add_issue(result, f"Error checking privacy policy language: {str(e)}", "warning", "privacy")

    def check_privacy_policy_updates(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if privacy policy includes update notification mechanism."""
        try:
            privacy_links = result.get("checks", {}).get("privacy_policy_links", [])
            
            if not privacy_links:
                return
            
            # Look for update notification patterns
            update_patterns = [
                r'\blast\s+updated\b',
                r'\bversion\s+\d+',
                r'\bupdated\s+on\b',
                r'\bchanges\s+to\s+this\s+policy\b',
                r'\bpolicy\s+updates\b'
            ]
            
            all_text = soup.get_text().lower()
            update_info_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in update_patterns
            )
            
            self.base_checker.set_check_result(result, "privacy_policy_update_info", update_info_found)
            
            if not update_info_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Add privacy policy update information",
                    impact="GDPR requires transparency about policy changes",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="easy",
                    category="privacy",
                    technical_details="No information found about when privacy policy was last updated",
                    fix_instructions="Add a 'Last Updated' date and information about how users will be notified of changes",
                    business_value="Shows transparency and helps users track policy changes",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Update Information",
                            "code": "<div class=\"policy-update\">\n    <p><strong>Last Updated:</strong> January 1, 2024</p>\n    <p>We will notify you of any changes to this policy by email or website notice.</p>\n</div>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in privacy policy updates check: {e}")
            self.base_checker.add_issue(result, f"Error checking privacy policy updates: {str(e)}", "warning", "privacy")
