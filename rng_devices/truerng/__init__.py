"""TrueRNG Module - Hardware random number generator via USB serial.

Interface for TrueRNG devices (TrueRNG3, TrueRNGPro) from ubld.it.
Connects via USB and appears as a serial port.

Dependencies: pyserial

Example:
    from truerng import is_device_available, get_bytes

    if is_device_available():
        data = get_bytes(32)
    else:
        print("TrueRNG device not found")
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
