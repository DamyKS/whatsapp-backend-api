import asyncio
import json
import websockets

class WebSocketChatTester:
    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.connection = None

    async def connect_websocket(self):
        try:
            self.connection = await websockets.connect(self.websocket_url)
            print(f"Connected to {self.websocket_url}")
            return self.connection
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            raise

    async def send_message(self, message, username):
        payload = json.dumps({
            'message': message,
            'username': username
        })
        await self.connection.send(payload)
        print(f"Sent message: {payload}")

    async def receive_message(self, timeout=15):
        try:
            message = await asyncio.wait_for(self.connection.recv(), timeout=timeout)
            print(f"Received message: {message}")
            return json.loads(message)
        except asyncio.TimeoutError:
            print("Receive timeout")
            return None

    async def close(self):
        if self.connection:
            await self.connection.close()
            print("WebSocket connection closed")

async def test_websocket_chat():
    WEBSOCKET_URL = 'ws://localhost:8000/ws/chat/1/'
    
    # Create tester
    tester = WebSocketChatTester(websocket_url=WEBSOCKET_URL)
    
    try:
        # Connect to WebSocket
        await tester.connect_websocket()
        
        # Send a test message
        await tester.send_message('Hello, WebSocket!', 'admin')
        
        # Wait for response
        response = await tester.receive_message()
        
        # Assertions
        assert response is not None, "No response received"
        assert 'message' in response, "Response missing 'message' key"
        assert 'username' in response, "Response missing 'username' key"
        assert response['message'] == 'Hello, WebSocket!', "Message content mismatch"
        assert response['username'] == 'admin', "Username mismatch"
        
        print("WebSocket test passed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        await tester.close()

def run_websocket_chat_test():
    asyncio.run(test_websocket_chat())

if __name__ == '__main__':
    run_websocket_chat_test()