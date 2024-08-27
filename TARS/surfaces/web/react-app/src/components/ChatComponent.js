import React, { useState } from 'react';
import axios from 'axios';

const ChatComponent = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  const handleSendMessage = async () => {
    if (message.trim() === '') return;

    const newMessage = { user: 'You', text: message };
    setChatHistory([...chatHistory, newMessage]);

    try {
      const response = await axios.post('http://localhost:8000/chat', { message });
      const botMessage = { user: 'TARS', text: response.data.response };
      setChatHistory([...chatHistory, newMessage, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    }

    setMessage('');
  };

  return (
    <div>
      <h2>Chat with TARS</h2>
      <div className="chat-history">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.user === 'You' ? 'user-message' : 'bot-message'}`}>
            <strong>{msg.user}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
      />
      <button onClick={handleSendMessage}>Send</button>
    </div>
  );
};

export default ChatComponent;
