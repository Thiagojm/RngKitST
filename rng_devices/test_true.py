from truerng import is_device_available, get_bytes, get_bits, get_exact_bits
import time

# Check if device is connected
if is_device_available():
    t0 = time.time()
    # Generate 32 random bytes (256 bits)
    data = get_bytes(32)
    print(data)
    
    # Generate 100 random bits (returns 13 bytes, 104 bits total)
    data1 = get_bits(100)
    print(data1)
    
    # Generate exactly 100 random bits (returns 13 bytes, extra bits zeroed)
    data2 = get_exact_bits(128)
    print(data2)
    
    # Count ones for statistical analysis
    ones = sum(bin(b).count('1') for b in data2)
    zeros = len(data2) * 8 - ones
    print(ones)
    print(zeros)
    t1 = time.time() - t0
    print(t1)
else:
    print("TrueRNG not found - check USB connection")