
<!DOCTYPE html>
<html>
<head>
{% load static %}
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">

<style>
.chat-input-container {
  display: flex;
  align-items: center;
  border: 1px solid #4c0ae6;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
}

#message-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  padding: 5px;
  height: 40px;  /* Initial height */
  min-height: 30px;  /* Set minimum height */
  overflow: hidden;  /* Remove scrollbar */
}

#send-message-button {
  background-color: #4752f7;
  color: #ffff;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

#send-message-button:hover {
  background-color: #444;
}

body {
  margin: 0 auto;
  max-width: 800px;
  padding: 0 20px;
}

.container {
  border: 2px solid #eff6ff;
  background-color: #bcbdf0;
  box-shadow: rgb(0 0 0 / 15%) 0px 3px 3px 2px;
  border-radius: 5px;
  padding: 10px;
  margin: 10px 0;
}

.darker {
  border-color: #a8a4a4;
  background-color: #7e73fa;
}

.container::after {
  content: "";
  clear: both;
  display: table;
}

.container img {
  float: left;
  max-width: 60px;
  width: 100%;
  margin-right: 20px;
  border-radius: 50%;
}

.container img.right {
  float: right;
  margin-left: 20px;
  margin-right:0;
}

.time-right {
  float: right;
  color: #fcf7f7;
}

.time-left {
  float: left;
  color: #251f1f;
}
#chat-container {
    
    overflow-y: auto;
    height: 400px;  
}
#chat_image {
  max-width: 300px;  
  margin-right: 20px;
  border-radius: 5%;
}

</style>
</head>
<body>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/tweetnacl/1.0.3/nacl.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/tweetnacl-util/0.15.1/nacl-util.min.js"></script> -->

  <script src="https://cdn.jsdelivr.net/npm/tweetnacl-util@0.15.0/nacl-util.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/tweetnacl@1.0.1/nacl.min.js"></script>
  <script>
    window.onload = function() {
        var chatContainer = document.getElementById("chat-container");  
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;  
        } 
        window.scrollTo(0, document.documentElement.scrollHeight);
    };
  </script>

<h2>Chat Room</h2>
<div id="chat-container">
  {% for message in messages %}
    {% if message.sender == request.user %}
      <div class="container darker">
        <img src="https://res.cloudinary.com/dqnwkkmzz/image/upload/v1/media/post-pic/default_dp.png" alt="Avatar" class="right" style="width:100%;">
        <p>{{message.sender}}</p>
        {% if message.image %}
          <img id="chat_image" src = "{{message.image.url}}">
        {% endif %}
        <p>{{message.content}}</p>
        <span class="time-left">11:01</span>
      </div>
    {%else %}
      <div class="container">
        <img src="https://res.cloudinary.com/dqnwkkmzz/image/upload/v1/media/post-pic/default_dp.png" alt="Avatar" style="width:100%;">
        <p>{{message.sender}}</p>
        {% if message.image %}
        <img id="chat_image" src = "{{message.image.url}}">
        {% endif %}
        <p>{{message.content}}</p>
        <span class="time-right">11:00</span>
      </div>
    {% endif %}
  {% endfor %}

</div> 
<div class="chat-input-container">
  <textarea id="message-input" placeholder="Type your message..." rows="1"></textarea>
  <button id="send-message-button">Send</button>
</div>

{{room_id|json_script:"room-id"}}
{{request.user.username|json_script:"user_username"}}
{{request.user.id|json_script:"user-id"}} 
{{user_private_key|json_script:"user_private_key"}} 

<script>
  const roomId = JSON.parse(document.getElementById('room-id').textContent);
  const user_username = JSON.parse(document.getElementById('user_username').textContent);
  const userId = JSON.parse(document.getElementById('user-id').textContent); // Add this to your template

  // Initialize WebSocket connection
  const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/' + roomId + '/'
  );

  // Handle sending messages
  document.querySelector("#send-message-button").onclick = async function(e) {
    const messageInputDOM = document.querySelector('#message-input');
    const message = messageInputDOM.value;
    
    if (message.trim()) {
      chatSocket.send(JSON.stringify({
        'message': message,
        'sender_id': userId
      }));
      messageInputDOM.value = "";
    }
  };
  const cryptoUtils = {
    // Box for public-key encryption/decryption
    openBox(encryptedMsgKey, senderPubKey, recipientPrivKey) {
        try {
            // First create the shared key
            const sharedKey = nacl.box.before(senderPubKey, recipientPrivKey);
            
            // Extract nonce (first 24 bytes) and ciphertext
            const nonce = encryptedMsgKey.slice(0, nacl.box.nonceLength);
            const ciphertext = encryptedMsgKey.slice(nacl.box.nonceLength);
            
            // Use the shared key to decrypt the message
            const decryptedMsgKey = nacl.box.open.after(ciphertext, nonce, sharedKey);
            
            if (!decryptedMsgKey) {
                throw new Error('Failed to decrypt message key');
            }
            
            return decryptedMsgKey;
        } catch (error) {
            console.error('Error in openBox:', error);
            throw error;
        }
    },
    
    // SecretBox for symmetric decryption
    openSecretBox(encryptedMsg, key) {
        try {
            // Extract nonce (first 24 bytes) and ciphertext
            const nonce = encryptedMsg.slice(0, nacl.secretbox.nonceLength);
            const ciphertext = encryptedMsg.slice(nacl.secretbox.nonceLength);
            
            const decrypted = nacl.secretbox.open(ciphertext, nonce, key);
            
            if (!decrypted) {
                throw new Error('Failed to decrypt message content');
            }
            
            return decrypted;
        } catch (error) {
            console.error('Error in openSecretBox:', error);
            throw error;
        }
    }
};

