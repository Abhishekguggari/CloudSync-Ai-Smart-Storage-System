import os
from cryptography.fernet import Fernet

KEY_FILE = 'secret.key'

# Load or generate a single persistent encryption key for the system
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as kf:
        key = kf.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as kf:
        kf.write(key)

fernet = Fernet(key)

# ==========================================
# SECURE FILE ENCRYPTION (IN-PLACE)
# ==========================================
def encrypt_file(filepath):
    """Encrypts a file directly on the disk using AES-128 Fernet."""
    if not os.path.exists(filepath):
        return
        
    with open(filepath, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(filepath, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

# ==========================================
# SECURE FILE DECRYPTION (STREAM BACK)
# ==========================================
def decrypt_file(filepath):
    """Decrypts an encrypted file and returns raw bytes safely."""
    if not os.path.exists(filepath):
        return b""
        
    with open(filepath, 'rb') as file:
        encrypted = file.read()

    try:
        decrypted = fernet.decrypt(encrypted)
        return decrypted
    except Exception:
        # Fallback safeguard: returns original data if it wasn't encrypted
        return encrypted