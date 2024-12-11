from django.contrib.auth import get_user_model 
from rest_framework import serializers
from .models import Chat, Message, CallSession

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username')
        #read_only_fields = ['id', 'username']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    read_by = UserSerializer(many=True)
    class Meta:
        fields = ('id', 'sender', 'content','image','timestamp', 'delivered','read_by')
        model = Message
        #read_only_fields = ['id', 'timestamp', 'read_by']

class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    last_message = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'messages', 'participants','last_message', 'unread_messages_count')

    def get_last_message(self, obj):
        # Get the most recent message in the chat
        last_message = obj.messages.first()
        return {
            'id': last_message.id if last_message else None,
            'content': last_message.content if last_message else '',
            'sender': last_message.sender.username if last_message else '',
            'timestamp': last_message.timestamp if last_message else None
        }
    
    def get_unread_messages_count(self, obj):
        user = self.context['request'].user
        
        # If no messages in the chat
        if not obj.messages.exists():
            return 0
        last_read_message = obj.messages.filter(read_by=user).first()
        print(last_read_message)
        
        if last_read_message is None:
            return obj.messages.count()
        
        return obj.messages.filter(timestamp__gt=last_read_message.timestamp).count()
            
class CallSessionSerializer(serializers.ModelSerializer):
    initiator = serializers.StringRelatedField()
    participants = serializers.StringRelatedField(many=True)
    
    class Meta:
        model = CallSession
        fields = ['id', 'initiator', 'participants', 'call_type', 'status', 'start_time', 'end_time']
        #read_only_fields = ['id', 'start_time']