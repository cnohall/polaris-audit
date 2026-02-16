import requests
import time
import urllib3
from typing import Tuple, Optional

# Disable SSL warnings for environments with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HTTPClient:
    """Handles HTTP requests with retry logic and rate limiting."""

    def __init__(self, config):
        self.timeout = config.get("timeout", 15)
        self.headers = config.get("headers", {})
        self.retry_count = config.get("retry_count", 2)
        self.rate_limit_delay = config.get("rate_limit_delay", 1)

        # Use a session for cookie persistence and connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_url(self, url: str) -> Tuple[Optional[requests.Response], Optional[str]]:
        """Fetch URL with error handling and retries."""
        last_error = None

        for attempt in range(self.retry_count + 1):
            try:
                if attempt > 0:
                    time.sleep(self.rate_limit_delay * attempt)

                # Try with SSL verification first
                try:
                    resp = self.session.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=True,
                    )
                except requests.exceptions.SSLError:
                    # If SSL verification fails, try without verification
                    resp = self.session.get(
                        url,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=False,
                    )

                # Accept any response that has content we can analyze
                # (403/429 pages still have headers worth auditing)
                if resp.status_code < 500:
                    return resp, None

                resp.raise_for_status()
                return resp, None

            except requests.exceptions.Timeout:
                last_error = "Request timed out"
            except requests.exceptions.ConnectionError:
                last_error = "Connection error occurred"
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP Error: {e.response.status_code}"
                break  # Don't retry 5xx errors
            except requests.exceptions.SSLError as e:
                last_error = f"SSL Error: {str(e)}"
                break
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {e}"

        return None, last_error
