from cryptography.fernet import Fernet

key = Fernet.generate_key()
fernet = Fernet(key)

#encryption
def encrypt_file(filepath):
    with open(filepath, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(filepath, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)