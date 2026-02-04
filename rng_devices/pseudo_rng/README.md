# Pseudo RNG Module

Software-based cryptographically secure random number generator using Python's `secrets` module. Zero dependencies, always available.

## Installation

No external dependencies required. Uses only Python standard library.

## Usage

```python
from pseudo_rng import get_bytes, get_bits, get_exact_bits

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
```

## API Reference

### `is_device_available() -> bool`
Always returns `True`.

### `get_bytes(n_bytes: int) -> bytes`
Generate exactly `n_bytes` of random data.

### `get_bits(n_bits: int) -> bytes`
Generate at least `n_bits` of random data. Returns `ceil(n_bits/8)` bytes (may have extra bits).

### `get_exact_bits(n_bits: int) -> bytes`
Generate exactly `n_bits` of random data. Returns `n_bits/8` bytes.

**Note:** `n_bits` must be divisible by 8. Raises `ValueError` if not.

### `random_int(min: int = 0, max: Optional[int] = None) -> int`
Generate random integer in range `[min, max)`.

### `close() -> None`
No-op for consistency with hardware modules.

## When to Use

- As a fallback when hardware RNGs are unavailable
- For testing and development
- When cryptographic security is needed but hardware RNG is not practical
