import base64
import json

def flip_admin_bit(original_token):
    decoded = base64.b64decode(original_token)
    nonce = decoded[:8]
    ciphertext = bytearray(decoded[8:])

    # We don't know the keystream, but we can manipulate ciphertext directly
    # Let's find where `"admin": 0` appears in the plaintext by decrypting normally first (you did see this printed in debug)
    # But since we can't decrypt, we'll do blind flipping based on known structure

    # Assume structure like:
    # {"nickname":"bob","password":"mypassword","admin":0}
    # Let's search for the value `0` near `"admin":`

    # Find position of byte `0x30` (ASCII for '0') at the correct offset
    # For now, scan all and flip any `0` to `1`
    for i in range(len(ciphertext)):
        if ciphertext[i] == ord('0'):
            # Flip 0 to 1 by XORing with (ord('0') ^ ord('1'))
            ciphertext[i] ^= ord('0') ^ ord('1')
            break

    forged_token = base64.b64encode(nonce + ciphertext).decode()
    return forged_token

# Example usage
your_token = input("Paste your user token: ").strip()
admin_token = flip_admin_bit(your_token)
print(f"[+] Forged admin token:\n{admin_token}")
