import re
from urllib.parse import urlparse


def validate_url(url: str):
    """Validate and normalize URL.

    Returns:
        tuple: (normalized_url, error_message) — error is None on success.
    """
    if not url or not isinstance(url, str):
        return None, "URL is required and must be a string"

    url = url.strip()
    if not url:
        return None, "URL cannot be empty"

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None, "Invalid URL format"

        domain_pattern = re.compile(
            r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        if not domain_pattern.match(parsed.netloc):
            return None, "Invalid domain format"
    except Exception:
        return None, "Invalid URL format"

    return url, None
