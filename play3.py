import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from nacl.public import Box, PrivateKey, PublicKey
from nacl.secret import SecretBox
import nacl.utils
from base64 import b64encode
from . models import Chat, Message, MessageKey, UserKey

class EncryptedChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_user_keys(self, user_id):
        """Retrieve public/private keys for a user"""
        user_key = UserKey.objects.get(user_id=user_id)
        return {
            'public_key': user_key.public_key,
            'encrypted_private_key': user_key.encrypted_private_key
        }
    
    @database_sync_to_async
    def get_chat_participants(self, chat_id):
        """Get all participants in a chat"""
        chat = Chat.objects.get(pk=chat_id)
        return [user.id for user in chat.participants.all()]
    
    @database_sync_to_async
    def get_user(self, user_id):
        """Get user object"""
        return User.objects.get(pk=user_id)
    
    @database_sync_to_async
    def save_encrypted_message(self, sender_id, encrypted_content, encrypted_keys):
        """Save encrypted message and its keys"""
        chat_id = int(self.scope['url_route']['kwargs']['room_id'])
        chat = Chat.objects.get(pk=chat_id)
        sender = User.objects.get(pk=sender_id)
        
        # Create new message with encrypted content
        new_message = Message.objects.create(
            sender=sender,
            encrypted_content=encrypted_content,
            delivered=True  # Mark as delivered since it's being saved
        )
        
        # Save encrypted message keys for each participant
        for user_id, encrypted_key in encrypted_keys.items():
            MessageKey.objects.create(
                message=new_message,
                sender=sender,
                encrypted_message_key=encrypted_key
            )
            
        # Add message to chat and save to update last_message_timestamp
        chat.messages.add(new_message)
        chat.save()  # This will trigger the custom save method to update last_message_timestamp
        
        return str(new_message.message_id)  # Return UUID as string

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        sender_id = data['sender_id']
        plaintext = data['message']
        
        # Generate random symmetric key for this message
        message_key = nacl.utils.random(SecretBox.KEY_SIZE)
        
        # Encrypt the actual message content
        box = SecretBox(message_key)
        encrypted_content = box.encrypt(plaintext.encode())
        
        # Get all chat participants
        participants = await self.get_chat_participants(self.room_id)
        
        # Encrypt message key for each participant
        encrypted_keys = {}
        sender_keys = await self.get_user_keys(sender_id)
        sender_private_key = PrivateKey(sender_keys['encrypted_private_key'])
        
        for participant_id in participants:
            # Get participant's public key
            participant_keys = await self.get_user_keys(participant_id)
            recipient_public_key = PublicKey(participant_keys['public_key'])
            
            # Encrypt message key
            encryption_box = Box(sender_private_key, recipient_public_key)
            encrypted_key = encryption_box.encrypt(message_key)
            encrypted_keys[participant_id] = encrypted_key  # Store as bytes
        
        # Save encrypted message and keys
        message_id = await self.save_encrypted_message(
            sender_id,
            encrypted_content,
            encrypted_keys
        )
        
        # Broadcast encrypted message to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'sender_id': sender_id,
                'encrypted_content': b64encode(encrypted_content).decode(),
                'encrypted_keys': {
                    str(k): b64encode(v).decode() 
                    for k, v in encrypted_keys.items()
                }
            }
        )

    async def chat_message(self, event):
        # Send encrypted message to WebSocket
        user_id = self.scope['user'].id
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'encrypted_content': event['encrypted_content'],
            'encrypted_key': event['encrypted_keys'].get(str(user_id))
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )