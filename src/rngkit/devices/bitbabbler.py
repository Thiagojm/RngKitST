from typing import Optional
import time

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


def reset() -> None:
    """Reset cached BitBabbler device handle.

    Forces subsequent detection/reads to reopen the device, ensuring
    that unplug/plug cycles are reflected immediately.
    """
    global _cached
    try:
        if _cached is not None and hasattr(_cached, "close"):
            _cached.close()  # release USB interface/resources if possible
    except Exception:
        pass
    _cached = None
    # allow OS to fully release interface
    time.sleep(0.1)


def is_open() -> bool:
    """Return True if a BitBabbler handle is currently cached/open."""
    return _cached is not None


def detect_fresh() -> bool:
    """Detect device status bypassing the cached handle.

    Returns
    -------
    bool
        True if device can be opened now, False otherwise.
    """
    reset()
    return detect()


def probe() -> bool:
    """Probe device availability without affecting cached handle.

    Tries to open a temporary handle and closes it immediately.
    Returns True on success, False otherwise.
    """
    if _BB is None:
        return False
    try:
        bb = _BB.open()
        try:
            return True
        finally:
            try:
                if hasattr(bb, "close"):
                    bb.close()
            except Exception:
                pass
    except Exception:
        return False


def get_detection_error() -> str:
    """Get detailed error message for BitBabbler detection failure."""
    if _BB is None:
        return "BitBabbler module not available. Please ensure bbpy is properly installed."
    
    try:
        bb = _BB.open()
        try:
            return "Device detection succeeded"
        finally:
            try:
                if hasattr(bb, "close"):
                    bb.close()
            except Exception:
                pass
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


def close() -> None:
    """Close and clear cached device handle if open."""
    global _cached
    try:
        if _cached is not None and hasattr(_cached, "close"):
            _cached.close()
    except Exception:
        pass
    _cached = None


