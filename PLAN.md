# RNG Devices Modularization Plan

## Overview
Create three standalone, reusable Python modules for random number generation that can be used independently in other projects.

## Module Structure

```
rng_devices/
├── bitbabbler_rng/          # Self-contained BitBabbler module
│   ├── __init__.py         # Main API
│   ├── bitbabbler.py       # Core BitBabbler class (from modules/bbpy/)
│   ├── ftdi.py            # FTDI USB interface (from modules/bbpy/)
│   └── libusb-1.0.dll     # Windows library (optional)
│
├── truerng/                 # TrueRNG via USB Serial
│   └── __init__.py         # Main API
│
└── pseudo_rng/              # Python secrets-based
    └── __init__.py         # Main API
```

## Common API (All Modules)

### Core Methods

```python
def get_bytes(n: int) -> bytes
    """Generate n random bytes of entropy.
    
    Args:
        n: Number of bytes to generate
        
    Returns:
        Random bytes
        
    Raises:
        ValueError: If n <= 0
        RuntimeError: If device not available
    """

def get_bits(n: int) -> int
    """Generate n bits of entropy.
    
    Args:
        n: Number of bits to generate
        
    Returns:
        Integer containing at least n bits (may have extra MSBs)
        
    Raises:
        ValueError: If n <= 0
        RuntimeError: If device not available
    """

def get_exact_bits(n: int) -> int
    """Generate exactly n bits of entropy.
    
    Args:
        n: Number of bits to generate
        
    Returns:
        Integer containing exactly n bits (MSBs masked)
        
    Raises:
        ValueError: If n <= 0
        RuntimeError: If device not available
    """

def is_device_available() -> bool
    """Check if the device is available on the current system.
    
    Returns:
        True if device is present and accessible, False otherwise
    """

def random_int(min: int = 0, max: Optional[int] = None) -> int
    """Generate a cryptographically secure random integer.
    
    Args:
        min: Minimum value (inclusive), defaults to 0
        max: Maximum value (exclusive), if None uses full range
        
    Returns:
        Random integer in range [min, max)
        
    Raises:
        ValueError: If min >= max
    """

def close() -> None
    """Close and release any resources (device handles, connections).
    
    Safe to call multiple times. Should be called when done or use as context manager.
    """
```

### Context Manager Support

All modules should support context manager protocol:

```python
with bitbabbler_rng.open() as rng:
    data = rng.get_bytes(32)
```

## Module-Specific Details

### bitbabbler_rng

**Files to migrate from modules/bbpy/**:
- `bitbabbler.py` → `bitbabbler.py`
- `ftdi.py` → `ftdi.py`  
- `libusb-1.0.dll` → `libusb-1.0.dll`

**Key features**:
- Cross-platform libusb-1.0 detection (Windows project folder, Linux/macOS system)
- Optional XOR folding parameter (folds=0-4)
- USB device auto-detection (VID:PID fallback to string scan)
- MPSSE mode initialization

**Dependencies**: pyusb, libusb-1.0

### truerng

**Key features**:
- Serial port auto-detection (works on Windows/Linux/macOS)
- Heuristic port matching (description/manufacturer/product strings)
- Linux serial port reset fix (stty min 1)
- Proper DTR/flush handling

**Dependencies**: pyserial

### pseudo_rng

**Key features**:
- Zero external dependencies
- Uses Python's `secrets` module (CSPRNG)
- Always available fallback
- Fast and reliable

**Dependencies**: None (stdlib only)

## Implementation Order

1. **pseudo_rng** (easiest, no dependencies)
2. **truerng** (simple serial interface)
3. **bitbabbler_rng** (most complex, consolidate bbpy)

## Testing Approach

Each module should have:
- Unit tests for all public methods
- Device availability tests
- Error handling tests
- Integration tests (if hardware available)

Example test structure:
```python
def test_get_bytes():
    if not module.is_device_available():
        pytest.skip("Device not available")
    data = module.get_bytes(32)
    assert len(data) == 32
    assert isinstance(data, bytes)

def test_get_exact_bits():
    if not module.is_device_available():
        pytest.skip("Device not available")
    # Test that we get exactly the requested bits
    for n in [1, 7, 8, 15, 16, 31, 32, 63, 64]:
        val = module.get_exact_bits(n)
        assert val.bit_length() <= n
        assert val >= 0
```

## Usage Example

```python
# Try hardware RNGs first, fallback to pseudo
try:
    import bitbabbler_rng as rng
    if not rng.is_device_available():
        raise RuntimeError("BitBabbler not found")
except RuntimeError:
    try:
        import truerng as rng
        if not rng.is_device_available():
            raise RuntimeError("TrueRNG not found")
    except RuntimeError:
        import pseudo_rng as rng

# Use the RNG
with rng:
    key = rng.get_bytes(32)
    nonce = rng.get_exact_bits(96)
```

## Notes

- Keep dependencies minimal and explicit
- Handle cross-platform differences gracefully
- Provide clear error messages
- Support both imperative and context manager usage
- Document hardware requirements in README files
