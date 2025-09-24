from serial.tools import list_ports
import serial
import os


def _is_trng_port(p) -> bool:
    """Heuristically determine if a port corresponds to a TrueRNG device.

    Works across platforms by checking description/manufacturer/product strings
    if available, and falling back to tuple indexing when needed.
    """
    try:
        # pyserial 3.x exposes attributes on the ListPortInfo object
        desc = (getattr(p, "description", None) or "")
        manuf = (getattr(p, "manufacturer", None) or "")
        prod = (getattr(p, "product", None) or "")
        text = f"{desc} {manuf} {prod}".lower()
        if "truerng" in text:
            return True
    except Exception:
        pass

    try:
        # Fallback for tuple-like entries: (device, description, ...)
        return str(p[1]).lower().startswith("truerng")
    except Exception:
        return False


def detect() -> bool:
    """Detect if TrueRNG device is available and accessible."""
    ports = list(list_ports.comports())
    for p in ports:
        if _is_trng_port(p):
            return True
    return False


def read_bytes(blocksize: int) -> bytes:
    """Read random bytes from TrueRNG device.
    
    Args:
        blocksize: Number of bytes to read
        
    Returns:
        Random bytes from TrueRNG
        
    Raises:
        RuntimeError: If TrueRNG device not found
    """
    ports = list(list_ports.comports())
    port = None
    for p in ports:
        if _is_trng_port(p):
            try:
                # Prefer attribute if available
                port = getattr(p, "device", None) or str(p[0])
            except Exception:
                port = str(p[0])
            break
    if port is None:
        raise RuntimeError("TrueRNG device not found")
    ser = serial.Serial(port=port, timeout=10)
    try:
        if not ser.isOpen():
            ser.open()
        ser.setDTR(True)
        ser.flushInput()
        data = ser.read(blocksize)
        
        # Linux fix: Reset serial port min setting after pyserial usage
        if os.name == 'posix':
            import subprocess
            try:
                subprocess.run(['stty', '-F', port, 'min', '1'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Ignore if stty fails or not available
                pass
        
        return data
    finally:
        try:
            ser.close()
        except Exception:
            pass


