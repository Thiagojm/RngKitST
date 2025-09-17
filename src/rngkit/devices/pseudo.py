import secrets
from typing import Union


def detect() -> bool:
    """Detect if pseudo RNG is available (always True)."""
    return True


def read_bytes(n: int) -> bytes:
    """Generate n random bytes using Python's secrets module.
    
    Args:
        n: Number of bytes to generate (must be positive)
        
    Returns:
        Random bytes
        
    Raises:
        ValueError: If n is not positive
    """
    if n <= 0:
        raise ValueError("n must be positive")
    return secrets.token_bytes(n)


