from typing import Optional

try:
    from modules.bbpy.bitbabbler import BitBabbler as _BB
except Exception:
    _BB = None

_cached: Optional[object] = None


def detect() -> bool:
    """Detect if BitBabbler device is available and accessible."""
    return _get() is not None


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


