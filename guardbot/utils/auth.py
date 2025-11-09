"""Authentication utilities: password hashing and verification.

WARNING: This implementation is a simple placeholder and NOT secure.
Do not use in production. For production deployments use a strong
password hashing algorithm such as bcrypt/argon2, store a salt, and
apply proper parameters.
"""


def hash_password(password: str) -> str:
    """Return a deterministic, insecure placeholder hash.

    The behavior is intentionally unchanged for compatibility with the
    existing code. Replace with a secure hasher for real systems.
    """
    return f"SIMPLE_HASH_{password}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against the placeholder hash."""
    return password_hash == f"SIMPLE_HASH_{password}"

