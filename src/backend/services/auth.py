"""Authentication service module."""


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hashed version.
    
    Args:
        password: The plain text password to verify
        hashed: The hashed password to compare against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    # TODO: Implement proper password hashing verification (e.g., using bcrypt)
    # For now, this is a placeholder
    return password == hashed


def normalize_and_validate_email(email: str) -> str:
    """
    Normalize and validate an email address.
    
    Args:
        email: The email address to normalize and validate
        
    Returns:
        str: The normalized email address (lowercase and stripped)
        
    Raises:
        ValueError: If email is invalid
    """
    email = email.lower().strip()
    
    # Basic email validation
    if not email or '@' not in email:
        raise ValueError("Invalid email address")
    
    return email
