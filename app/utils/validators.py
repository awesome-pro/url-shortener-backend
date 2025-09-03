import re
from urllib.parse import urlparse
from typing import Optional


def is_valid_url(url: str) -> bool:
    """Validate if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_short_code(code: str) -> bool:
    """Validate if a string is a valid short code format."""
    if not code or len(code) < 3 or len(code) > 10:
        return False
    
    # Only allow alphanumeric characters, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, code))


def sanitize_url(url: str) -> str:
    """Sanitize and normalize URL."""
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None