chatSocket.onmessage = async function(e) {
    const data = JSON.parse(e.data);
    console.log('Raw received data:', data);

    try {
        // Get user data
        const user_username = JSON.parse(document.getElementById('user_username').textContent);
        const user_private_key = JSON.parse(document.getElementById('user_private_key').textContent);
        const sender_public_key = data['sender_public_key'];
        const encrypted_message_key = data.encrypted_message_keys[user_username];
        const encrypted_content = data['encrypted_content'];

        console.log('Decoding keys:', {
            encrypted_message_key,
            sender_public_key,
            user_private_key,
            encrypted_content
        });

        // Input validation
        if (!encrypted_message_key || !sender_public_key || !user_private_key || !encrypted_content) {
            throw new Error('Missing required encryption fields');
        }

        // Decode Base64 inputs
        const decodedMsgKey = nacl.util.decodeBase64(encrypted_message_key);
        const decodedSenderPubKey = nacl.util.decodeBase64(sender_public_key);
        const decodedUserPrivKey = nacl.util.decodeBase64(user_private_key);
        const decodedContent = nacl.util.decodeBase64(encrypted_content);

        // Verify decoded data
        if (!decodedMsgKey || !decodedSenderPubKey || !decodedUserPrivKey || !decodedContent) {
            throw new Error('Invalid Base64 encoding');
        }

        // Decrypt message key
        const decrypted_msg_key = cryptoUtils.openBox(
            decodedMsgKey,
            decodedSenderPubKey,
            decodedUserPrivKey
        );
        console.log('Decrypted msg key length:', decrypted_msg_key.length);

        // Decrypt content
        const decrypted_content = cryptoUtils.openSecretBox(
            decodedContent,
            decrypted_msg_key
        );
        
        // Convert to text
        const messageText = nacl.util.encodeUTF8(decrypted_content);
        console.log('Decrypted message:', messageText);

        // Here you can handle the decrypted message (e.g., display it in UI)
        const senderId = data.sender_id;
      console.log("encrypted_message_keys:  ", data.encrypted_message_keys);
      
      // Create message element
      const messageElement = document.createElement('div');
      messageElement.classList.add('container');
      
      let new_message_string;
      // Check if this is from the current user
      if (senderId === userId) {
        messageElement.classList.add('darker');
        new_message_string = `
          <img src="https://res.cloudinary.com/dqnwkkmzz/image/upload/v1/media/post-pic/default_dp.png" alt="Avatar" class="right" style="width:100%;">
          <p>${user_username}</p>
          <p>${messageText}</p>
          <span class="time-right">${new Date().toLocaleTimeString()}</span>
        `;
      } else {
        new_message_string = `
          <img src="https://res.cloudinary.com/dqnwkkmzz/image/upload/v1/media/post-pic/default_dp.png" alt="Avatar" style="width:100%;">
          <p>${data.sender_username || 'User'}</p>
          <p>${messageText}</p>
          <span class="time-right">${new Date().toLocaleTimeString()}</span>
        `;
      }
      
      messageElement.innerHTML = new_message_string;
      
      // Add message to chat container
      const chatContainer = document.querySelector('#chat-container');
      chatContainer.appendChild(messageElement);
      
      // Scroll to bottom
      chatContainer.scrollTop = chatContainer.scrollHeight;
        
    } catch (error) {
        console.error('Full error details:', error);
    }

};

  // Handle Enter key in textarea
  document.querySelector('#message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      document.querySelector('#send-message-button').click();
    }
  });

  // Handle WebSocket errors
  chatSocket.onerror = function(error) {
    console.error('WebSocket error:', error);
  };

  chatSocket.onclose = function(e) {
    console.log('Chat socket closed unexpectedly');
  };

  // Auto-expand textarea
  const messageInput = document.querySelector('#message-input');
  messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
  });
</script>
</body>
</html>
