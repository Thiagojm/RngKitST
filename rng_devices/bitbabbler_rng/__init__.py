"""BitBabbler RNG Module - Hardware random number generator via USB/FTDI.

Interface for BitBabbler devices (Black, White) from bitbabbler.org.
Uses USB with FTDI chipset for high-speed entropy generation.

Dependencies: pyusb
Includes: libusb-1.0.dll (Windows)

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
