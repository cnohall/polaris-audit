"""
Consent management checker.

This module handles consent-related GDPR compliance checks including
consent quality, withdrawal mechanisms, and consent implementation.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ConsentChecker:
    """Handles consent management checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_consent_quality(self, soup: BeautifulSoup, result: dict) -> None:
        """Check quality of consent mechanisms with reduced false flags."""
        try:
            # Look for pre-ticked checkboxes in consent context only
            pre_ticked_found = False
            checkboxes = soup.find_all('input', type='checkbox')
            
            for checkbox in checkboxes:
                if checkbox.get('checked') is not None:  # More precise check
                    # Only flag if clearly in consent context
                    context = ""
                    parent = checkbox.find_parent()
                    if parent:
                        context = parent.get_text().lower()
                        # Also check siblings and nearby text
                        for sibling in parent.find_next_siblings():
                            if sibling.name and sibling.get_text():
                                context += " " + sibling.get_text().lower()
                                break
                    
                    # More specific consent keywords
                    consent_keywords = [
                        'consent', 'agree to', 'accept', 'gdpr', 'privacy policy',
                        'terms of service', 'newsletter', 'marketing', 'cookies'
                    ]
                    
                    # Exclude functional checkboxes
                    functional_keywords = [
                        'remember me', 'keep me logged in', 'show password', 
                        'default', 'enable', 'notification'
                    ]
                    
                    is_consent_checkbox = any(keyword in context for keyword in consent_keywords)
                    is_functional_checkbox = any(keyword in context for keyword in functional_keywords)
                    
                    if is_consent_checkbox and not is_functional_checkbox:
                        pre_ticked_found = True
                        logger.info(f"Pre-ticked consent checkbox found in context: {context[:100]}")
                        break
            
            # Look for consent withdrawal mechanisms (more permissive)
            withdrawal_found = False
            withdrawal_patterns = [
                r'\bunsubscribe\b',
                r'\bopt\s+out\b',
                r'\bwithdraw\s+consent\b',
                r'\bmanage\s+(consent|preferences)\b',
                r'\bconsent\s+settings\b',
                r'\bchange\s+preferences\b'
            ]
            
            all_text = soup.get_text().lower()
            for pattern in withdrawal_patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    withdrawal_found = True
                    break
            
            # Also check for unsubscribe links
            if not withdrawal_found:
                unsubscribe_links = soup.find_all('a', href=re.compile(r'unsubscribe|opt-out', re.I))
                if unsubscribe_links:
                    withdrawal_found = True
            
            self.base_checker.set_check_result(result, "pre_ticked_consent_found", pre_ticked_found)
            self.base_checker.set_check_result(result, "consent_withdrawal_found", withdrawal_found)
            
            # Add business issues based on findings
            if pre_ticked_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Remove pre-ticked consent boxes",
                    impact="GDPR prohibits pre-ticked boxes for consent - users must actively opt-in",
                    priority="must_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Pre-ticked checkboxes found in consent context - violates GDPR Article 7",
                    fix_instructions="Remove 'checked' attribute from consent checkboxes. Users must actively opt-in.",
                    business_value="Ensures GDPR compliance and avoids fines",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Correct Consent Implementation",
                            "code": "<!-- WRONG: Pre-ticked consent -->\n<input type=\"checkbox\" checked> I agree to marketing emails\n\n<!-- CORRECT: User must actively consent -->\n<input type=\"checkbox\"> I agree to marketing emails (optional)",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Check all consent forms for pre-ticked boxes",
                        "Verify users must actively opt-in for non-essential processing"
                    ]
                )
            
            # Only flag missing withdrawal if consent exists and site processes significant data
            scope = result.get("checks", {}).get("data_processing_scope", {})
            site_complexity = scope.get("site_complexity", "simple")
            has_consent = result.get("checks", {}).get("cookie_consent_found", False)
            
            if not withdrawal_found and has_consent and site_complexity != "simple":
                self.base_checker.add_business_issue(
                    result,
                    title="Add consent withdrawal mechanism",
                    impact="GDPR requires users to withdraw consent as easily as they gave it",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="No clear mechanism found for users to withdraw consent",
                    fix_instructions="Add unsubscribe links or consent management options that are easy to find.",
                    business_value="Ensures GDPR compliance and respects user privacy choices",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Consent Management Links",
                            "code": "<footer>\n  <a href=\"/consent-settings\">Cookie Settings</a>\n  <a href=\"mailto:unsubscribe@company.com\">Unsubscribe</a>\n</footer>",
                            "language": "html"
                        }
                    ],
                    testing_steps=[
                        "Add easy-to-find consent withdrawal options",
                        "Test that withdrawal mechanisms work properly"
                    ]
                )

        except Exception as e:
            logger.error(f"Exception in consent quality check: {e}")
            self.base_checker.add_issue(result, f"Error checking consent quality: {str(e)}", "warning", "privacy")

    def check_consent_granularity(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if consent mechanisms allow granular control."""
        try:
            cookie_consent_found = result.get("checks", {}).get("cookie_consent_found", False)
            
            if not cookie_consent_found:
                return
            
            # Look for granular consent options
            granular_patterns = [
                r'\bmanage\s+cookies\b',
                r'\bcookie\s+preferences\b',
                r'\bcustomize\s+cookies\b',
                r'\bcookie\s+categories\b',
                r'\bessential\s+only\b',
                r'\bnecessary\s+cookies\b'
            ]
            
            granular_found = False
            all_text = soup.get_text().lower()
            
            for pattern in granular_patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    granular_found = True
                    break
            
            # Also check for multiple consent options
            consent_buttons = soup.find_all(['button', 'a'], string=re.compile(r'accept|reject|manage|settings', re.I))
            has_multiple_options = len(consent_buttons) > 2
            
            self.base_checker.set_check_result(result, "granular_consent_found", granular_found)
            self.base_checker.set_check_result(result, "multiple_consent_options", has_multiple_options)
            
            if not granular_found and not has_multiple_options:
                self.base_checker.add_business_issue(
                    result,
                    title="Add granular consent options",
                    impact="GDPR requires users to have control over different types of data processing",
                    priority="nice_to_have",
                    fix_time=45,
                    difficulty="medium",
                    category="privacy",
                    technical_details="Cookie consent found but no granular control options",
                    fix_instructions="Allow users to choose which types of cookies to accept (essential, analytics, marketing, etc.)",
                    business_value="Gives users more control and shows respect for their privacy choices",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Granular Consent Options",
                            "code": "<div class=\"cookie-preferences\">\n    <h3>Cookie Preferences</h3>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"essential\" checked disabled>\n        <label for=\"essential\">Essential (Required)</label>\n    </div>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"analytics\">\n        <label for=\"analytics\">Analytics (Optional)</label>\n    </div>\n    <div class=\"category\">\n        <input type=\"checkbox\" id=\"marketing\">\n        <label for=\"marketing\">Marketing (Optional)</label>\n    </div>\n</div>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in consent granularity check: {e}")
            self.base_checker.add_issue(result, f"Error checking consent granularity: {str(e)}", "warning", "privacy")

    def check_consent_freely_given(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if consent is freely given and not conditional."""
        try:
            # Look for conditional consent patterns
            conditional_patterns = [
                r'\bmust\s+accept\s+to\s+use\b',
                r'\brequired\s+to\s+accept\b',
                r'\baccept\s+to\s+continue\b',
                r'\bmandatory\s+consent\b',
                r'\bconsent\s+required\s+for\s+access\b'
            ]
            
            all_text = soup.get_text().lower()
            conditional_consent_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in conditional_patterns
            )
            
            # Check for consent that's required for basic functionality
            forms = soup.find_all('form')
            consent_required_for_basic = False
            
            for form in forms:
                form_text = form.get_text().lower()
                if any(keyword in form_text for keyword in ['newsletter', 'marketing', 'cookies']):
                    # Check if consent is required for basic form submission
                    required_consent = form.find('input', {'required': True, 'type': 'checkbox'})
                    if required_consent:
                        consent_required_for_basic = True
                        break
            
            self.base_checker.set_check_result(result, "conditional_consent_found", conditional_consent_found)
            self.base_checker.set_check_result(result, "consent_required_for_basic", consent_required_for_basic)
            
            if conditional_consent_found or consent_required_for_basic:
                self.base_checker.add_business_issue(
                    result,
                    title="Make consent truly optional",
                    impact="GDPR requires consent to be freely given - not conditional on service access",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Consent appears to be conditional or required for basic functionality",
                    fix_instructions="Make consent optional and allow users to access basic services without consenting to non-essential processing",
                    business_value="Ensures GDPR compliance and respects user autonomy",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Optional Consent",
                            "code": "<!-- Make consent optional -->\n<form>\n    <input type=\"email\" name=\"email\" required>\n    <input type=\"checkbox\" name=\"newsletter\"> Subscribe to newsletter (optional)\n    <button type=\"submit\">Submit</button>\n</form>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in consent freely given check: {e}")
            self.base_checker.add_issue(result, f"Error checking consent freely given: {str(e)}", "warning", "privacy")

    def check_consent_specific(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if consent is specific and informed."""
        try:
            # Look for vague consent language
            vague_patterns = [
                r'\bwe\s+may\s+use\s+your\s+data\b',
                r'\bdata\s+may\s+be\s+shared\b',
                r'\bwe\s+reserve\s+the\s+right\b',
                r'\bfor\s+any\s+purpose\b',
                r'\bgeneral\s+consent\b'
            ]
            
            all_text = soup.get_text().lower()
            vague_consent_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in vague_patterns
            )
            
            # Look for specific consent language
            specific_patterns = [
                r'\bfor\s+marketing\s+emails\b',
                r'\bfor\s+analytics\s+purposes\b',
                r'\bto\s+improve\s+our\s+service\b',
                r'\bfor\s+personalized\s+content\b'
            ]
            
            specific_consent_found = any(
                re.search(pattern, all_text, re.IGNORECASE) 
                for pattern in specific_patterns
            )
            
            self.base_checker.set_check_result(result, "vague_consent_found", vague_consent_found)
            self.base_checker.set_check_result(result, "specific_consent_found", specific_consent_found)
            
            if vague_consent_found and not specific_consent_found:
                self.base_checker.add_business_issue(
                    result,
                    title="Make consent more specific",
                    impact="GDPR requires consent to be specific about what data is used for",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Consent language is too vague and doesn't specify data usage purposes",
                    fix_instructions="Be specific about what data you collect and how you use it",
                    business_value="Ensures GDPR compliance and builds user trust",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Specific Consent Language",
                            "code": "<!-- Vague consent -->\n<p>We may use your data for various purposes.</p>\n\n<!-- Specific consent -->\n<p>We will use your email address to send you our weekly newsletter and product updates. We will use your browsing data to improve our website performance.</p>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            logger.error(f"Exception in consent specific check: {e}")
            self.base_checker.add_issue(result, f"Error checking consent specific: {str(e)}", "warning", "privacy")

    def check_consent_withdrawal_ease(self, soup: BeautifulSoup, result: dict) -> None:
        """Check if consent withdrawal is as easy as giving consent."""
        try:
            # Look for withdrawal mechanisms
            withdrawal_links = soup.find_all('a', href=re.compile(r'unsubscribe|opt-out|withdraw|consent', re.I))
            withdrawal_buttons = soup.find_all(['button', 'a'], string=re.compile(r'unsubscribe|opt-out|withdraw', re.I))
            
            withdrawal_mechanisms = len(withdrawal_links) + len(withdrawal_buttons)
            
            # Look for consent mechanisms
            consent_links = soup.find_all('a', href=re.compile(r'consent|accept|agree', re.I))
            consent_buttons = soup.find_all(['button', 'a'], string=re.compile(r'accept|agree|consent', re.I))
            
            consent_mechanisms = len(consent_links) + len(consent_buttons)
            
            self.base_checker.set_check_result(result, "withdrawal_mechanisms_count", withdrawal_mechanisms)
            self.base_checker.set_check_result(result, "consent_mechanisms_count", consent_mechanisms)
            
            # Check if withdrawal is as prominent as consent
            if consent_mechanisms > 0 and withdrawal_mechanisms == 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Add consent withdrawal mechanism",
                    impact="GDPR requires withdrawal to be as easy as giving consent",
                    priority="should_fix",
                    fix_time=30,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Consent mechanisms found but no withdrawal mechanisms",
                    fix_instructions="Add unsubscribe links or consent management options that are as prominent as consent options",
                    business_value="Ensures GDPR compliance and respects user privacy choices",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Withdrawal Mechanisms",
                            "code": "<div class=\"consent-management\">\n    <button class=\"btn-consent\">Accept Cookies</button>\n    <a href=\"/consent-settings\" class=\"btn-withdraw\">Manage Preferences</a>\n    <a href=\"/unsubscribe\" class=\"btn-unsubscribe\">Unsubscribe</a>\n</div>",
                            "language": "html"
                        }
                    ]
                )
            elif consent_mechanisms > withdrawal_mechanisms * 2:
                self.base_checker.add_business_issue(
                    result,
                    title="Make withdrawal more prominent",
                    impact="Withdrawal should be as easy to find as consent options",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="easy",
                    category="privacy",
                    technical_details="Consent options are more prominent than withdrawal options",
                    fix_instructions="Make withdrawal options more visible and accessible",
                    business_value="Ensures balanced user experience and GDPR compliance",
                    recurring_check=True
                )
                
        except Exception as e:
            logger.error(f"Exception in consent withdrawal ease check: {e}")
            self.base_checker.add_issue(result, f"Error checking consent withdrawal ease: {str(e)}", "warning", "privacy")
