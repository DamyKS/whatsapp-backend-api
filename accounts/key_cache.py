# Store decrypted keys temporarily in session or cache
from django.core.cache import cache

class UserKeyManager:
    @staticmethod
    def store_session_key(user_id, decrypted_key):
        # Store in cache with expiry
        cache_key = f"user_key_{user_id}"
        cache.set(cache_key, decrypted_key, timeout=3600)  # 1 hour expiry

    @staticmethod
    def get_session_key(user_id):
        cache_key = f"user_key_{user_id}"
        return cache.get(cache_key)

# # During login:
# def login_view(request):
#     if login_successful:
#         decrypted_key = decrypt_user_private_key(user, password, encrypted_data)
#         UserKeyManager.store_session_key(user.id, decrypted_key)

# # In send_message view:
# def send_message(request):
#     decrypted_key = UserKeyManager.get_session_key(request.user.id)
#     if not decrypted_key:
#         # Redirect to password re-entry