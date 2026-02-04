from bitbabbler_rng import is_device_available, get_bytes, get_bits, get_exact_bits
import time

t0 = time.time()
# Check if device is connected
if is_device_available():
    
    # Generate 1024 bytes of raw entropy
    raw = get_bytes(2)
    print(raw)
    
    # Generate with XOR folding (whitening)
    # folds=0: raw, folds=1-4: progressively whitened
    folded = get_bytes(2, folds=2)
    print(folded)
    
    # Generate 1000 bits for statistical analysis
    data = get_exact_bits(80, folds=1)  # Exactly 1000 bits with whitening
    ones = sum(bin(b).count('1') for b in data)
    zeros = len(data) * 8 - ones
    print("data", data)
    print(ones)
    print(zeros)
    
else:
    print("BitBabbler not found")
    
t1 = time.time() - t0
print(t1)