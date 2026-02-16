from typing import Tuple, Optional
from bs4 import BeautifulSoup


class ContentService:
    """Handles content fetching and HTML parsing."""
    
    def __init__(self):
        pass
    
    def get_rendered_soup(self, url: str, wait_time: int = 2000) -> BeautifulSoup:
        """Load a page with JS and return a BeautifulSoup object."""
        try:
            # Try to import playwright
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(wait_time)
                html = page.content()
                browser.close()
            return BeautifulSoup(html, "html.parser")
        except ImportError:
            # If playwright is not available, raise an exception
            raise ImportError("Playwright is not installed. Please install it with: pip install playwright")
        except Exception as e:
            # If playwright fails for any other reason, raise the exception
            raise Exception(f"Playwright rendering failed: {str(e)}")
    
    def should_parse_html(self, content_type: str) -> bool:
        """Check if content type indicates HTML that should be parsed."""
        return "text/html" in content_type.lower()
