from des import DesKey

def expand_key(val):
    k = val | (val << 14) | (val << 28) | (val << 42)
    return DesKey(bytearray.fromhex("{v:016X}".format(v=k)))

known_pt = b"a short message!"
known_ct = bytes.fromhex("d8bf8dc0054d525a3d7fcedb6912cc43")
captured_ct = bytes.fromhex("26d22089fd6b1c9d5a33ae252bd9922a48d2a7e2d5868daf4d847d0c8eff3529e308ae7beb33015d")

# Step 1: Create a dictionary to store intermediate values
intermediate_values = {}

# Step 2: Encrypt the known plaintext using all possible 14-bit keys
for key1 in range(2**14):
    k1 = expand_key(key1)
    ct1 = k1.encrypt(known_pt)
    intermediate_values[ct1] = key1

# Step 3: Decrypt the known ciphertext using all possible 14-bit keys
for key2 in range(2**14):
    k2 = expand_key(key2)
    pt2 = k2.decrypt(known_ct)

    # Check if the decrypted value matches any intermediate value
    if pt2 in intermediate_values:
        k1 = expand_key(intermediate_values[pt2])
        break

# Step 4: Decrypt the captured ciphertext using the found keys
decrypted_ct1 = k1.decrypt(k2.decrypt(captured_ct))

# Step 5: Convert the decrypted bytes to an ASCII string
decrypted_message = decrypted_ct1.decode('ascii')
print(decrypted_message)