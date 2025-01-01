from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.pwhash import argon2id
import nacl.utils

def generate_user_keys():
    """Generate a new key pair for a user."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    return private_key.encode(), public_key.encode()

def derive_master_key(password, salt):
    """Derives a master key from a password and salt using argon2id."""
    key = argon2id.kdf(
        size=SecretBox.KEY_SIZE,
        password=password.encode('utf-8'),
        salt=salt,
        opslimit=argon2id.OPSLIMIT_MODERATE,
        memlimit=argon2id.MEMLIMIT_MODERATE
    )
    return key

def encrypt_private_key(private_key, master_key):
    """
    Encrypts a private key using a master key.
    Returns the encrypted key and nonce separately to avoid confusion.
    """
    box = SecretBox(master_key)
    nonce = nacl.utils.random(SecretBox.NONCE_SIZE)
    # Don't return the combined ciphertext, instead separate the nonce and encrypted data
    encrypted = box.encrypt(private_key, nonce)
    return {
        'nonce': nonce,
        'encrypted_key': encrypted.ciphertext  # Only return the ciphertext portion
    }

def decrypt_private_key(encrypted_key, nonce, master_key):
    """
    Decrypts a private key using a master key.
    Now expects separate ciphertext and nonce.
    """
    box = SecretBox(master_key)
    try:
        return box.decrypt(encrypted_key, nonce)
    except nacl.exceptions.CryptoError as e:
        # Log the error details
        print(f"Decryption failed: {str(e)}")
        print(f"Encrypted key length: {len(encrypted_key)}")
        print(f"Nonce length: {len(nonce)}")
        print(f"Master key length: {len(master_key)}")
        raise