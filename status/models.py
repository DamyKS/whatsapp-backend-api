from django.db import models
from django.contrib.auth.models import User

class Status(models.Model):
    creator = models.ForeignKey(User, related_name='created', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    caption = models.TextField(blank=True)
    image= models.ImageField(upload_to="status_images/", blank=True)
    seen_by=  models.ManyToManyField(User, related_name="has_seen", blank=True)
    def __str__(self):
        return f"{self.creator.username}: {self.caption[:20]}"  # Truncate for display
    class Meta:
        ordering = ["-created_at"]  # Order by timestamp (newest first)