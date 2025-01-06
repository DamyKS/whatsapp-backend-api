from django.contrib.auth import get_user_model 
from rest_framework import serializers
from .models import Chat, Message,MessageKey,  CallSession

from nacl.public import Box, PrivateKey, PublicKey
from nacl.secret import SecretBox
from accounts.models import UserKey
from accounts.key_cache import UserKeyManager

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

class DecryptedMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    read_by = UserSerializer(many=True)
    content= serializers.SerializerMethodField()
    class Meta:
        #'image'
        fields = ('id', 'sender', 'content','timestamp', 'delivered','read_by')
        model = Message
        #read_only_fields = ['id', 'timestamp', 'read_by']
    def get_sender(self,obj):
        return obj.sender.username
    def get_content(self, obj):
        #get curent user
        current_user=self.context['request'].user
        #get sender from msg obj
        sender=obj.sender
        #get msg key 
        message_keys= MessageKey.objects.filter(message=obj).all()
        for potential_msg_key in message_keys:
            if potential_msg_key.recipient==current_user:
                message_key=potential_msg_key
        #get encrypted_msg_key from msg key
        encrypted_message_key= message_key.encrypted_message_key
        #get current user private key from cache
        current_user_private_key= PrivateKey(UserKeyManager.get_session_key(current_user.id))
        #get sender's userkey and get their public key 
        sender_public_key= PublicKey( UserKey.objects.get(user=sender).public_key)
        #create Box(current_user_pri, sender_pub )
        print("pti:  ", current_user_private_key)
        print("pub: ", sender_public_key)
        box= Box(current_user_private_key,sender_public_key )
        #use Box to decript encrypted_msg_key = decrypted_msg_key
        decrypted_message_key= box.decrypt(encrypted_message_key)
        #use decrypted_msg_key to create SecretBox 
        secret_box= SecretBox(decrypted_message_key)
        #use SecretBox to decrypted encrypted_msg_content = content
        decrypted_content=secret_box.decrypt(obj.encrypted_content)
        #retirn content
        print("TEST TEST TEST")
        return decrypted_content.decode('utf-8') 
    
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