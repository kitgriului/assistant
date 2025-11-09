"""Input validation utilities.

Provides validators for common input types in the GuardBot application.
All validators return (is_valid, error_message) tuples.
"""
import re
from typing import Tuple, Optional
from datetime import datetime


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """Validate phone number format.
    
    Accepts various formats:
    - +7XXXXXXXXXX
    - 8XXXXXXXXXX
    - 7XXXXXXXXXX
    - With spaces/dashes
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_phone_number("+79001234567")
        if not is_valid:
            await message.answer(f"Invalid phone: {error}")
    """
    if not phone:
        return False, "Phone number cannot be empty"
    
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it matches valid patterns
    patterns = [
        r'^\+7\d{10}$',      # +7XXXXXXXXXX
        r'^8\d{10}$',        # 8XXXXXXXXXX
        r'^7\d{10}$',        # 7XXXXXXXXXX
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True, None
    
    return False, "Phone number must be in format +7XXXXXXXXXX or 8XXXXXXXXXX"


def validate_car_number(car_number: str) -> Tuple[bool, Optional[str]]:
    """Validate vehicle registration number.
    
    Accepts Russian license plate formats:
    - А123БВ777 (standard)
    - А123БВ77 (old format)
    - Case insensitive
    - With or without spaces
    
    Args:
        car_number: Car registration number to validate
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_car_number("А123БВ777")
        if not is_valid:
            await message.answer(f"Invalid car number: {error}")
    """
    if not car_number:
        return False, "Car number cannot be empty"
    
    # Remove spaces
    cleaned = car_number.replace(' ', '').upper()
    
    # Russian license plate pattern (simplified)
    # Format: Letter + 3 digits + 2 letters + 2-3 digits (region)
    # Using Latin transliteration: A, B, C, E, H, K, M, O, P, T, X, Y
    pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$'
    
    if re.match(pattern, cleaned):
        return True, None
    
    return False, "Invalid car number format. Example: А123БВ777"


def validate_name(name: str, min_length: int = 2, max_length: int = 255) -> Tuple[bool, Optional[str]]:
    """Validate person name.
    
    Args:
        name: Name to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_name(user_input)
        if not is_valid:
            await message.answer(error)
    """
    if not name:
        return False, "Name cannot be empty"
    
    name = name.strip()
    
    if len(name) < min_length:
        return False, f"Name must be at least {min_length} characters"
    
    if len(name) > max_length:
        return False, f"Name must not exceed {max_length} characters"
    
    # Check for valid characters (letters, spaces, hyphens)
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', name):
        return False, "Name can only contain letters, spaces, and hyphens"
    
    return True, None


def validate_purpose(purpose: str, min_length: int = 5, max_length: int = 512) -> Tuple[bool, Optional[str]]:
    """Validate visit purpose description.
    
    Args:
        purpose: Purpose text to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_purpose(user_input)
        if not is_valid:
            await message.answer(error)
    """
    if not purpose:
        return False, "Purpose cannot be empty"
    
    purpose = purpose.strip()
    
    if len(purpose) < min_length:
        return False, f"Purpose must be at least {min_length} characters"
    
    if len(purpose) > max_length:
        return False, f"Purpose must not exceed {max_length} characters"
    
    return True, None


def validate_datetime_str(datetime_str: str) -> Tuple[bool, Optional[str]]:
    """Validate datetime string format.
    
    Accepts formats:
    - DD.MM.YYYY HH:MM
    - DD.MM.YYYY
    - DD/MM/YYYY HH:MM
    - DD/MM/YYYY
    
    Args:
        datetime_str: DateTime string to validate
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_datetime_str("01.12.2023 14:30")
        if not is_valid:
            await message.answer(error)
    """
    if not datetime_str:
        return False, "Date/time cannot be empty"
    
    # Try different datetime formats
    formats = [
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
    ]
    
    for fmt in formats:
        try:
            parsed_dt = datetime.strptime(datetime_str.strip(), fmt)
            
            # Check if date is not too far in the past
            if parsed_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                return False, "Date cannot be in the past"
            
            # Check if date is not too far in the future (1 year)
            max_future = datetime.now().replace(year=datetime.now().year + 1)
            if parsed_dt > max_future:
                return False, "Date cannot be more than 1 year in the future"
            
            return True, None
            
        except ValueError:
            continue
    
    return False, "Invalid date/time format. Use: DD.MM.YYYY HH:MM or DD.MM.YYYY"


def validate_qr_code(qr_code: str) -> Tuple[bool, Optional[str]]:
    """Validate QR code format.
    
    Args:
        qr_code: QR code string to validate
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_qr_code(scanned_code)
        if not is_valid:
            await message.answer("Invalid QR code")
    """
    if not qr_code:
        return False, "QR code cannot be empty"
    
    # QR code should be 32 hex characters
    if not re.match(r'^[a-f0-9]{32}$', qr_code.lower()):
        return False, "Invalid QR code format"
    
    return True, None


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize text input for safe display.
    
    Removes potentially dangerous characters and trims to max length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (truncates if exceeded)
        
    Returns:
        Sanitized text string
        
    Example:
        safe_text = sanitize_text(user_input, max_length=100)
    """
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized


def validate_rejection_reason(reason: str, min_length: int = 3, max_length: int = 500) -> Tuple[bool, Optional[str]]:
    """Validate rejection reason text.
    
    Args:
        reason: Rejection reason to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
        
    Example:
        is_valid, error = validate_rejection_reason(reason_text)
        if not is_valid:
            await message.answer(error)
    """
    if not reason:
        return False, "Rejection reason cannot be empty"
    
    reason = reason.strip()
    
    if len(reason) < min_length:
        return False, f"Rejection reason must be at least {min_length} characters"
    
    if len(reason) > max_length:
        return False, f"Rejection reason must not exceed {max_length} characters"
    
    return True, None
