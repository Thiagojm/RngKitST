from serial.tools import list_ports
import serial
import os


def detect() -> bool:
    """Detect if TrueRNG device is available and accessible."""
    ports = list(list_ports.comports())
    for p in ports:
        if p[1].startswith("TrueRNG"):
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
        if p[1].startswith("TrueRNG"):
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


