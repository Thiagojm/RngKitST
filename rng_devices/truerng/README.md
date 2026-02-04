# TrueRNG Module

Hardware random number generator interface for TrueRNG devices (TrueRNG3, TrueRNGPro) from ubld.it.

## Hardware Requirements

- TrueRNG3 or TrueRNGPro device
- USB port
- Device driver installed (see device documentation)

## Installation

```bash
pip install pyserial
```

## Usage

```python
from truerng import is_device_available, get_bytes, get_bits, get_exact_bits

# Check if device is connected
if is_device_available():
    # Generate 32 random bytes (256 bits)
    data = get_bytes(32)
    
    # Generate 100 random bits (returns 13 bytes, 104 bits total)
    data = get_bits(100)
    
    # Generate exactly 256 random bits (32 bytes)
    # Note: n_bits must be divisible by 8
    data = get_exact_bits(256)
    
    # Count ones for statistical analysis
    ones = sum(bin(b).count('1') for b in data)
    zeros = len(data) * 8 - ones
else:
    print("TrueRNG not found - check USB connection")
```

## API Reference

### `is_device_available() -> bool`
Check if TrueRNG device is detected on any serial port.

### `get_bytes(n_bytes: int) -> bytes`
Generate exactly `n_bytes` of random data from hardware.

### `get_bits(n_bits: int) -> bytes`
Generate at least `n_bits` of random data. Returns `ceil(n_bits/8)` bytes (may have extra bits).

### `get_exact_bits(n_bits: int) -> bytes`
Generate exactly `n_bits` of random data. Returns `n_bits/8` bytes.

**Note:** `n_bits` must be divisible by 8. Raises `ValueError` if not.

### `random_int(min: int = 0, max: Optional[int] = None) -> int`
Generate random integer in range `[min, max)`.

### `close() -> None`
No-op (connections auto-close after each read).

## Platform Notes

**Windows**: Install device driver from manufacturer.

**Linux**: May need udev rules for serial port access.

**macOS**: Device should appear as `/dev/cu.usbserial-*`.

## Troubleshooting

- **Device not found**: Check USB connection and driver installation
- **Permission denied** (Linux): Add user to `dialout` group
- **Read timeout**: Device may be busy or disconnected
