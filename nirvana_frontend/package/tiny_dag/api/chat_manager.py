import os
import json
from datetime import datetime
from fastapi import WebSocket
from pathlib import Path

class ChatManager:
    def __init__(self):
        
        self._tmp_folder_ = Path(__file__).parent / "tmp"
        self._tmp_folder_.mkdir(exist_ok=True)
        self._storage_dir = self._tmp_folder_ / "chat_history"
        self._storage_dir.mkdir(exist_ok=True)
        
        
        self._history_file = self._storage_dir / "chat_history.json"
        print(f"[Chat] Using history file: {self._history_file}")
        
        self._websocket_connections = set()
        self._message_history = []
        self._load_history()
        print("[Chat] ChatManager initialized")

    def _load_history(self):
        """Load chat history from file"""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r') as f:
                    self._message_history = json.load(f)
                print(f"[Chat] Loaded {len(self._message_history)} messages from history")
        except Exception as e:
            print(f"[Chat] Error loading history: {str(e)}")
            self._message_history = []

    def _save_history(self):
        """Save chat history to file"""
        try:
            
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._history_file, 'w') as f:
                json.dump(self._message_history, f, indent=2)
            print(f"[Chat] History saved to {self._history_file}")
        except Exception as e:
            print(f"[Chat] Error saving history: {str(e)}")

    async def process_message(self, message, websocket: WebSocket):
        try:
            
            response = {
                "text": f"Server received: {message['text']}",
                "timestamp": datetime.now().isoformat()
            }
            
           
            self._message_history.append(message)
            self._message_history.append(response) 
            self._save_history()

            await websocket.send_json({
                "type": "chat_message",
                "message": response
            })
            
        except Exception as e:
            print(f"[Chat] Error processing message: {str(e)}")

    async def send_history(self, websocket: WebSocket):
        """Send chat history to new connection"""
        try:
            for msg in self._message_history:
                await websocket.send_json({
                    "type": "chat_message",
                    "message": msg
                })
            print(f"[Chat] Sent {len(self._message_history)} historical messages")
        except Exception as e:
            print(f"[Chat] Error sending history: {str(e)}")

chat_manager = ChatManager()