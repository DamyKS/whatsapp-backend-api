import asyncio
import json
import websockets
import uuid
from datetime import datetime

class WebRTCCallSignalingTester:
    def __init__(self, websocket_url, username):
        self.websocket_url = websocket_url
        self.username = username
        self.connection = None
    
    async def connect_websocket(self):
        try:
            # Append username to WebSocket URL
            full_url = f"{self.websocket_url}{self.username}/"
            self.connection = await websockets.connect(full_url)
            print(f"{self.username} connected to {full_url}")
            return self.connection
        except Exception as e:
            print(f"WebSocket connection error for {self.username}: {e}")
            raise
    
    async def send_message(self, message_type, data=None):
        """
        Send a WebRTC signaling message
        
        :param message_type: Type of signal (start_call, is_online, answer, etc.)
        :param data: Additional data for the message
        """
        if data is None:
            data = {}
        
        payload = {
            'type': message_type,
            **data
        }
        
        payload_json = json.dumps(payload)
        await self.connection.send(payload_json)
        print(f"{self.username} sent message: {payload_json}")
    
    async def receive_message(self, timeout=20):
        """
        Receive a WebSocket message
        
        :param timeout: Timeout in seconds
        :return: Parsed JSON message or None
        """
        try:
            message = await asyncio.wait_for(self.connection.recv(), timeout=timeout)
            print(f"{self.username} received message: {message}")
            return json.loads(message)
        except asyncio.TimeoutError:
            print(f"{self.username} receive timeout")
            return None
    
    async def close(self):
        if self.connection:
            await self.connection.close()
            print(f"{self.username} WebSocket connection closed")

async def test_webrtc_call_signaling():
    """
    Comprehensive test for WebRTC call signaling workflow
    
    Workflow:
    1. User1 connects to WebSocket
    2. User2 connects to WebSocket
    3. User1 sends a call start request to User2
    4. User2 receives call invitation
    5. User2 sends is_online and answer signals
    6. User1 receives signals from User2
    7. Both users receive call details
    """
    WEBSOCKET_URL = 'ws://localhost:8000/ws/call/'
    
    # Create testers for two users
    user1 = WebRTCCallSignalingTester(WEBSOCKET_URL, 'admin')
    user2 = WebRTCCallSignalingTester(WEBSOCKET_URL, 'admin2')
    
    try:
        # Connect both users
        await user1.connect_websocket()
        await user2.connect_websocket()
        
        # Prepare call start data
        call_start_data = {
            'type': 'start_call',
            'initiator': 'admin',
            'recipient_username': 'admin2',
            'participant': ['admin', 'admin2'],
            'call_type': 'video',
            'status': 'initiated',
            'start_time': datetime.now().isoformat(),
            'call_id': str(uuid.uuid4())
        }
        
        # User1 sends call start request
        await user1.send_message('start_call', call_start_data)
        
        # User2 should receive call invitation
        user2_response = await user2.receive_message()
        assert user2_response is not None, "User2 did not receive call invitation"
        assert user2_response['type'] == 'call_invitation', "Incorrect message type"
        assert user2_response['initiator'] == 'admin', "Incorrect call initiator"
        
        # Get call_id
        call_id = user2_response['call_id']
        
        # User2 sends is_online and answer signals
        online_signal = {
            'type': 'is_online',
            'recipient_username': 'admin',
            'status': 'online'
        }
        answer_signal = {
            'type': 'answer',
            'recipient_username': 'admin',
            'current_sender':'admin2',
            'value': 'accept',
            'call_id': call_id
        }
        
        await user2.send_message('is_online', online_signal)
        await user2.send_message('answer', answer_signal)
        
        # User1 should receive signals from User2
        user1_online_signal = await user1.receive_message()
        user1_answer_signal = await user1.receive_message()
        
        assert user1_online_signal is not None, "User1 did not receive online signal"
        assert user1_answer_signal is not None, "User1 did not receive answer signal"
        
        # Both users should now receive call details
        user1_call_details = await user1.receive_message()
        user2_call_details = await user2.receive_message()
        
        assert user1_call_details is not None, "User1 did not receive call details"
        assert user2_call_details is not None, "User2 did not receive call details"
        
        # Verify call details contain necessary information
        assert user1_call_details['type'] == 'call_detail', "User1 call details have incorrect type"
        assert user2_call_details['type'] == 'call_detail', "User2 call details have incorrect type"
        assert 'access_token' in user1_call_details or 'user_access_token' in user1_call_details, "User1 call details missing access token"
        assert 'access_token' in user2_call_details or 'user_access_token' in user2_call_details, "User2 call details missing access token"
        
        print("WebRTC Call Signaling Test Passed Successfully!")
    
    except Exception as e:
        print(f"WebRTC Call Signaling Test Failed: {e}")
    
    finally:
        await user1.close()
        await user2.close()

def run_webrtc_call_signaling_test():
    asyncio.run(test_webrtc_call_signaling())

if __name__ == '__main__':
    run_webrtc_call_signaling_test()