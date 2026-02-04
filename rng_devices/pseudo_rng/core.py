"""Pseudo RNG core implementation.

Software-based cryptographically secure random number generator using Python's
secrets module. Serves as a fallback when hardware RNGs are not available.
"""

import secrets
from typing import Optional


def is_device_available() -> bool:
    """Check if the pseudo RNG is available.

    The pseudo RNG is always available as it uses Python's standard library.

    Returns:
        Always True
    """
    return True


def get_bytes(n: int) -> bytes:
    """Generate n random bytes of entropy.

    Args:
        n: Number of bytes to generate. Must be positive.

    Returns:
        Random bytes string of length n.

    Raises:
        ValueError: If n <= 0
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    return secrets.token_bytes(n)


def get_bits(n: int) -> bytes:
    """Generate n bits of entropy.

    Returns bytes containing at least n random bits. The result may
    contain extra bits (rounds up to nearest byte boundary).

    Args:
        n: Number of bits to generate. Must be positive.

    Returns:
        Bytes containing at least n random bits.

    Raises:
        ValueError: If n <= 0
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    n_bytes = (n + 7) // 8
    return secrets.token_bytes(n_bytes)


def get_exact_bits(n: int) -> bytes:
    """Generate exactly n bits of entropy.

    Returns bytes containing exactly n random bits. The number of bits
    must be divisible by 8 (byte-aligned).

    Args:
        n: Number of bits to generate. Must be positive and divisible by 8.

    Returns:
        Bytes containing exactly n random bits.

    Raises:
        ValueError: If n <= 0 or if n is not divisible by 8
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n % 8 != 0:
        raise ValueError(f"n must be divisible by 8, got {n}")

    n_bytes = n // 8
    return secrets.token_bytes(n_bytes)


def random_int(min: int = 0, max: Optional[int] = None) -> int:
    """Generate a cryptographically secure random integer.

    Args:
        min: Minimum value (inclusive). Defaults to 0.
        max: Maximum value (exclusive). If None, generates using full range.

    Returns:
        Random integer in range [min, max) if max is specified.

    Raises:
        ValueError: If min >= max or if min < 0 when max is None
    """
    if max is None:
        if min < 0:
            raise ValueError("min must be non-negative when max is None")
        return secrets.randbelow(min) if min > 0 else secrets.randbits(32)

    if min >= max:
        raise ValueError(f"min must be less than max, got min={min}, max={max}")

    return min + secrets.randbelow(max - min)


def close() -> None:
    """Close and release any resources.

    For pseudo_rng, this is a no-op. Provided for API consistency.
    """
    pass
