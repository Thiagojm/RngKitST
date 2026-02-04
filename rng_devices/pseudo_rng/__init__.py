"""Pseudo RNG Module - Software-based cryptographically secure random number generator.

This module provides a pure Python implementation using the secrets module
from the standard library. It serves as a fallback when hardware RNGs are
not available.

Example:
    from pseudo_rng import get_bytes, random_int

    # Generate 32 random bytes
    data = get_bytes(32)

    # Generate a random integer between 1 and 100
    num = random_int(1, 100)
"""

from .core import (
    is_device_available,
    get_bytes,
    get_bits,
    get_exact_bits,
    random_int,
    close,
)

__all__ = [
    "is_device_available",
    "get_bytes",
    "get_bits",
    "get_exact_bits",
    "random_int",
    "close",
]
