import json
from channels.generic.websocket import  AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from . models import Chat, Message, CallSession
from django.contrib.auth.models import User

from .twilio_utils import get_access_token , get_call_twiml

class ChatRoomConsumer(AsyncWebsocketConsumer):   
    @database_sync_to_async
    def save_message(self, username, message):
        #get the sender 
        sender=User.objects.get(username=username)
        #get the chat
        chat_room_id= int(self.scope['url_route']['kwargs']['room_id'])
        chat = Chat.objects.get(pk=chat_room_id)
        #create new message and add a sender and content to it 
        new_message= Message()
        new_message.sender = sender
        new_message.content=message
        new_message.save()
        #add new message to current chat and save
        chat.messages.add(new_message)
        chat.save()
    

    async def connect(self):      
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = 'chat_%s' % self.room_id
        
        await self.channel_layer.group_add(
            self.room_group_name,  
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,  
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        await self.save_message(username, message)

        await self.channel_layer.group_send(
            self.room_group_name,  
            {
                'type':'chatroom_message',
                'message': message,
                'username': username,
            }
        )

        # Send immediate acknowledgment back to the sender
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))

        
    async def chatroom_message(self, event):
        message = event['message']
        username = event['username']
        await self.send(text_data=json.dumps({
            'message': message,
            'username':username,
        }))


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
    