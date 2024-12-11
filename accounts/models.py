from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """
    represent a user profile 
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True
    )
    cover_picture=models.ImageField(
        upload_to="cover_pictures/",
        blank=True,
        null=True
    )
    phone_number = models.CharField(
        max_length=15, 
        unique=True, 
        blank=True, 
        null=True
    )
    online_status = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    followers=models.ManyToManyField(User, related_name="follows")
    def __str__(self):
        return self.owner.username
   