from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserKey
from .encryption import derive_master_key, generate_user_keys, encrypt_private_key
import nacl.utils

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_key(sender, instance, created, **kwargs):
    pass
   