"""
Form accessibility checker.

This module handles form-related accessibility checks including
form labels, required field indicators, error handling, and form structure.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FormChecker:
    """Handles form accessibility checks."""

    def __init__(self, base_checker):
        """Initialize with reference to base checker for common methods."""
        self.base_checker = base_checker

    def check_form_accessibility(self, soup: BeautifulSoup, result: dict) -> None:
        """Enhanced form accessibility checking."""
        try:
            inputs = soup.find_all(["input", "textarea", "select"])
            form_inputs = [inp for inp in inputs if inp.get("type", "").lower() not in ["hidden", "submit", "button", "reset"]]
            
            issues = 0
            total_inputs = len(form_inputs)
            problematic_inputs = []
            
            for input_elem in form_inputs:
                has_label = self._has_accessible_label(input_elem, soup)
                has_required_indicator = self._has_required_indicator(input_elem)
                
                if not has_label:
                    issues += 1
                    # Collect specific problematic input details
                    input_type = input_elem.get("type", "text")
                    input_name = input_elem.get("name", "unnamed")
                    input_id = input_elem.get("id", "no-id")
                    problematic_inputs.append(f"Form field '{input_name}' ({input_type}) - needs a label so users know what to enter")
                elif input_elem.get("required") and not has_required_indicator:
                    issues += 1
                    input_type = input_elem.get("type", "text")
                    input_name = input_elem.get("name", "unnamed")
                    input_id = input_elem.get("id", "no-id")
                    problematic_inputs.append(f"Required field '{input_name}' ({input_type}) - should clearly show it's required (add asterisk or 'required' text)")

            score = max(0, 100 - (issues * 20))
            self.base_checker.set_check_result(result, "form_accessibility_score", score)
            self.base_checker.set_check_result(result, "form_inputs_without_labels", issues)
            self.base_checker.set_check_result(result, "total_form_inputs", total_inputs)

            if issues > 0 and total_inputs > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve form accessibility",
                    impact=f"{issues} form fields are difficult for screen reader users",
                    priority="should_fix",
                    fix_time=issues * 5,
                    difficulty="easy",
                    category="accessibility",
                    count=issues,
                    examples=problematic_inputs,  # Show all examples
                    total_forms=total_inputs,
                    element_type="forms",
                    technical_details=f"{issues} form accessibility issues found",
                    fix_instructions="Add proper labels and required field indicators to all form fields",
                    business_value="Makes your forms usable by everyone, improving conversions",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Form Fields",
                            "code": "<form>\n    <label for=\"email\">Email Address *</label>\n    <input type=\"email\" id=\"email\" name=\"email\" required aria-describedby=\"email-error\">\n    <div id=\"email-error\" class=\"error-message\" aria-live=\"polite\"></div>\n    \n    <button type=\"submit\">Submit</button>\n</form>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking forms: {str(e)}", "warning", "accessibility")

    def _has_accessible_label(self, input_elem, soup) -> bool:
        """Check if input has accessible labeling."""
        # Check for explicit label
        input_id = input_elem.get("id")
        if input_id and soup.find("label", {"for": input_id}):
            return True
        
        # Check for wrapped label
        if input_elem.find_parent("label"):
            return True
        
        # Check for ARIA labeling
        if input_elem.get("aria-label") or input_elem.get("aria-labelledby"):
            return True
        
        # Check for title (less preferred but acceptable)
        if input_elem.get("title"):
            return True
            
        return False

    def _has_required_indicator(self, input_elem) -> bool:
        """Check if required field has proper indicator."""
        if not input_elem.get("required"):
            return True  # Not required, so no indicator needed
        
        # Check for aria-required
        if input_elem.get("aria-required"):
            return True
        
        # Check for visual indicator in associated label
        input_id = input_elem.get("id")
        if input_id:
            label = input_elem.find_parent().find("label", {"for": input_id})
            if label and ("*" in label.get_text() or "required" in label.get_text().lower()):
                return True
        
        return False

    def check_form_error_handling(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for error identification and description."""
        try:
            # Look for form error patterns
            error_elements = soup.find_all(class_=re.compile(r'error|invalid|danger'))
            error_messages = soup.find_all(attrs={"role": "alert"})
            aria_describedby = soup.find_all(attrs={"aria-describedby": True})
            
            has_error_handling = len(error_elements) > 0 or len(error_messages) > 0 or len(aria_describedby) > 0
            
            self.base_checker.set_check_result(result, "error_handling_present", has_error_handling)
            
            # Only suggest improvement if there are forms but no error handling
            forms = soup.find_all("form")
            if len(forms) > 0 and not has_error_handling:
                self.base_checker.add_business_issue(
                    result,
                    title="Add form error handling",
                    impact="Users can't understand what went wrong when form submission fails",
                    priority="nice_to_have",
                    fix_time=30,
                    difficulty="medium",
                    category="accessibility",
                    technical_details="No error identification patterns found for forms",
                    fix_instructions="Add clear error messages and associate them with form fields using aria-describedby",
                    business_value="Helps users understand and fix form submission problems",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Form Error Handling",
                            "code": "<form>\n    <label for=\"email\">Email Address</label>\n    <input type=\"email\" id=\"email\" aria-describedby=\"email-error\" class=\"invalid\">\n    <div id=\"email-error\" role=\"alert\" class=\"error-message\">\n        Please enter a valid email address\n    </div>\n</form>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking error handling: {str(e)}", "warning", "accessibility")

    def check_form_fieldset_legends(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for proper fieldset and legend usage in forms."""
        try:
            fieldsets = soup.find_all("fieldset")
            fieldsets_without_legends = 0
            
            for fieldset in fieldsets:
                if not fieldset.find("legend"):
                    fieldsets_without_legends += 1
            
            self.base_checker.set_check_result(result, "fieldsets_without_legends", fieldsets_without_legends)
            
            if fieldsets_without_legends > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Add legends to fieldsets",
                    impact="Screen reader users can't understand grouped form fields",
                    priority="nice_to_have",
                    fix_time=15,
                    difficulty="easy",
                    category="accessibility",
                    technical_details=f"Found {fieldsets_without_legends} fieldsets without legends",
                    fix_instructions="Add legend elements to describe grouped form fields",
                    business_value="Makes grouped form fields accessible to screen reader users",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Fieldset with Legend",
                            "code": "<fieldset>\n    <legend>Contact Information</legend>\n    <label for=\"name\">Name</label>\n    <input type=\"text\" id=\"name\" name=\"name\">\n    \n    <label for=\"email\">Email</label>\n    <input type=\"email\" id=\"email\" name=\"email\">\n</fieldset>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking fieldsets: {str(e)}", "warning", "accessibility")

    def check_form_autocomplete(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for autocomplete attributes on form fields."""
        try:
            form_inputs = soup.find_all(["input", "textarea", "select"])
            inputs_without_autocomplete = 0
            total_relevant_inputs = 0
            problematic_inputs = []

            # Fields that should have autocomplete
            autocomplete_fields = ["email", "name", "tel", "address", "city", "state", "zip", "country"]

            for input_elem in form_inputs:
                input_type = input_elem.get("type", "").lower()
                input_name = input_elem.get("name", "").lower()
                input_id = input_elem.get("id", "")

                # Check if this field should have autocomplete
                should_have_autocomplete = (
                    input_type in ["email", "tel", "text"] or
                    any(field in input_name for field in autocomplete_fields)
                )

                if should_have_autocomplete:
                    total_relevant_inputs += 1
                    if not input_elem.get("autocomplete"):
                        inputs_without_autocomplete += 1

                        # Create identifier for the field
                        field_identifier = input_name or input_id or f"{input_type} field"

                        # Suggest appropriate autocomplete value
                        suggested_autocomplete = self._get_suggested_autocomplete(input_type, input_name)

                        problematic_inputs.append(
                            f"Field '{field_identifier}' ({input_type}) - add autocomplete='{suggested_autocomplete}' to help users fill it faster"
                        )

            self.base_checker.set_check_result(result, "inputs_without_autocomplete", inputs_without_autocomplete)

            if inputs_without_autocomplete > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Add autocomplete attributes to form fields",
                    impact="Users can't benefit from browser autocomplete features",
                    priority="nice_to_have",
                    fix_time=20,
                    difficulty="easy",
                    category="accessibility",
                    count=inputs_without_autocomplete,
                    examples=problematic_inputs,
                    total_elements=total_relevant_inputs,
                    element_type="forms",
                    technical_details=f"Found {inputs_without_autocomplete} form fields without autocomplete attributes",
                    fix_instructions="Add appropriate autocomplete attributes to help users fill out forms faster",
                    business_value="Improves user experience and form completion rates",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Form with Autocomplete",
                            "code": "<form>\n    <label for=\"name\">Full Name</label>\n    <input type=\"text\" id=\"name\" name=\"name\" autocomplete=\"name\">\n    \n    <label for=\"email\">Email</label>\n    <input type=\"email\" id=\"email\" name=\"email\" autocomplete=\"email\">\n    \n    <label for=\"phone\">Phone</label>\n    <input type=\"tel\" id=\"phone\" name=\"phone\" autocomplete=\"tel\">\n</form>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking autocomplete: {str(e)}", "warning", "accessibility")

    def _get_suggested_autocomplete(self, input_type: str, input_name: str) -> str:
        """Suggest appropriate autocomplete value based on input type and name."""
        input_name = input_name.lower()

        if input_type == "email" or "email" in input_name:
            return "email"
        elif input_type == "tel" or "phone" in input_name or "tel" in input_name:
            return "tel"
        elif "name" in input_name:
            if "first" in input_name or "fname" in input_name:
                return "given-name"
            elif "last" in input_name or "lname" in input_name:
                return "family-name"
            else:
                return "name"
        elif "address" in input_name:
            if "line1" in input_name or "street" in input_name:
                return "address-line1"
            elif "line2" in input_name:
                return "address-line2"
            else:
                return "street-address"
        elif "city" in input_name:
            return "address-level2"
        elif "state" in input_name or "province" in input_name:
            return "address-level1"
        elif "zip" in input_name or "postal" in input_name:
            return "postal-code"
        elif "country" in input_name:
            return "country"
        else:
            return "on"  # Generic autocomplete

    def check_form_validation(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for proper form validation attributes and patterns."""
        try:
            form_inputs = soup.find_all(["input", "textarea", "select"])
            validation_issues = 0
            
            for input_elem in form_inputs:
                input_type = input_elem.get("type", "").lower()
                
                # Check for required fields without proper validation
                if input_elem.get("required"):
                    if input_type == "email" and not input_elem.get("pattern"):
                        validation_issues += 1
                    elif input_type == "tel" and not input_elem.get("pattern"):
                        validation_issues += 1
                    elif input_type == "url" and not input_elem.get("pattern"):
                        validation_issues += 1
            
            self.base_checker.set_check_result(result, "form_validation_issues", validation_issues)
            
            if validation_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve form validation",
                    impact="Form validation may not provide clear feedback to users",
                    priority="nice_to_have",
                    fix_time=25,
                    difficulty="medium",
                    category="accessibility",
                    technical_details=f"Found {validation_issues} form validation issues",
                    fix_instructions="Add proper validation patterns and clear error messages for form fields",
                    business_value="Prevents form submission errors and improves user experience",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Form Validation Examples",
                            "code": "<form>\n    <label for=\"email\">Email Address</label>\n    <input type=\"email\" id=\"email\" name=\"email\" required \n           pattern=\"[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$\"\n           aria-describedby=\"email-help\">\n    <div id=\"email-help\">Please enter a valid email address</div>\n    \n    <label for=\"phone\">Phone Number</label>\n    <input type=\"tel\" id=\"phone\" name=\"phone\" required\n           pattern=\"[0-9]{3}-[0-9]{3}-[0-9]{4}\"\n           placeholder=\"123-456-7890\">\n</form>",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking form validation: {str(e)}", "warning", "accessibility")

    def check_form_submit_buttons(self, soup: BeautifulSoup, result: dict) -> None:
        """Check for proper submit button accessibility."""
        try:
            submit_buttons = soup.find_all(["button", "input"], type=["submit", "button"])
            button_issues = 0
            
            for button in submit_buttons:
                button_text = button.get_text(strip=True) or button.get("value", "")
                
                # Check for empty or generic button text
                if not button_text or button_text.lower() in ["submit", "button", "click"]:
                    button_issues += 1
                
                # Check for proper button type
                if button.name == "input" and not button.get("type") in ["submit", "button", "reset"]:
                    button_issues += 1
            
            self.base_checker.set_check_result(result, "submit_button_issues", button_issues)
            
            if button_issues > 0:
                self.base_checker.add_business_issue(
                    result,
                    title="Improve submit button accessibility",
                    impact="Submit buttons are not clearly labeled for screen reader users",
                    priority="nice_to_have",
                    fix_time=10,
                    difficulty="easy",
                    category="accessibility",
                    technical_details=f"Found {button_issues} submit button issues",
                    fix_instructions="Use descriptive text for submit buttons and proper button elements",
                    business_value="Makes form submission clear and accessible",
                    recurring_check=True,
                    code_snippets=[
                        {
                            "title": "Accessible Submit Buttons",
                            "code": "<!-- Good: Descriptive button text -->\n<button type=\"submit\">Create Account</button>\n<button type=\"submit\">Send Message</button>\n\n<!-- Good: Input with descriptive value -->\n<input type=\"submit\" value=\"Subscribe to Newsletter\">",
                            "language": "html"
                        }
                    ]
                )
                
        except Exception as e:
            self.base_checker.add_issue(result, f"Error checking submit buttons: {str(e)}", "warning", "accessibility")
