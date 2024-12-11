from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    """ a models to represent messsages """
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat_images/", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    delivered= models.BooleanField(default=False)
    read_by=  models.ManyToManyField(User, related_name="has_read", blank=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"  # Truncate for display
    class Meta:
        ordering = ["-timestamp"]  # Order by timestamp (newest first)

class Chat(models.Model):
    """A model to hold all messages in a chat"""
    messages = models.ManyToManyField(Message, related_name="messages", blank=True)
    participants = models.ManyToManyField(User, related_name="participates_in")

    last_message_timestamp = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
       # Update last_message_timestamp when a new message is added
       if self.pk:
           latest_message = self.messages.first()
           if latest_message:
               self.last_message_timestamp = latest_message.timestamp
       super().save(*args, **kwargs)

    def __str__(self):
        chat_number = str(self.pk)  # Convert primary key to string
        return f"Chat {chat_number}"
    

class CallSession(models.Model):
    """
    Represents a call session between users
    """
    CALL_TYPES = (
        ('voice', 'Voice Call'),
        ('video', 'Video Call')
    )
    
    CALL_STATUSES = (
        ('initiated', 'Initiated'),
        ('connecting', 'Connecting'),
        ('active', 'Active'),
        ('ended', 'Ended')
    )
    
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    initiator = models.ForeignKey(User, related_name='initiated_calls', on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name='call_sessions')
    
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=20, choices=CALL_STATUSES, default='initiated')
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    duration = models.DurationField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.initiator.username}'s {self.call_type} call"