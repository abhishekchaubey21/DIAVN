import re
import hashlib
from typing import Optional


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """
    Normalizes phone numbers to standard digit strings.
    Strips country code +91 or leading 0 for 10-digit Indian numbers.
    """
    if not phone or not isinstance(phone, str):
        return None
    
    # Extract all digits
    digits = re.sub(r"\D", "", phone.strip())
    if not digits:
        return None
    
    # Standardize 10-digit numbers with +91 or 0 prefix
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    
    return digits if len(digits) >= 7 else None


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """
    Masks a phone number for privacy-compliant UI rendering.
    Example: '+91-9823000001' -> '+91-98****0001' or '98****0001'
    """
    norm = normalize_phone(phone)
    if not norm:
        return "[Not Provided]"
    if len(norm) <= 4:
        return "****"
    if len(norm) == 10:
        return f"+91-{norm[:2]}****{norm[-4:]}"
    return f"{norm[:2]}****{norm[-3:]}"


def normalize_email(email: Optional[str]) -> Optional[str]:
    """
    Normalizes email address by trimming and lowercasing.
    """
    if not email or not isinstance(email, str):
        return None
    cleaned = email.strip().lower()
    return cleaned if "@" in cleaned and "." in cleaned else None


def mask_email(email: Optional[str]) -> Optional[str]:
    """
    Masks an email address for privacy-compliant UI rendering.
    Example: 'rajesh.sharma@example.synthetic' -> 'r***a@example.synthetic'
    """
    norm = normalize_email(email)
    if not norm:
        return "[Not Provided]"
    try:
        user_part, domain_part = norm.split("@", 1)
        if len(user_part) <= 2:
            masked_user = user_part[0] + "***"
        else:
            masked_user = f"{user_part[0]}***{user_part[-1]}"
        return f"{masked_user}@{domain_part}"
    except Exception:
        return "***@***.***"


def normalize_address(address: Optional[str]) -> Optional[str]:
    """
    Normalizes physical address strings for conservative comparison.
    Converts to lowercase, collapses spaces, removes non-alphanumeric punctuation.
    """
    if not address or not isinstance(address, str):
        return None
    
    cleaned = address.strip().lower()
    # Replace punctuation with single spaces
    cleaned = re.sub(r"[,\.\#\-\/\\_\(\)]", " ", cleaned)
    # Standardize common abbreviations
    cleaned = re.sub(r"\b(industrial area|indl area)\b", "midc", cleaned)
    cleaned = re.sub(r"\b(plot no|plot number|survey no|sy no|sy)\b", "plot", cleaned)
    cleaned = re.sub(r"\b(road|rd)\b", "rd", cleaned)
    cleaned = re.sub(r"\b(sector|sec)\b", "sec", cleaned)
    # Collapse multiple whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    return cleaned if len(cleaned) >= 5 else None


def mask_address(address: Optional[str]) -> Optional[str]:
    """
    Masks an address to provide location summary without full street detail.
    Example: 'Plot 45, MIDC Phase II, Bhosari, Pune' -> 'Plot 45, MIDC... [Pune]'
    """
    if not address or not isinstance(address, str):
        return "[Not Provided]"
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 2:
        return f"{parts[0]}... [{parts[-1]}]"
    return address[:15] + "..." if len(address) > 15 else address


def normalize_serial(serial: Optional[str]) -> Optional[str]:
    """
    Normalizes serial number for cross-case matching.
    """
    if not serial or not isinstance(serial, str):
        return None
    cleaned = re.sub(r"[^A-Za-z0-9\-]", "", serial.strip().upper())
    return cleaned if len(cleaned) >= 3 else None


def hash_attribute(val: Optional[str]) -> Optional[str]:
    """
    Produces deterministic SHA-256 digest with prefix for audit traceability.
    """
    if not val:
        return None
    digest = hashlib.sha256(val.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"
