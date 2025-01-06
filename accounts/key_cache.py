from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class UserKeyManager:
    KEY_PREFIX = "user_key_"
    DEFAULT_TIMEOUT = 3600*24  # 24 hour
    
    @classmethod
    def store_session_key(cls, user_id, decrypted_key, timeout=None):
        """Store decrypted key in cache with optional custom timeout"""
        cache_key = f"{cls.KEY_PREFIX}{user_id}"
        timeout = timeout or cls.DEFAULT_TIMEOUT
        
        try:
            cache.set(cache_key, decrypted_key, timeout=timeout)
            logger.debug(f"Stored session key for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store session key for user {user_id}: {str(e)}")
            return False
    
    @classmethod
    def get_session_key(cls, user_id):
        """Get decrypted key from cache with logging"""
        cache_key = f"{cls.KEY_PREFIX}{user_id}"
        key = cache.get(cache_key)
        
        if key is None:
            logger.warning(f"No session key found for user {user_id}")
        
        return key
    
    @classmethod
    def clear_session_key(cls, user_id):
        """Clear key from cache (useful for logout)"""
        cache_key = f"{cls.KEY_PREFIX}{user_id}"
        cache.delete(cache_key)
        logger.debug(f"Cleared session key for user {user_id}")
    
    @classmethod
    def refresh_session_key(cls, user_id):
        """Refresh the timeout for an existing key"""
        key = cls.get_session_key(user_id)
        if key:
            return cls.store_session_key(user_id, key)
        return False