from typing import Optional

try:
    from modules.bbpy.bitbabbler import BitBabbler as _BB
except Exception:
    _BB = None

_cached: Optional[object] = None


def detect() -> bool:
    """Detect if BitBabbler device is available and accessible."""
    try:
        return _get() is not None
    except Exception:
        return False


def get_detection_error() -> str:
    """Get detailed error message for BitBabbler detection failure."""
    if _BB is None:
        return "BitBabbler module not available. Please ensure bbpy is properly installed."
    
    try:
        _BB.open()
        return "Device detection succeeded"
    except RuntimeError as e:
        if "not found" in str(e).lower():
            return "BitBabbler device not found. Please check USB connection and driver installation."
        elif "initialize" in str(e).lower():
            return "BitBabbler device found but failed to initialize. Try reconnecting the device."
        else:
            return f"BitBabbler error: {str(e)}"
    except Exception as e:
        return f"Unexpected error during BitBabbler detection: {str(e)}"


def _get() -> Optional[object]:
    """Get cached BitBabbler device instance."""
    global _cached
    if _BB is None:
        return None
    if _cached is not None:
        return _cached
    try:
        _cached = _BB.open()
        return _cached
    except Exception:
        _cached = None
        return None


def read_bytes(out_len: int, folds: int = 0) -> bytes:
    """Read random bytes from BitBabbler device.
    
    Args:
        out_len: Number of output bytes to read
        folds: Number of XOR folds to apply (0 = raw, 1-4 = folded)
        
    Returns:
        Random bytes from BitBabbler
        
    Raises:
        RuntimeError: If BitBabbler device not found
    """
    dev = _get()
    if dev is None:
        raise RuntimeError("BitBabbler device not found")
    if folds and folds > 0:
        return dev.read_entropy_folded(out_len, folds)
    return dev.read_entropy(out_len)


