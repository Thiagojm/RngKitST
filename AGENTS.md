# AGENTS.md - Coding Guidelines for RngKit

## Project Overview
RngKit is a Streamlit-based web application for collecting and analyzing data from True Random Number Generators (TRNGs) and Pseudo-Random Number Generators (PRNGs). It supports hardware devices like BitBabbler and TrueRNG.

## Build & Run Commands

```bash
# Run the Streamlit application
uv run streamlit run main_streamlit.py

# Install dependencies
pip install -r requirements_streamlit.txt
# OR using uv
uv pip install -r requirements_streamlit.txt

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_services.py

# Run a specific test function
pytest tests/test_services.py::test_filenames_roundtrip

# Run randomness tests from device
python -m tests.randomness_tests --bytes 1024

# Run with verbose output
pytest tests/ -v
```

## Code Style Guidelines

### Import Order
1. Standard library imports (os, sys, time, typing, etc.)
2. External library imports (streamlit, pandas, numpy, plotly, serial)
3. Internal imports (src/rngkit modules)

Use sys.path.append() before internal imports:
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from rngkit.services import filenames  # type: ignore
```

### Type Hints
- Use type hints for function parameters and return values
- Import from typing: `Optional`, `Tuple`, `List`, `Dict`, etc.
- Use `# type: ignore` for imports that may fail (optional dependencies)

### Naming Conventions
- Functions/variables: `snake_case` (e.g., `detect_device`, `sample_size`)
- Classes: `PascalCase` (e.g., `BitBabbler`, `TrueRngReader`)
- Constants: `UPPER_CASE` (e.g., `LIVE_MAX_POINTS`, `DATA_DIR`)
- Private functions: `_leading_underscore` (e.g., `_get_cached_device`)

### Docstrings
Use descriptive docstrings with Args/Returns sections:
```python
def parse_bits(name: str) -> int:
    """Extract sample size in bits from filename.
    
    Args:
        name: Filename stem (e.g., "20201011T142208_bitb_s2048_i1_f0")
        
    Returns:
        Sample size as integer
        
    Raises:
        ValueError: If bits pattern not found in name
    """
```

### Error Handling
- Use try/except blocks for device operations and external dependencies
- Provide fallback behavior (e.g., return None, False, or default values)
- Log errors appropriately; avoid exposing sensitive details
- Use specific exception types when possible
- Clean up resources in finally blocks (close devices, files, etc.)

Example:
```python
def detect() -> bool:
    """Detect if device is available."""
    try:
        return _get() is not None
    except Exception:
        return False  # Graceful fallback
```

### Session State Management
When using Streamlit, initialize session state variables with defaults:
```python
def init_session_state():
    defaults = {
        'collecting': False,
        'sample_size': 2048,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
```

### File Naming Convention
Capture files follow pattern: `YYYYMMDDTHHMMSS_{device}_s{bits}_i{interval}[_f{folds}]`
- Use `filenames.format_capture_name()` to generate
- Use `filenames.parse_bits()` and `parse_interval()` to parse

## Testing Guidelines

- Tests are in `tests/` directory using pytest
- Test files named `test_*.py`
- Use pytest fixtures (e.g., `tmp_path` for temporary files)
- Mock hardware dependencies when possible
- Device-specific tests in dedicated files (e.g., `test_bitbabbler.py`)

## Project Structure

```
main_streamlit.py      # Streamlit entry point
test_browser_performance.py  # Performance testing
src/rngkit/
  devices/             # Hardware interfaces (bitbabbler.py, truerng.py, pseudo.py)
  services/            # Business logic (filenames.py, storage.py, utils.py)
tests/                 # Test files
modules/bbpy/          # External BitBabbler interface module
data/                  # Output directory (created at runtime)
```

## Dependencies

Core dependencies (from pyproject.toml):
- streamlit (UI framework)
- pandas, numpy (data processing)
- plotly (visualization)
- pyserial (TrueRNG communication)
- pyusb (BitBabbler USB interface)
- xlsxwriter (Excel report generation)
- bitstring (binary data handling)

## Hardware Considerations

- Device detection should be non-blocking and cacheable
- Always provide fallback to pseudo-RNG for testing without hardware
- Handle device disconnection gracefully
- Reset cached device handles on errors
