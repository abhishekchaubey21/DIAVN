import re
from typing import Optional

LEGAL_SUFFIXES = [
    r'\bprivate limited\b', r'\bpvt\.?\s*ltd\.?\b', r'\blimited\b', r'\bltd\.?\b',
    r'\bllp\b', r'\bcorp\.?\b', r'\bcorporation\b', r'\benterprises\b', r'\bsolutions\b',
    r'\bdistributors\b', r'\bdealers\b', r'\bagrotech\b', r'\binfra\b'
]

PLACEHOLDER_SERIAL_PATTERNS = [
    r'^(n/?a|na|none|null|nil)$',
    r'^(test|sample|dummy|demo|example)$',
    r'^(unknown|unspecified|pending|tbd)$',
    r'^(0+|1+|2+|3+|4+|5+|6+|7+|8+|9+)$',
    r'^(12345|123456|1234567|12345678|123456789|012345)$',
    r'^(abc|abcd|abcdef|xyz)$',
    r'^\s*$'
]


def normalize_name(name: Optional[str]) -> str:
    """
    Conservative string normalization for dealer / customer names.
    Preserves original for evidence; creates comparable representation.
    """
    if not name:
        return ""
    cleaned = name.lower().strip()
    # Remove harmless punctuation
    cleaned = re.sub(r'[\.,\'\(\)\-\/]', ' ', cleaned)
    # Remove standard corporate legal suffixes
    for suffix in LEGAL_SUFFIXES:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
    # Collapse multiple whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def normalize_serial(serial: Optional[str]) -> str:
    """
    Standardize serial number for exact and relaxed equality comparison.
    """
    if not serial:
        return ""
    cleaned = serial.upper().strip()
    # Remove whitespace
    cleaned = re.sub(r'\s+', '', cleaned)
    return cleaned


def normalize_product_name(product: Optional[str]) -> str:
    """
    Normalize product / asset category name for category benchmark lookup.
    """
    if not product:
        return ""
    cleaned = product.lower().strip()
    cleaned = re.sub(r'[\.,\'\(\)\-\/]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def is_placeholder_serial(serial: Optional[str]) -> bool:
    """
    Deterministic check for obviously invalid or placeholder serial strings.
    """
    if not serial:
        return True
    cleaned = serial.lower().strip()
    if len(cleaned) < 3 or len(cleaned) > 100:
        return True
    for pattern in PLACEHOLDER_SERIAL_PATTERNS:
        if re.match(pattern, cleaned):
            return True
    return False
