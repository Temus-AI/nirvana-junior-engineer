export class ChatWebSocket {
    constructor() {
        this.connect();
        this.messageHandlers = new Set();
    }

    connect() {
        console.log('[ChatWS] Attempting to connect...');
        this.ws = new WebSocket('ws://localhost:8000/ws/chat');
        
        this.ws.onopen = () => {
            console.log('[ChatWS] Connected successfully');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[ChatWS] Received message:', data);
                this.messageHandlers.forEach(handler => handler(data));
            } catch (error) {
                console.error('[ChatWS] Error parsing message:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('[ChatWS] WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('[ChatWS] Connection closed, attempting to reconnect...');
            setTimeout(() => this.connect(), 3000);
        };
    }

    addMessageHandler(handler) {
        console.log('[ChatWS] Adding message handler');
        this.messageHandlers.add(handler);
    }

    removeMessageHandler(handler) {
        console.log('[ChatWS] Removing message handler');
        this.messageHandlers.delete(handler);
    }

    sendMessage(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            const data = {
                type: 'chat_message',
                message
            };
            console.log('[ChatWS] Sending message:', data);
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('[ChatWS] WebSocket not ready, message not sent');
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

export const chatWebSocket = new ChatWebSocket();

export default chatWebSocket; 