import os
from cryptography.fernet import Fernet

KEY_FILE = 'secret.key'

# Load or generate persistent encryption key
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as kf:
        key = kf.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as kf:
        kf.write(key)

fernet = Fernet(key)

# encryption
def encrypt_file(filepath):
    with open(filepath, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(filepath, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

# decryption
def decrypt_file(filepath):
    with open(filepath, 'rb') as file:
        encrypted = file.read()

    try:
        decrypted = fernet.decrypt(encrypted)
        return decrypted
    except Exception as e:
        # If already decrypted or not encrypted
        return encrypted
