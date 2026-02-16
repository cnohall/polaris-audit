import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup


class CookieAnalysisService:
    """Handles cookie and third-party tracking analysis."""
    
    def __init__(self):
        # Categorized third-party services by GDPR compliance requirements
        self.third_party_patterns = {
            # ESSENTIAL SERVICES - No consent required
            'essential_services': {
                'cloudflare': [
                    r'cloudflare\.com',
                    r'cf-cdn\.net',
                    r'cloudflareinsights\.com'
                ],
                'cdn_services': [
                    r'jsdelivr\.net',
                    r'cdnjs\.cloudflare\.com',
                    r'unpkg\.com',
                    r'cdn\.skypack\.dev'
                ],
                'security_services': [
                    r'recaptcha\.net',
                    r'google\.com/recaptcha',
                    r'hcaptcha\.com'
                ]
            },
            
            # ANALYTICS SERVICES - Basic consent or legitimate interest
            'analytics_services': {
                'google_analytics': [
                    r'google-analytics\.com',
                    r'googletagmanager\.com',
                    r'gtag\(',
                    r'ga\(',
                    r'google\.com/analytics',
                    r'UA-\d+-\d+',  # Universal Analytics ID
                    r'G-[A-Z0-9]{10}',  # Google Analytics 4 ID
                ],
                'microsoft_clarity': [
                    r'c\.clarity\.ms',
                    r'clarity\.ms',
                ],
                'plausible': [
                    r'plausible\.io',
                    r'plausible\.js',
                ],
                'matomo': [
                    r'matomo\.org',
                    r'piwik\.js',
                    r'_paq\.push',
                ],
                'hotjar': [
                    r'hotjar\.com',
                    r'hj\(',
                    r'_hjSessionUser_\d+=',
                ],
                'fullstory': [
                    r'fullstory\.com',
                    r'fs\.identify',
                ]
            },
            
            # MARKETING/ADVERTISING SERVICES - Explicit consent required
            'marketing_services': {
                'facebook_pixel': [
                    r'facebook\.net',
                    r'connect\.facebook\.net',
                    r'fbq\(',
                    r'facebook\.com/tr',
                    r'_fbp=',
                    r'_fbc=',
                ],
                'google_ads': [
                    r'googleadservices\.com',
                    r'googlesyndication\.com',
                    r'google\.com/ads',
                    r'AW-\d+',  # Google Ads conversion ID
                ],
                'linkedin_insight': [
                    r'snap\.licdn\.com',
                    r'linkedin\.com/insight',
                    r'_linkedin_partner_id',
                ],
                'twitter_pixel': [
                    r'static\.ads-twitter\.com',
                    r'twitter\.com/i/jot',
                    r'twq\(',
                ],
                'tiktok_pixel': [
                    r'analytics\.tiktok\.com',
                    r'tiktok\.com/i18n/pixel',
                    r'ttq\.',
                ],
                'google_tag_manager': [
                    r'googletagmanager\.com/gtm\.js',
                    r'GTM-[A-Z0-9]{6,7}',
                    r'dataLayer',
                ]
            },
            
            # USER EXPERIENCE SERVICES - May require consent depending on data collected
            'ux_services': {
                'intercom': [
                    r'intercom\.io',
                    r'widget\.intercom\.io',
                    r'Intercom',
                ],
                'mixpanel': [
                    r'mixpanel\.com',
                    r'mixpanel\.track',
                ],
                'amplitude': [
                    r'amplitude\.com',
                    r'amplitude\.init',
                ],
                'segment': [
                    r'segment\.com',
                    r'analytics\.segment\.com',
                ],
                'heap': [
                    r'heapanalytics\.com',
                    r'heap\.track',
                ]
            },

            # FONT SERVICES - Privacy concern: shares IP addresses and enables tracking
            'font_services': {
                'google_fonts': [
                    r'fonts\.googleapis\.com',
                    r'fonts\.gstatic\.com',
                    r'gstatic\.com/fonts',
                    r'@import.*fonts\.googleapis',
                    r'link.*href.*fonts\.googleapis',
                ],
                'adobe_fonts': [
                    r'use\.typekit\.net',
                    r'typekit\.com',
                    r'use\.edgefonts\.net',
                    r'fonts\.adobe\.com',
                ],
                'font_awesome': [
                    r'maxcdn\.bootstrapcdn\.com.*font-awesome',
                    r'fontawesome\.com',
                    r'use\.fontawesome\.com',
                    r'fa-brands|fa-solid|fa-regular',
                ],
                'font_squirrel': [
                    r'fontsquirrel\.com',
                    r'fonts\.fontsquirrel',
                ],
                'fonts_com': [
                    r'fast\.fonts\.net',
                    r'fonts\.com',
                    r'webfonts\.fonts\.com',
                ]
            }
        }

    def analyze_cookies_and_tracking(self, response, soup: BeautifulSoup = None) -> Dict[str, Any]:
        """Analyze cookies and third-party tracking services with proper categorization."""
        detected_services = []
        essential_services = []
        analytics_services = []
        marketing_services = []
        ux_services = []
        
        # Get all content for analysis
        html_content = ""
        response_text = ""
        response_headers = ""
        
        if soup:
            html_content = str(soup)
        
        if hasattr(response, 'text'):
            response_text = response.text
            
        if hasattr(response, 'headers'):
            response_headers = str(response.headers)
        
        # Combine all content for comprehensive analysis
        all_content = f"{html_content} {response_text} {response_headers}".lower()
        
        # Check for services by category
        for category, services in self.third_party_patterns.items():
            for service_name, patterns in services.items():
                for pattern in patterns:
                    if re.search(pattern, all_content, re.IGNORECASE):
                        service_info = {
                            "name": service_name.replace('_', ' ').title(),
                            "category": category,
                            "type": self._get_service_type(category, service_name),
                            "consent_required": self._requires_consent(category, service_name),
                            "pattern_matched": pattern
                        }
                        detected_services.append(service_info)
                        
                        # Categorize for detailed analysis
                        if category == "essential_services":
                            essential_services.append(service_info)
                        elif category == "analytics_services":
                            analytics_services.append(service_info)
                        elif category == "marketing_services":
                            marketing_services.append(service_info)
                        elif category == "ux_services":
                            ux_services.append(service_info)
                        elif category == "font_services":
                            # Font services don't have their own list but are consent-required
                            ux_services.append(service_info)  # Add to UX for consent requirement
                        break
        
        # Only flag as pre-consent violation if marketing/UX services are detected
        # Essential and basic analytics are generally allowed
        cookies_before_consent = len(marketing_services) > 0 or len(ux_services) > 0
        
        # Initialize detection flags
        cookie_banner_found = False
        privacy_policy_found = False
        
        if soup:
            # Enhanced cookie consent banner detection
            cookie_consent_indicators = [
                'cookie', 'consent', 'privacy', 'gdpr', 'accept', 'decline', 'reject',
                'allow', 'permit', 'enable', 'disable', 'manage cookies', 'cookie settings',
                'cookie policy', 'cookie preferences', 'cookie banner', 'cookie notice',
                'data protection', 'privacy settings', 'tracking preferences'
            ]
            
            # Check HTML content for consent-related text
            html_lower = html_content.lower()
            if any(indicator in html_lower for indicator in cookie_consent_indicators):
                cookie_banner_found = True
            
            # Check for common cookie consent banner elements with more selectors
            consent_selectors = [
                '[class*="cookie" i]', '[id*="cookie" i]',
                '[class*="consent" i]', '[id*="consent" i]',
                '[class*="banner" i]', '[id*="banner" i]',
                '[class*="popup" i]', '[id*="popup" i]',
                '[class*="modal" i]', '[id*="modal" i]',
                '[class*="gdpr" i]', '[id*="gdpr" i]',
                '[class*="privacy" i]', '[id*="privacy" i]',
                '[data-testid*="cookie" i]', '[data-testid*="consent" i]',
                '[role="dialog"]', '[role="alertdialog"]'
            ]
            
            for selector in consent_selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        # Check if any of these elements contain consent-related text
                        for element in elements:
                            element_text = element.get_text().lower()
                            if any(indicator in element_text for indicator in cookie_consent_indicators):
                                cookie_banner_found = True
                                break
                        if cookie_banner_found:
                            break
                except Exception:
                    continue
            
            # Check for cookie-related buttons and links
            cookie_buttons = soup.find_all(['button', 'a', 'input'], 
                                         string=re.compile(r'accept|decline|reject|allow|manage|settings|preferences|ok|yes|no|cookie|consent', re.I))
            if cookie_buttons:
                cookie_banner_found = True
            
            # Enhanced privacy policy detection
            privacy_indicators = [
                'privacy', 'privacy policy', 'privacy notice', 'data protection',
                'terms of service', 'terms and conditions', 'legal', 'gdpr'
            ]
            
            # Check for privacy policy links with more patterns
            privacy_link_patterns = [
                r'privacy', r'privacy-policy', r'privacy_policy', r'privacy-policy\.html',
                r'terms', r'legal', r'gdpr', r'data-protection', r'privacy-notice'
            ]
            
            for pattern in privacy_link_patterns:
                privacy_links = soup.find_all('a', href=re.compile(pattern, re.I))
                if privacy_links:
                    privacy_policy_found = True
                    break
            
            # Check for privacy policy text in links
            privacy_text_links = soup.find_all('a', string=re.compile(r'privacy|privacy policy|terms|legal', re.I))
            if privacy_text_links:
                privacy_policy_found = True
            
            # Check for privacy policy in footer or common locations
            footer_selectors = ['footer', '[class*="footer" i]', '[id*="footer" i]', '[class*="bottom" i]']
            for selector in footer_selectors:
                try:
                    footer = soup.select_one(selector)
                    if footer:
                        footer_text = footer.get_text().lower()
                        if any(indicator in footer_text for indicator in privacy_indicators):
                            privacy_policy_found = True
                            break
                except Exception:
                    continue
        else:
            # Fallback analysis when soup is not available
            response_lower = response_text.lower()
            
            # Basic text-based detection
            if any(indicator in response_lower for indicator in ['cookie', 'consent', 'privacy', 'gdpr']):
                cookie_banner_found = True
            
            if any(indicator in response_lower for indicator in ['privacy', 'privacy policy', 'terms']):
                privacy_policy_found = True
        
        return {
            "cookies_before_consent": cookies_before_consent,
            "cookie_banner_found": cookie_banner_found,
            "privacy_policy_found": privacy_policy_found,
            "third_party_services_count": len(detected_services),
            "essential_services": essential_services,
            "analytics_services": analytics_services,
            "marketing_services": marketing_services,
            "ux_services": ux_services,
            "tracking_services": marketing_services + ux_services,  # Only marketing/UX require consent
            "third_party_services": detected_services
        }
    
    def _get_service_type(self, category: str, service_name: str) -> str:
        """Determine the service type based on category and name."""
        if category == "essential_services":
            return "essential"
        elif category == "analytics_services":
            return "analytics"
        elif category == "marketing_services":
            return "marketing"
        elif category == "ux_services":
            return "ux"
        else:
            return "other"
    
    def _requires_consent(self, category: str, service_name: str) -> bool:
        """Determine if a service requires explicit consent."""
        # Essential services never require consent
        if category == "essential_services":
            return False
        
        # Analytics services may require consent depending on data collected
        # Basic analytics often fall under legitimate interest
        if category == "analytics_services":
            # Google Analytics 4 and basic analytics can often use legitimate interest
            if service_name in ["google_analytics", "microsoft_clarity", "plausible"]:
                return False  # Often legitimate interest
            return True  # Other analytics services typically need consent
        
        # Marketing, UX, and font services always require consent
        if category in ["marketing_services", "ux_services", "font_services"]:
            return True

        return True  # Default to requiring consent
