"""BitBabbler RNG Module - Hardware random number generator via USB/FTDI.

Interface for BitBabbler devices (Black, White) from bitbabbler.org.
Uses USB with FTDI chipset for high-speed entropy generation.

Dependencies: pyusb

Example:
    from bitbabbler_rng import is_device_available, get_bytes

    if is_device_available():
        # Get raw entropy
        data = get_bytes(1024)

        # Get folded entropy (XOR whitening)
        folded = get_bytes(1024, folds=2)
    else:
        print("BitBabbler not found")
"""

from typing import Optional
import time

# Import bbpy modules from same package
try:
    from . import bitbabbler as _bb

    _bb_available = True
except Exception:
    _bb_available = False

# Device cache
_cached_device: Optional[object] = None


def is_device_available() -> bool:
    """Check if BitBabbler device is available and accessible.

    Returns:
        True if device is detected and can be opened
    """
    if not _bb_available:
        return False

    try:
        bb = _bb.BitBabbler.open()
        try:
            return True
        finally:
            try:
                bb.close()
            except Exception:
                pass
    except Exception:
        return False


def _get_device() -> Optional[object]:
    """Get cached BitBabbler device or open new one."""
    global _cached_device

    if not _bb_available:
        return None

    if _cached_device is not None:
        return _cached_device

    try:
        _cached_device = _bb.BitBabbler.open()
        return _cached_device
    except Exception:
        return None


def get_bytes(n: int, folds: int = 0) -> bytes:
    """Generate n random bytes from BitBabbler device.

    Args:
        n: Number of bytes to generate. Must be positive.
        folds: XOR folding level (0=raw, 1-4=whitened). Defaults to 0.

    Returns:
        Random bytes from hardware device.

    Raises:
        ValueError: If n <= 0 or invalid folds
        RuntimeError: If device not found or read fails
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if folds < 0 or folds > 4:
        raise ValueError(f"folds must be 0-4, got {folds}")

    if not _bb_available:
        raise RuntimeError("BitBabbler module not available (pyusb not installed)")

    dev = _get_device()
    if dev is None:
        raise RuntimeError("BitBabbler device not found")

    try:
        if folds > 0:
            return dev.read_entropy_folded(n, folds)
        else:
            return dev.read_entropy(n)
    except Exception as e:
        # Reset cache on error
        global _cached_device
        _cached_device = None
        raise RuntimeError(f"Failed to read from BitBabbler: {e}")


def get_bits(n: int, folds: int = 0) -> bytes:
    """Generate n random bits from BitBabbler device.

    Returns bytes containing at least n random bits.
    May contain extra bits (rounds up to byte boundary).

    Args:
        n: Number of bits to generate. Must be positive.
        folds: XOR folding level (0=raw, 1-4=whitened). Defaults to 0.

    Returns:
        Bytes containing at least n random bits.

    Raises:
        ValueError: If n <= 0
        RuntimeError: If device not found
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    n_bytes = (n + 7) // 8
    return get_bytes(n_bytes, folds=folds)


def get_exact_bits(n: int, folds: int = 0) -> bytes:
    """Generate exactly n random bits from BitBabbler device.

    Returns bytes containing exactly n random bits. The number of bits
    must be divisible by 8 (byte-aligned).

    Args:
        n: Number of bits to generate. Must be positive and divisible by 8.
        folds: XOR folding level (0=raw, 1-4=whitened). Defaults to 0.

    Returns:
        Bytes containing exactly n random bits.

    Raises:
        ValueError: If n <= 0 or if n is not divisible by 8
        RuntimeError: If device not found
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if n % 8 != 0:
        raise ValueError(f"n must be divisible by 8, got {n}")

    n_bytes = n // 8
    return get_bytes(n_bytes, folds=folds)


def _bytes_to_int(data: bytes) -> int:
    """Convert bytes to integer."""
    return int.from_bytes(data, "big")


def random_int(min: int = 0, max: Optional[int] = None, folds: int = 0) -> int:
    """Generate a cryptographically secure random integer from BitBabbler.

    Args:
        min: Minimum value (inclusive). Defaults to 0.
        max: Maximum value (exclusive). If None, generates 32-bit value.
        folds: XOR folding level (0=raw, 1-4=whitened). Defaults to 0.

    Returns:
        Random integer in range [min, max).

    Raises:
        ValueError: If min >= max
        RuntimeError: If device not found
    """
    if max is None:
        return _bytes_to_int(get_bytes(4, folds=folds))

    if min >= max:
        raise ValueError(f"min must be less than max, got min={min}, max={max}")

    import math

    range_size = max - min
    bits_needed = max(1, math.ceil(math.log2(range_size)))

    # Use rejection sampling for uniform distribution
    while True:
        data = get_exact_bits(bits_needed, folds=folds)
        val = _bytes_to_int(data)
        if val < range_size:
            return min + val


def close() -> None:
    """Close and release the BitBabbler device connection.

    Closes the cached device handle and releases USB resources.
    Safe to call multiple times.
    """
    global _cached_device
    if _cached_device is not None:
        try:
            _cached_device.close()
        except Exception:
            pass
        _cached_device = None
        time.sleep(0.1)  # Allow OS to release interface
