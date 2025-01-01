import os
import nacl.secret
import nacl.utils
from nacl.pwhash import scrypt
from django.contrib.auth.hashers import check_password # For password verification

def derive_master_key(password, salt):
    """Derives a master key from a password and salt using scrypt."""
    kdf_key = scrypt(
        password.encode('utf-8'),
        salt=salt,
        N=nacl.pwhash.scrypt.OPSLIMIT_INTERACTIVE,  # Adjust as needed
        r=8,
        p=1,
        dkLen=nacl.secret.SecretBox.KEY_SIZE,
    )
    return kdf_key

def encrypt_private_key(private_key, master_key):
    """Encrypts a private key using a master key."""
    box = nacl.secret.SecretBox(master_key)
    nonce = nacl.utils.random(box.NONCE_SIZE)
    encrypted_key = box.encrypt(private_key, nonce)
    return {
        'nonce': nonce.hex(),
        'encrypted_key': encrypted_key.hex(),
    }

def decrypt_private_key(encrypted_data, master_key):
    try:
        nonce = bytes.fromhex(encrypted_data['nonce'])
        encrypted_key = bytes.fromhex(encrypted_data['encrypted_key'])
        box = nacl.secret.SecretBox(master_key)
        decrypted_key = box.decrypt(encrypted_key, nonce)
        return decrypted_key
    except (nacl.exceptions.CryptoError, ValueError, KeyError):
        return None

# In your UserKey model:
from django.db import models
from django.contrib.auth.models import User

class UserKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='keys')
    master_key_salt = models.BinaryField(null=True, blank=True)
    encrypted_private_key = models.TextField(null=True, blank=True)
    key_nonce = models.CharField(max_length=64, blank = True, null = True)

# During User Registration:
def register_user(request):
    # ... (User registration logic)
    if form.is_valid():
        user = form.save()
        password = form.cleaned_data['password'] # Get the password from the form
        salt = nacl.utils.random(nacl.pwhash.scrypt.SALTBYTES)
        master_key = derive_master_key(password, salt)
        UserKey.objects.create(user=user, master_key_salt=salt)
        # ...

# When encrypting the private key (in a separate request):
def encrypt_user_private_key(request):
    if request.method == 'POST':
        user = request.user  # Get the authenticated user
        user_key = UserKey.objects.get(user=user)
        password = request.POST.get('password') # Get the password from user
        if check_password(password, user.password): # Verify the password
            salt = user_key.master_key_salt
            master_key = derive_master_key(password, salt)
            private_key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
            encrypted_data = encrypt_private_key(private_key, master_key)
            user_key.encrypted_private_key = encrypted_data['encrypted_key']
            user_key.key_nonce = encrypted_data['nonce']
            user_key.save()
            # ...

# When decrypting the private key:
def decrypt_user_private_key(user, password, encrypted_data):
    user_key = UserKey.objects.get(user=user)
    if check_password(password, user.password):
        salt = user_key.master_key_salt
        master_key = derive_master_key(password, salt)
        decrypted_key = decrypt_private_key(encrypted_data, master_key)
        return decrypted_key
    return None