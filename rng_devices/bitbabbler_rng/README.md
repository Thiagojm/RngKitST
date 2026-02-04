# BitBabbler RNG Module

Hardware random number generator interface for BitBabbler devices (Black, White) from bitbabbler.org. Uses USB with FTDI chipset.

## Hardware Requirements

- BitBabbler Black or White device
- USB 2.0+ port
- libusb-1.0 (included for Windows)

## Installation

```bash
pip install pyusb
```

**Windows**: libusb-1.0.dll included in module folder.

**Linux**: Install system libusb: `sudo apt-get install libusb-1.0-0`

**macOS**: `brew install libusb`

## Usage

```python
from bitbabbler_rng import is_device_available, get_bytes, get_bits, get_exact_bits

# Check if device is connected
if is_device_available():
    # Generate 1024 bytes of raw entropy
    raw = get_bytes(1024)
    
    # Generate with XOR folding (whitening)
    # folds=0: raw, folds=1-4: progressively whitened
    folded = get_bytes(1024, folds=2)
    
    # Generate exactly 8192 bits (1024 bytes) for statistical analysis
    # Note: n_bits must be divisible by 8
    data = get_exact_bits(8192, folds=2)  # Exactly 8192 bits with whitening
    ones = sum(bin(b).count('1') for b in data)
    zeros = 8192 - ones
else:
    print("BitBabbler not found")
```

## API Reference

### `is_device_available() -> bool`
Check if BitBabbler device is detected.

### `get_bytes(n_bytes: int, folds: int = 0) -> bytes`
Generate exactly `n_bytes` of random data. Optional folding (0-4).

### `get_bits(n_bits: int, folds: int = 0) -> bytes`
Generate at least `n_bits` of random data. Returns `ceil(n_bits/8)` bytes (may have extra bits).

### `get_exact_bits(n_bits: int, folds: int = 0) -> bytes`
Generate exactly `n_bits` of random data. Returns `n_bits/8` bytes.

**Note:** `n_bits` must be divisible by 8. Raises `ValueError` if not.

### `random_int(min: int = 0, max: Optional[int] = None, folds: int = 0) -> int`
Generate random integer in range `[min, max)`.

### `close() -> None`
Close device connection and release USB resources.

## XOR Folding

Folding applies XOR whitening to improve entropy quality:
- `folds=0`: Raw entropy from device
- `folds=1-4`: XOR adjacent bits progressively

Higher folds reduce throughput but improve statistical quality.

## Troubleshooting

- **Device not found**: Check USB connection and driver (Zadig on Windows)
- **Permission denied** (Linux): Add udev rules or run as root
- **Import error**: Install pyusb: `pip install pyusb`
