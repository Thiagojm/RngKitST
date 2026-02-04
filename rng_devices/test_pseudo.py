from pseudo_rng import get_bytes, get_bits, get_exact_bits

# Generate 32 random bytes (256 bits)
data1 = get_bytes(32)
print(data1)

# Generate 100 random bits (returns 13 bytes, 104 bits total)
data2 = get_bits(100)
print(data2)

# Generate exactly 256 random bits (32 bytes)
# Note: n_bits must be divisible by 8
data3 = get_exact_bits(96)
print(data3)

# Count ones for statistical analysis
ones = sum(bin(b).count('1') for b in data3)
zeros = len(data3) * 8 - ones
print(ones)
print(zeros)