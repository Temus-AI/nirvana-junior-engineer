import React from 'react';
import { chatWebSocket } from '../utils/chatWebSocket';

const ChatBox = ({ messages, setMessages, newMessage, setNewMessage }) => {
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim()) {

      const userMessage = {
        text: newMessage,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);
      

      chatWebSocket.sendMessage(userMessage);
      

      setNewMessage('');
    }
  };

  return (
    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1/2 bg-white shadow-lg rounded-t-2xl">
      <div className="max-h-40 overflow-y-auto p-3 space-y-2">
        {messages.map((msg, index) => (
          <div key={index} className="px-4 py-2 rounded-lg bg-gray-50">
            {msg.text}
          </div>
        ))}
      </div>
      <div className="p-3 border-t">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-full border"
          />
          <button type="submit" className="p-2 rounded-full bg-blue-500 text-white">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
              <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatBox;