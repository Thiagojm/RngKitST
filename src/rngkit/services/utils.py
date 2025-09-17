import os


def ensure_data_dir() -> str:
    """Return path to data directory and ensure it exists.

    Defaults to data/raw under the project root. Override with RNGKIT_DATA_DIR.
    
    Returns:
        Path to data directory (created if it doesn't exist)
        
    Raises:
        OSError: If directory cannot be created
    """
    default_dir = os.path.join(os.getcwd(), "data", "raw")
    base = os.environ.get("RNGKIT_DATA_DIR", default_dir)
    os.makedirs(base, exist_ok=True)
    return base


def is_valid_params(bit_count: int, time_count: int) -> bool:
    """Validate RNG collection parameters.
    
    Args:
        bit_count: Number of bits per sample (must be positive and divisible by 8)
        time_count: Sample interval in seconds (must be >= 1)
        
    Returns:
        True if parameters are valid, False otherwise
    """
    if bit_count <= 0 or (bit_count % 8) != 0:
        return False
    if time_count < 1:
        return False
    return True


