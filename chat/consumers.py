import json
from channels.generic.websocket import  AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from . models import Chat, Message, CallSession
from django.contrib.auth.models import User

from .twilio_utils import get_access_token , get_call_twiml




from nacl.public import Box, PrivateKey, PublicKey
from nacl.secret import SecretBox
import nacl.utils
from base64 import b64encode
from . models import Chat, Message, MessageKey
from accounts.models import UserKey
from accounts.key_cache import UserKeyManager

class ChatRoomConsumer(AsyncWebsocketConsumer):
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
            recipient= User.objects.get(id=user_id)
            MessageKey.objects.create(
                message=new_message,
                sender=sender,
                encrypted_message_key=encrypted_key,
                recipient=recipient
            )
            
        # Add message to chat and save to update last_message_timestamp
        chat.messages.add(new_message)
        chat.save()  # This will trigger the custom save method to update last_message_timestamp
        
        return str(new_message.message_id)  # Return UUID as string

    # async def connect(self):
    #     self.room_id = self.scope['url_route']['kwargs']['room_id']
    #     self.room_group_name = f'chat_{self.room_id}'
        
    #     await self.channel_layer.group_add(
    #         self.room_group_name,
    #         self.channel_name
    #     )
    #     await self.accept()
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Check if user is authenticated
        self.user = self.scope.get('user')
        if not self.user or self.user.is_anonymous:
            # Handle unauthenticated user
            await self.close()
            return
            
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
        decrypted_pri_key= UserKeyManager.get_session_key(sender_id)
        print(len(decrypted_pri_key))
        print("sender_private_key :  ",decrypted_pri_key)
        sender_private_key = PrivateKey(decrypted_pri_key)
        for participant_id in participants:
            # Get participant's public key
            participant_keys = await self.get_user_keys(participant_id)
            recipient_public_key = PublicKey(participant_keys['public_key'])
            #print("recipient public key:  ",recipient_public_key)
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
        
        print( 'encrypted_keys: ', {
                    str(k): b64encode(v).decode() 
                    for k, v in encrypted_keys.items()
                })
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

    # async def chat_message(self, event):
    #     # Send encrypted message to WebSocket
    #     user_id = self.scope['user'].id
    #     await self.send(text_data=json.dumps({
    #         'message_id': event['message_id'],
    #         'sender_id': event['sender_id'],
    #         'encrypted_content': event['encrypted_content'],
    #         'encrypted_key': event['encrypted_keys'].get(str(user_id))
    #     }))
    #     #
    async def chat_message(self, event):
        try:
            # Get user ID safely
            user_id = self.scope.get('user', {}).id if self.scope.get('user') else None
            
            if user_id:
                await self.send(text_data=json.dumps({
                    'message_id': event['message_id'],
                    'sender_id': event['sender_id'],
                    'encrypted_content': event['encrypted_content'],
                    'encrypted_key': event['encrypted_keys'].get(str(user_id))
                }))
            else:
                # Handle case where user is not authenticated
                await self.send(text_data=json.dumps({
                    'error': 'Authentication required'
                }))
        except Exception as e:
            # Handle any errors gracefully
            await self.send(text_data=json.dumps({
                'error': 'Error processing message'
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

class CallSignalingConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def create_call_session(self, data):
        current_initiator = User.objects.get(username=data['initiator'])
        counterpart = User.objects.get(username=data['participant'][1])

        call_session = CallSession()
        call_session.initiator = current_initiator
        call_session.call_type = data['call_type']
        call_session.status = data['status']
        call_session.start_time = data['start_time']
        call_session.save()  # Save first to get an ID

        # Now add participants
        call_session.participants.add(current_initiator, counterpart)

        return call_session
    
    @database_sync_to_async
    def handle_call_create(self, data):
        
            user1= data['current_sender']
            user2 = data['recipient_username']
            call_id = data['call_id']
            call_session_name =f'{ user1}_{user2}_{call_id}'

            user1_access_token = get_access_token(user1)
            user2_access_token = get_access_token(user2)

            user1_call_twiml= get_call_twiml(user1,call_session_name )
            user2_call_twiml= get_call_twiml(user2,call_session_name )

            return {
                'user1':user1,
                'user2':user2,
                'user1_access_token' : user1_access_token,
                'user2_access_token': user2_access_token,
                'user1_call_twiml':user1_call_twiml,
                'user2_call_twiml': user2_call_twiml
            }
        
    async def connect(self):
        # Join user-specific room for call signaling
        self.user_name = self.scope['url_route']['kwargs']['user_name']
        self.room_name = f"call_signaling_{self.user_name}"
        
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Handle incoming WebRTC signaling messages
        """
        data = json.loads(text_data)
        signal_type = data.get('type')
        
        # Dispatch based on signal type
        if signal_type == 'start_call':
            await self.handle_call_start(data)
        elif signal_type in ['is_online', 'answer']:
            await self.forward_signaling(data)
    
    async def handle_call_start(self, data):
        # Create CallSession
        call_session = await self.create_call_session(data)
        
        # Broadcast call invitation to participants
        await self.channel_layer.group_send(
            f"call_signaling_{data['recipient_username']}",
            {
                'type': 'call_invitation',
                'call_id': str(call_session.id),
                'initiator': self.user_name,
                'call_type': data['call_type']
            }
        )
    
    async def forward_signaling(self, data):
        if data['type'] == 'answer':
            await self.channel_layer.group_send(
                f"call_signaling_{data['recipient_username']}",
                {
                    'type': 'receive_signal',
                    'signal': data
                }
            )

            created_call_detail = await self.handle_call_create(data)
            await self.channel_layer.group_send(
                f"call_signaling_{created_call_detail['user1']}",
                {    
                    'type': 'call_detail',
                    'user':created_call_detail['user1'],
                    'user_access_token' : created_call_detail['user1_access_token'],
                    'user_call_twiml':created_call_detail['user1_call_twiml'],
                }
        
            )

            await self.channel_layer.group_send(
                f"call_signaling_{created_call_detail['user2']}",
                {    
                    'type': 'call_detail',
                    'user':created_call_detail['user2'],
                    'user_access_token' : created_call_detail['user2_access_token'] ,
                    'user_call_twiml':created_call_detail['user2_call_twiml']
                }
        
            )
    
        # Forward WebRTC signaling messages
        else:
            await self.channel_layer.group_send(
                f"call_signaling_{data['recipient_username']}",
                {
                    'type': 'receive_signal',
                    'signal': data
                }
            )
    
    # Signaling message handlers
    async def call_invitation(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_invitation',
            **event
        }))
    
    async def receive_signal(self, event):
        await self.send(text_data=json.dumps(event['signal']))

    async def call_detail(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_detail',
            **event
        }))
    